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
from deep.config import ConfigService
from deep.push import PushService
from utils import mock_snapshot, Captor


class TestPushService(unittest.TestCase):

    def setUp(self):
        self.config = ConfigService()
        self.grpc_service = mockito.mock()
        self.handler = mockito.mock()
        # mock for stub sending
        mockito.when(self.handler).submit_task(mockito.ANY, mockito.ANY).thenReturn(mockito.mock())
        deep.logging.init(self.config)

    def tearDown(self):
        mockito.unstub()

    def test_push_service(self):
        service = PushService(self.grpc_service, self.handler)
        service.push_snapshot(mock_snapshot())

        mockito.verify(self.handler).submit_task(mockito.ANY, mockito.ANY)

    def test_push_service_function(self):
        service = PushService(self.grpc_service, self.handler)
        service.push_snapshot(mock_snapshot())

        task_captor = Captor()
        snapshot_captor = Captor()

        mockito.verify(self.handler).submit_task(task_captor, snapshot_captor)

        task = task_captor.get_value()
        snapshot = snapshot_captor.get_value()

        self.assertIsNotNone(task)
        self.assertIsNotNone(snapshot)

        mock_channel = mockito.mock()

        self.sent_snap = None

        # noinspection PyUnusedLocal
        def mock_send(snap, **kwargs):
            self.sent_snap = snap

        self.grpc_service.channel = mock_channel
        mockito.when(mock_channel).unary_unary(mockito.ANY, request_serializer=mockito.ANY,
                                               response_deserializer=mockito.ANY).thenReturn(mock_send)

        task(snapshot)

        self.assertIsNotNone(self.sent_snap)

    def test_do_not_send_on_convert_failure(self):
        service = PushService(self.grpc_service, self.handler)

        class FakeSnapshot:
            def complete(self):
                pass

        # noinspection PyTypeChecker
        service.push_snapshot(FakeSnapshot())

        task_captor = Captor()
        snapshot_captor = Captor()

        mockito.verify(self.handler).submit_task(task_captor, snapshot_captor)

        task = task_captor.get_value()
        snapshot = snapshot_captor.get_value()

        self.assertIsNotNone(task)
        self.assertIsNotNone(snapshot)

        mock_channel = mockito.mock()

        self.sent_snap = None

        # noinspection PyUnusedLocal
        def mock_send(snap, **kwargs):
            self.sent_snap = snap

        self.grpc_service.channel = mock_channel
        mockito.when(mock_channel).unary_unary(mockito.ANY, request_serializer=mockito.ANY,
                                               response_deserializer=mockito.ANY).thenReturn(mock_send)

        task(snapshot)

        self.assertIsNone(self.sent_snap)
