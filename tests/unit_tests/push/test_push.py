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
from deep.api.tracepoint import WatchResult
from deep.push import convert_snapshot
from utils import mock_snapshot, mock_frame, mock_variable, mock_variable_id


def test_convert_snapshot():
    event_snapshot = mock_snapshot()
    snapshot = convert_snapshot(event_snapshot)
    assert snapshot is not None


def test_convert_snapshot_with_frame():
    event_snapshot = mock_snapshot(frames=[mock_frame()])
    snapshot = convert_snapshot(event_snapshot)
    assert snapshot is not None
    assert 1 == len(snapshot.frames)

    assert "file_name" == snapshot.frames[0].file_name


def test_convert_snapshot_with_frame_with_vars():
    event_snapshot = mock_snapshot(frames=[mock_frame(variables=[mock_variable_id()])],
                                   var_lookup={'vid': mock_variable()})
    snapshot = convert_snapshot(event_snapshot)
    assert snapshot is not None
    assert 1 == len(snapshot.frames)

    assert "file_name" == snapshot.frames[0].file_name

    assert 1 == len(snapshot.frames[0].variables)

    assert "name" == snapshot.frames[0].variables[0].name

    assert 1 == len(snapshot.var_lookup)

    assert "name" == snapshot.var_lookup['vid'].value


def test_convert_snapshot_with_watch():
    event_snapshot = mock_snapshot()
    event_snapshot.add_watch_result(WatchResult("test", mock_variable_id()))

    snapshot = convert_snapshot(event_snapshot)

    assert snapshot.watches[0].error_result == ''
    assert snapshot.watches[0].good_result is not None
    assert snapshot.watches[0].good_result.ID == "vid"
    assert "good_result" == snapshot.watches[0].WhichOneof("result")


def test_convert_snapshot_with_error_watch():
    event_snapshot = mock_snapshot()
    event_snapshot.add_watch_result(WatchResult("test", None, 'test error'))

    snapshot = convert_snapshot(event_snapshot)

    assert snapshot.watches[0].error_result == 'test error'
    assert "error_result" == snapshot.watches[0].WhichOneof("result")


def test_convert_error():
    # noinspection PyTypeChecker
    snapshot = convert_snapshot({})
    assert snapshot is None
