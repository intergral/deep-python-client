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

import deep
from deep.api.resource import Resource
from deep.config import ConfigService
from deep.poll import LongPoll

# noinspection PyUnresolvedReferences
from deepproto.proto.poll.v1.poll_pb2 import PollResponse, ResponseType


class TestPoll(unittest.TestCase):

    def setUp(self):
        self.tracepoints = mockito.mock()
        self.tracepoints.current_hash = '123'
        self.config = ConfigService(tracepoints=self.tracepoints)
        self.config.resource = Resource.create(attributes={"test": "test_poll"})
        self.grpc_service = mockito.mock()
        self.handler = mockito.mock()
        # mock for stub sending
        mockito.when(self.handler).submit_task(mockito.ANY, mockito.ANY).thenReturn(mockito.mock())
        deep.logging.init(self.config)

    def test_can_poll(self):
        poll = LongPoll(self.config, self.grpc_service)

        self.poll_request = None

        # noinspection PyUnusedLocal
        def mock_poll(request, **kwargs):
            self.poll_request = request
            return PollResponse(response_type=ResponseType.NO_CHANGE)

        mock_channel = mockito.mock()
        self.grpc_service.channel = mock_channel
        mockito.when(mock_channel).unary_unary(mockito.ANY, request_serializer=mockito.ANY,
                                               response_deserializer=mockito.ANY).thenReturn(mock_poll)

        poll.start()

        poll.shutdown()

        self.assertIsNotNone(self.poll_request)

        self.assertEqual("test", self.poll_request.resource.attributes[3].key)
        self.assertEqual("test_poll", self.poll_request.resource.attributes[3].value.string_value)

        mockito.verify(self.tracepoints, mockito.times(1)).update_no_change(mockito.ANY)

    def test_can_poll_new_cfg(self):
        poll = LongPoll(self.config, self.grpc_service)

        self.poll_request = None

        # noinspection PyUnusedLocal
        def mock_poll(request, **kwargs):
            self.poll_request = request
            return PollResponse(response_type=ResponseType.UPDATE)

        mock_channel = mockito.mock()
        self.grpc_service.channel = mock_channel
        mockito.when(mock_channel).unary_unary(mockito.ANY, request_serializer=mockito.ANY,
                                               response_deserializer=mockito.ANY).thenReturn(mock_poll)

        poll.start()

        poll.shutdown()

        self.assertIsNotNone(self.poll_request)

        self.assertEqual("test", self.poll_request.resource.attributes[3].key)
        self.assertEqual("test_poll", self.poll_request.resource.attributes[3].value.string_value)

        mockito.verify(self.tracepoints, mockito.times(0)).update_no_change(mockito.ANY)
        mockito.verify(self.tracepoints, mockito.times(1)).update_new_config(mockito.ANY, mockito.ANY, mockito.ANY)
