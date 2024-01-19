#       Copyright (C) 2024  Intergral GmbH
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
import unittest

import mockito

import deep.logging
from deep.api.tracepoint.tracepoint_config import MetricDefinition, LabelExpression
from deep.processor.context.metric_action import MetricActionContext


class TestMetricAction(unittest.TestCase):

    def setUp(self):
        deep.logging.init()

    def test_metric_action(self):
        parent = mockito.mock()
        parent.config = mockito.mock()
        parent.config.has_metric_processor = True
        metric_processor = mockito.mock()
        mockito.when(metric_processor).counter("simple_test", {}, 'deep', None, None, 1).thenReturn()
        parent.config.metric_processors = (m for m in [metric_processor])
        action = mockito.mock()
        action.can_trigger = lambda x: True
        action.condition = None
        action.config = {
            'metrics': [MetricDefinition(name="simple_test", metric_type="counter")]
        }
        context = MetricActionContext(parent, action)
        context.process()
        self.assertTrue(context.can_trigger())

        mockito.verify(metric_processor, mockito.times(1)).counter("simple_test", {}, 'deep', None, None, 1)

    def test_metric_action_with_expression(self):
        parent = mockito.mock()
        mockito.when(parent).evaluate_expression("len([1,2,3])").thenReturn(3)
        parent.config = mockito.mock()
        parent.config.has_metric_processor = True
        metric_processor = mockito.mock()
        mockito.when(metric_processor).counter("simple_test", {}, 'deep', None, None, 3).thenReturn()
        parent.config.metric_processors = (m for m in [metric_processor])
        action = mockito.mock()
        action.can_trigger = lambda x: True
        action.condition = None
        action.config = {
            'metrics': [MetricDefinition(name="simple_test", metric_type="counter", expression="len([1,2,3])")]
        }
        context = MetricActionContext(parent, action)
        context.process()
        self.assertTrue(context.can_trigger())

        mockito.verify(metric_processor, mockito.times(1)).counter("simple_test", {}, 'deep', None, None, 3)

    def test_metric_action_with_bad_expression(self):
        parent = mockito.mock()
        mockito.when(parent).evaluate_expression("len([1,2,3])").thenReturn(None)
        parent.config = mockito.mock()
        parent.config.has_metric_processor = True
        metric_processor = mockito.mock()
        mockito.when(metric_processor).counter("simple_test", {}, 'deep', None, None, 3).thenReturn()
        parent.config.metric_processors = (m for m in [metric_processor])
        action = mockito.mock()
        action.can_trigger = lambda x: True
        action.condition = None
        action.config = {
            'metrics': [MetricDefinition(name="simple_test", metric_type="counter", expression="len([1,2,3])")]
        }
        context = MetricActionContext(parent, action)
        context.process()
        self.assertTrue(context.can_trigger())

        mockito.verify(metric_processor, mockito.times(1)).counter("simple_test", {}, 'deep', None, None, 1)

    def test_metric_action_with_label_expression(self):
        parent = mockito.mock()
        mockito.when(parent).evaluate_expression("len([1,2,3])").thenReturn("None")
        parent.config = mockito.mock()
        parent.config.has_metric_processor = True
        metric_processor = mockito.mock()
        mockito.when(metric_processor).counter("simple_test", {}, 'deep', None, None, 3).thenReturn()
        parent.config.metric_processors = (m for m in [metric_processor])
        action = mockito.mock()
        action.can_trigger = lambda x: True
        action.condition = None
        action.config = {
            'metrics': [MetricDefinition(name="simple_test", metric_type="counter",
                                         labels=[LabelExpression(key="test", expression="len([1,2,3])")])]
        }
        context = MetricActionContext(parent, action)
        context.process()
        self.assertTrue(context.can_trigger())

        mockito.verify(metric_processor, mockito.times(1)).counter("simple_test", {"test": "None"}, 'deep', None, None,
                                                                   1)

    def test_metric_action_with_label_bad_expression(self):
        parent = mockito.mock()
        mockito.when(parent).evaluate_expression("len([1,2,3])").thenRaise(Exception("test: bad expression"))
        parent.config = mockito.mock()
        parent.config.has_metric_processor = True
        metric_processor = mockito.mock()
        mockito.when(metric_processor).counter("simple_test", {}, 'deep', None, None, 3).thenReturn()
        parent.config.metric_processors = (m for m in [metric_processor])
        action = mockito.mock()
        action.can_trigger = lambda x: True
        action.condition = None
        action.config = {
            'metrics': [MetricDefinition(name="simple_test", metric_type="counter",
                                         labels=[LabelExpression(key="test", expression="len([1,2,3])")])]
        }
        context = MetricActionContext(parent, action)
        context.process()
        self.assertTrue(context.can_trigger())

        mockito.verify(metric_processor, mockito.times(1)).counter("simple_test", {'test': 'expression failed'}, 'deep',
                                                                   None, None, 1)

    def test_metric_action_with_label_static(self):
        parent = mockito.mock()
        mockito.when(parent).evaluate_expression("len([1,2,3])").thenRaise(Exception("test: bad expression"))
        parent.config = mockito.mock()
        parent.config.has_metric_processor = True
        metric_processor = mockito.mock()
        mockito.when(metric_processor).counter("simple_test", {}, 'deep', None, None, 3).thenReturn()
        parent.config.metric_processors = (m for m in [metric_processor])
        action = mockito.mock()
        action.can_trigger = lambda x: True
        action.condition = None
        action.config = {
            'metrics': [MetricDefinition(name="simple_test", metric_type="counter",
                                         labels=[LabelExpression(key="test", static="len([1,2,3])")])]
        }
        context = MetricActionContext(parent, action)
        context.process()
        self.assertTrue(context.can_trigger())

        mockito.verify(metric_processor, mockito.times(1)).counter("simple_test", {'test': 'len([1,2,3])'}, 'deep',
                                                                   None, None, 1)

    def test_no_processors(self):
        parent = mockito.mock()
        parent.config = mockito.mock()
        parent.config.has_metric_processor = False

        action = mockito.mock()
        context = MetricActionContext(parent, action)
        self.assertFalse(context.can_trigger())
