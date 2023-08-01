# deker-shell - interactive management shell for deker
# Copyright (C) 2023  OpenWeather
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import deker


help_start = """
This is an interactive python interface to Deker, based on ptpython.
You have an initiated 'client' instance to create and get collections,
'collections' variable with a list of collection names
and 'collection' variable that can be set by 'use' method.
If you need more information, call help()
Example:
    use("test")
    collection.create()
---
F2 - ptpython menu
F3 - history
"""

help_text = """
Preset variables:
- client: Client (registry of collections) instance, connected to the uri-database
- collections: list of Client collections names
- collection: global default collection variable, set by use("coll_name") method;
- np: numpy library

Classes:
- Client: registry of collections
- Collection: collection of arrays or varrays
- Array: array with/without data, can be read through subset: array[:].read()
- VArray: virtual array
- Subset: subset of Array data with set bounds and shape, can read, update and clear the data within the array
- VSubset: virtual subset of VArray data with set bounds and shape
- ArraySchema: schema with arrays attributes, dimensions and dtype, needed to create collection
- VArraySchema: ArraySchema with vgrid: an ordered sequence of positive integers, used for splitting virtual array into ordinary arrays  # noqa E501
- DimensionSchema: dimensions (data) schema, you can also use TimeDimensionSchema

Methods:
- use("name"): gets collection from client and saves it to 'collection' variable
- get_global_coll_variable: returns 'collection' global variable

Call help(class or function) to read more
"""

deker_objects = tuple(deker_obj + "(" for deker_obj in deker.__all__)
