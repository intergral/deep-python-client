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

"""Collection of utils for testing."""


def find_var_by_name(grpc_snapshot, _vars, name):
    """Find a variable by name in a list of variables."""
    var_id = None
    for var in _vars:
        if var.name == name:
            var_id = var
            break
    if var_id is None:
        return None
    return grpc_snapshot.var_lookup[var_id.ID]


def find_var_in_snap_by_name(grpc_snapshot, name):
    """Find a variable in the snapshot by name."""
    _vars = grpc_snapshot.frames[0].variables
    return find_var_by_name(grpc_snapshot, _vars, name)


def find_var_in_snap_by_path(grpc_snapshot, path):
    """Find a variable in a snapshot by using the path."""
    _vars = grpc_snapshot.frames[0].variables
    parts = path.split('.')
    var = None
    for part in parts:
        var = find_var_by_name(grpc_snapshot, _vars, part)
        if var is None:
            return None
        else:
            _vars = var.children
    return var
