# !/usr/env python3

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
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.#
#      You should have received a copy of the GNU Affero General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

import glob
import os
import shutil
import sys

import yaml


def dump_nav(_nav, depth=0):
    keys = []
    for key in _nav.keys():
        keys.append(key)
    keys.sort()
    for k in keys:
        val = _nav[k]
        if type(val) is dict:
            print("%s - %s:" % (' ' * (depth * 2), k))
            dump_nav(val, depth + 1)
        else:
            print("%s - %s: %s" % (' ' * (depth * 2), k, val))


def covert_nav(new_nav):
    as_list = []
    for k in new_nav:
        val = new_nav[k]
        if type(val) is dict:
            _nav = covert_nav(val)
            as_list.append({k: _nav})
        else:
            as_list.append({k: val})
    # sort the nav alphabetically (each list item is a single element dict, so use first key to sort)
    return sorted(as_list, key=lambda x: list(x.keys())[0])


def update_nav(_project_root, new_nav):
    loaded = None
    with open("%s/mkdocs.yml" % _project_root, 'r') as mkdocs:
        read = mkdocs.read()
        loaded = yaml.load(read, Loader=yaml.Loader)
    if loaded is None:
        print("Cannot load mkdocs.yml")
        exit()
    loaded['nav'].append({'apidocs': covert_nav(new_nav)})
    with open("%s/mkdocs-mod.yml" % _project_root, 'w') as mkdocs:
        yaml.dump(loaded, mkdocs)


if __name__ == '__main__':
    nav = {}
    project_root = sys.argv[1]
    if os.path.exists("%s/docs/apidocs" % project_root):
        shutil.rmtree("%s/docs/apidocs" % project_root)

    for file in glob.glob("%s/src/**/*.py" % project_root, recursive=True):
        source_file = file
        dest_file = ("%s/docs/apidocs%s" % (project_root, file[len("%s/src" % project_root):]))[:-3] + ".md"
        mod_name = file[len("%s/src/" % project_root):-3]
        if mod_name.endswith("__init__"):
            mod_name = mod_name[:-9]
        mod_name = mod_name.replace('/', '.')
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        with open(dest_file, 'w') as f:
            f.write("# %s\n::: %s" % (mod_name, mod_name))

        c_nav = nav
        split = dest_file[len("%s/docs/apidocs/" % project_root):-3].split('/')
        end_part = split[-1]
        for part in split[:-1]:
            if part in c_nav:
                c_nav = c_nav[part]
            else:
                c_nav[part] = {}
                c_nav = c_nav[part]

        c_nav[end_part] = dest_file[len("%s/docs/" % project_root):]

    # dump_nav(nav)
    update_nav(project_root, nav)
