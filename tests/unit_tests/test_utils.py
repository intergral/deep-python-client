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
from time import sleep

from deep.utils import snapshot_id_as_hex_str, time_ms, time_ns, str2bool, RepeatedTimer


def test_snapshot_id_as_hex_str():
    assert "0000000000000000000000000000007b" == snapshot_id_as_hex_str(123)
    assert "000000000000000000000000499602d2" == snapshot_id_as_hex_str(1234567890)
    assert "0000000000000000000000003ade68b1" == snapshot_id_as_hex_str(987654321)


def test_time_ms():
    assert time_ms()
    assert len(str(time_ms())) == 13


def test_time_ns():
    assert time_ns()
    assert len(str(time_ns())) == 19


def test_str2bool():
    assert str2bool("yes")
    assert str2bool("Yes")
    assert str2bool("y")
    assert str2bool("Y")
    assert str2bool("true")
    assert str2bool("True")
    assert str2bool("t")
    assert str2bool("1")
    assert not str2bool("0")
    assert not str2bool("false")
    assert not str2bool("False")
    assert not str2bool("no")
    assert not str2bool("No")


count = 0


def test_repeated_timer():
    global count

    def repeated(val):
        global count
        val += 1
        count = count + 1

    timer = RepeatedTimer("test", 1, repeated, 1)
    timer.start()
    sleep(2)
    timer.stop()

    assert count > 0


def test_repeated_timer_error():
    global count
    count = 0

    # noinspection PyUnusedLocal
    def repeated(val):
        raise Exception("test")

    timer = RepeatedTimer("test", 1, repeated, 1)
    timer.start()
    sleep(2)
    timer.stop()

    assert 0 == 0
