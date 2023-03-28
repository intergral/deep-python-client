#     Copyright 2023 Intergral GmbH
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import abc

from deep import logging
from deep.api.tracepoint import StackFrame, WatchResult, Variable, VariableId
from deep.processor.bfs import Node, NodeValue, breadth_first_search, ParentNode
from deep.utils import time_ms
from .frame_config import FrameProcessorConfig
from .variable_processor import process_variable, process_child_nodes, variable_to_string, truncate_string, Collector


class FrameCollector(Collector):
    """
    This deals with collecting data from the paused frames.
    """
    def __init__(self, frame, config):
        self._var_cache: dict[str, str] = {}
        self._config = config
        self._has_time_exceeded = False
        self._ts = time_ms()
        self._frame_config = FrameProcessorConfig()
        self._frame = frame
        self._var_lookup: dict[str, Variable] = {}
        self._var_id = 0

    @property
    def frame_config(self) -> FrameProcessorConfig:
        return self._frame_config

    @abc.abstractmethod
    def configure_self(self):
        pass

    def add_child_to_lookup(self, parent_id: str, child: VariableId):
        self._var_lookup[parent_id].children.append(child)

    def eval_watch(self, watch):
        # reset var lookup - var cache is still used to reduce duplicates
        self._var_lookup = {}

        try:
            result = eval(watch, None, self._frame.f_locals)
            watch_var, var_lookup = self.process_watch_result_breadth_first(watch, result)
            return WatchResult(watch, watch_var), var_lookup
        except BaseException as e:
            logging.exception("Error evaluating watch %s", watch)
            return WatchResult(watch, None, str(e)), {}

    def process_frame(self):
        """
        This is the main variable processing
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
        return collected_frames, self._var_lookup

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
        if process_vars and not self.time_exceeded():
            var_ids = self.process_frame_variables_breadth_first(f_locals)

        return StackFrame(filename, func_name, lineno, var_ids, class_name, app_frame=self.is_app_frame(filename))

    def time_exceeded(self):
        if self._has_time_exceeded:
            return self._has_time_exceeded

        duration = time_ms() - self._ts
        self._has_time_exceeded = duration > self._frame_config.max_tp_process_time
        return self._has_time_exceeded

    def is_app_frame(self, filename):
        in_app_include = self._config.IN_APP_INCLUDE
        in_app_exclude = self._config.IN_APP_EXCLUDE

        for path in in_app_exclude:
            if filename.startswith(path):
                return False

        for path in in_app_include:
            if filename.starstwith(path):
                return True

        return True

    def process_frame_variables_breadth_first(self, f_locals):
        """
        Here we start the BFS process for the frame.
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
        This is the search function to use during BFS
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
        process_result = process_variable(self, node_value.name, node_value.value)
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
        if len(self._var_cache) > self._frame_config.max_variables:
            return False
        return True

    def process_watch_result_breadth_first(self, watch: str, result: any):

        identity_hash_id = str(id(result))
        check_id = self.check_id(identity_hash_id)
        if check_id is not None:
            # this means the watch result is already in the var_lookup
            return VariableId(check_id, watch), {}

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
        return VariableId(var_id, watch), self._var_lookup

    def check_id(self, identity_hash_id):
        if identity_hash_id in self._var_cache:
            return self._var_cache[identity_hash_id]
        return None

    def new_var_id(self, identity_hash_id: str) -> str:
        var_count = len(self._var_cache)
        new_id = str(var_count + 1)
        self._var_cache[identity_hash_id] = new_id
        return new_id

    def append_variable(self, var_id, variable):
        self._var_lookup[var_id] = variable
