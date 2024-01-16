#       Copyright (C) 2023  Intergral GmbH
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Processing for frame collection."""

import abc
from typing import Dict, Tuple, List, Optional

from deep import logging
from deep.api.tracepoint import StackFrame, WatchResult, Variable, VariableId
from deep.processor.bfs import Node, NodeValue, breadth_first_search, ParentNode
from deep.utils import time_ns
from .frame_config import FrameProcessorConfig
from .variable_processor import process_variable, process_child_nodes, variable_to_string, truncate_string, Collector
from ..config import ConfigService


class FrameCollector(Collector):
    """This deals with collecting data from the paused frames."""

    def __init__(self, frame, config: ConfigService):
        """
        Create a new collector.

        :param frame:  the frame data
        :param config: the deep config service
        """
        self._var_cache: Dict[str, str] = {}
        self._config = config
        self._has_time_exceeded = False
        self._ts = time_ns()
        self._frame_config = FrameProcessorConfig()
        self._frame = frame
        self._var_lookup: Dict[str, Variable] = {}
        self._var_id = 0

    @property
    def frame_config(self) -> FrameProcessorConfig:
        """
        The frame config.

        :return: the frame config
        """
        return self._frame_config

    @abc.abstractmethod
    def configure_self(self):
        """Process the filtered tracepoints to configure this processor."""
        pass

    def add_child_to_lookup(self, parent_id: str, child: VariableId):
        """
        Add a child variable to the var lookup parent.

        :param parent_id: the internal id of the parent
        :param child: the child VariableId to append
        :return:
        """
        self._var_lookup[parent_id].children.append(child)

    def log_tracepoint(self, log_msg: str, tp_id: str, snap_id: str):
        """Send the processed log to the log handler."""
        self._config.log_tracepoint(log_msg, tp_id, snap_id)

    def process_log(self, tp, log_msg) -> Tuple[str, List[WatchResult], Dict[str, Variable]]:
        """
        Process a log message.

        :param tp: the tracepoint config
        :param log_msg:  the log message
        :returns:
            (str) log_msg: the processed log message
            (list) watches: the watch results from the log
            (dict) vars: the collected vars for the watches
        """
        frame_col = self
        watch_results = []
        _var_lookup = {}

        class FormatDict(dict):
            """This type is used in the log process to ensure that missing values are formatted don't error."""

            def __missing__(self, key):
                return "{%s}" % key

        import string

        class FormatExtractor(string.Formatter):
            """
            Allows logs to be formatted correctly.

            This type allows us to use watches within log strings and collect the watch
            as well as interpolate the values.
            """

            def get_field(self, field_name, args, kwargs):
                # evaluate watch
                watch, var_lookup, log_str = frame_col.eval_watch(field_name)
                # collect data
                watch_results.append(watch)
                _var_lookup.update(var_lookup)

                return log_str, field_name

        log_msg = "[deep] %s" % FormatExtractor().vformat(log_msg, (), FormatDict(self._frame.f_locals))
        return log_msg, watch_results, _var_lookup

    def eval_watch(self, watch: str) -> Tuple[WatchResult, Dict[str, Variable], str]:
        """
        Evaluate an expression in the current frame.

        :param watch: The watch expression to evaluate.
        :return: Tuple with WatchResult, collected variables, and the log string for the expression
        """
        # reset var lookup - var cache is still used to reduce duplicates
        self._var_lookup = {}

        try:
            result = eval(watch, None, self._frame.f_locals)
            watch_var, var_lookup, log_str = self.__process_watch_result_breadth_first(watch, result)
            # again we reset the local version of the var lookup.
            self._var_lookup = {}
            return WatchResult(watch, watch_var), var_lookup, log_str
        except BaseException as e:
            logging.exception("Error evaluating watch %s", watch)
            return WatchResult(watch, None, str(e)), {}, str(e)

    def process_frame(self):
        """
        Start processing the frame.

        :return: Tuple of collected frames and variables
        """
        current_frame = self._frame
        collected_frames = []
        # while we still have frames process them
        while current_frame is not None:
            # process the current frame
            frame = self._process_frame(current_frame, self._frame_config.should_collect_vars(len(collected_frames)))
            collected_frames.append(frame)
            current_frame = current_frame.f_back
        # We want to clear the local collected var lookup now that we have processed the frame
        # this is, so we can process watches later while maintaining independence between tracepoints
        _vars = self._var_lookup
        self._var_lookup = {}
        return collected_frames, _vars

    def _process_frame(self, frame, process_vars):
        # process the current frame info
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        func_name = frame.f_code.co_name

        f_locals = frame.f_locals
        _self = f_locals.get('self', None)
        class_name = None
        if _self is not None:
            class_name = _self.__class__.__name__

        var_ids = []
        # only process vars if we are under the time limit
        if process_vars and not self.__time_exceeded():
            var_ids = self.process_frame_variables_breadth_first(f_locals)
        short_path, app_frame = self.parse_short_name(filename)
        return StackFrame(filename, short_path, func_name, lineno, var_ids, class_name,
                          app_frame=app_frame)

    def __time_exceeded(self):
        if self._has_time_exceeded:
            return self._has_time_exceeded

        duration = (time_ns() - self._ts) / 1000000  # make duration ms not ns
        self._has_time_exceeded = duration > self._frame_config.max_tp_process_time
        return self._has_time_exceeded

    def __is_app_frame(self, filename: str) -> Tuple[bool, Optional[str]]:
        in_app_include = self._config.IN_APP_INCLUDE
        in_app_exclude = self._config.IN_APP_EXCLUDE

        for path in in_app_exclude:
            if filename.startswith(path):
                return False, path

        for path in in_app_include:
            if filename.startswith(path):
                return True, path

        if filename.startswith(self._config.APP_ROOT):
            return True, self._config.APP_ROOT

        return False, None

    def process_frame_variables_breadth_first(self, f_locals):
        """
        Process the variables on a frame.

        :param f_locals: the frame locals.
        :return: the list of var ids for the frame.
        """
        var_ids = []

        class FrameParent(ParentNode):

            def add_child(self, child):
                var_ids.append(child)

        root_parent = FrameParent()

        initial_nodes = [Node(NodeValue(k, v), parent=root_parent) for k, v in f_locals.items()]
        breadth_first_search(Node(None, initial_nodes, root_parent), self.search_function)

        return var_ids

    def search_function(self, node: Node) -> bool:
        """
        Process a node using breadth first approach.

        :param node: the current node we are process
        :return: True, if we want to continue with the nodes children
        """
        if not self.check_var_count():
            # we have exceeded the var count, so do not continue
            return False

        node_value = node.value
        if node_value is None:
            # this node has no value, continue with children
            return True

        # process this node variable
        process_result = process_variable(self, node_value)
        var_id = process_result.variable_id
        # add the result to the parent - this maintains the hierarchy in the var look up
        node.parent.add_child(var_id)

        # some variables do not want the children processed (e.g. strings)
        if process_result.process_children:
            # process children and add to node
            child_nodes = process_child_nodes(self, var_id.vid, node_value.value, node.depth)
            node.add_children(child_nodes)
        return True

    def check_var_count(self):
        """
        Check if we have exceeded our var count.

        :return: True, if we should continue.
        """
        if len(self._var_cache) > self._frame_config.max_variables:
            return False
        return True

    def __process_watch_result_breadth_first(self, watch: str, result: any) -> (
            Tuple)[VariableId, Dict[str, Variable], str]:

        identity_hash_id = str(id(result))
        check_id = self.check_id(identity_hash_id)
        if check_id is not None:
            # this means the watch result is already in the var_lookup
            return VariableId(check_id, watch), {}, str(result)

        # else this is an unknown value so process breadth first
        var_ids = []

        class FrameParent(ParentNode):

            def add_child(self, child):
                var_ids.append(child)

        root_parent = FrameParent()

        initial_nodes = [Node(NodeValue(watch, result), parent=root_parent)]
        breadth_first_search(Node(None, initial_nodes, root_parent), self.search_function)

        var_id = self.check_id(identity_hash_id)

        variable_type = type(result)
        variable_value_str, truncated = truncate_string(variable_to_string(variable_type, result),
                                                        self.frame_config.max_string_length)

        self._var_lookup[var_id] = Variable(str(variable_type.__name__), variable_value_str, identity_hash_id, [],
                                            truncated)
        return VariableId(var_id, watch), self._var_lookup, str(result)

    def check_id(self, identity_hash_id):
        """
        Check if the identity_hash_id is known to us, and return the lookup id.

        :param identity_hash_id: the id of the object
        :return: the lookup id used
        """
        if identity_hash_id in self._var_cache:
            return self._var_cache[identity_hash_id]
        return None

    def new_var_id(self, identity_hash_id: str) -> str:
        """
        Create a new cache id for the lookup.

        :param identity_hash_id: the id of the object
        :return: the new lookup id
        """
        var_count = len(self._var_cache)
        new_id = str(var_count + 1)
        self._var_cache[identity_hash_id] = new_id
        return new_id

    def append_variable(self, var_id, variable):
        """
        Append a variable to var lookup using the var id.

        :param var_id: the internal variable id
        :param variable: the variable data to append
        """
        self._var_lookup[var_id] = variable

    def parse_short_name(self, filename: str) -> Tuple[str, bool]:
        """
        Process a file name into a shorter version.

        By default, the file names in python are the absolute path to the file on disk. These can be quite long,
        so we try to shorten the names by looking at the APP_ROOT and converting the file name into a relative path.

        e.g. if the file name is '/dev/python/custom_service/api/handler.py' and the APP_ROOT is
            '/dev/python/custom_service' then we shorten the path to 'custom_service/api/handler.py'.

        :param (str) filename: the file name
        :returns:
            (str) filename: the new file name
            (bool) is_app_frame: True if the file is an application frame file
        """
        is_app_frame, match = self.__is_app_frame(filename)
        if match is not None:
            return filename[len(match):], is_app_frame
        return filename, is_app_frame
