===============
Deker shell
===============

Deker shell provides python REPL interface for Deker, offering features like autocompletion,
preset variables, and enhanced REPL functionality through Ptpython.

Start
------------------------
You need Deker and python 3.9 installed

.. code-block:: bash

    pip install deker-shell
    deker file://<path-to-your-deker-storage>

Features
------------------------
- Deker features
- Autocompletion
- Preset client and collections variable
- Default collection variable with 'use' method
- Ptpython features

Examples
------------------------
Using global collection variable

.. code-block:: python

    # set "weather" collection as default
    use("weather")
    # you can use collection variable freely for now
    print(json.dumps(collection.as_dict, indent=4))

Creating a new collection

.. code-block:: python

    # prepare dimensions and schema
    dimensions = [
            DimensionSchema(name="y", size=361),
            DimensionSchema(name="x", size=720),
            DimensionSchema(
                name="layers", size=4, labels=["temp", "pressure", "dew_point", "wind_speed"]
            ),
            TimeDimensionSchema(
                name="weather_dt",
                size=129,
                start_value=datetime.datetime.now(datetime.timezone.utc),
                step=datetime.timedelta(3),
            )
        ]
    array_schema = ArraySchema(dtype=float, dimensions=dimensions)

    # create new collection and empty array
    new_collection: Collection = client.create_collection("weather", array_schema)
    empty_array: Array = new_collection.create()

Preset variables
------------------------
- client: Client (registry of collections) instance, connected to the uri-database
- collections: list of Client collections names
- collection: global default collection variable, set by use("coll_name") method;
- np: numpy library

Classes
------------------------
- :external+deker:class:`Client <deker.client.Client>` - registry of collections
- :external+deker:class:`Collection <deker.collection.Collection>` - collection of arrays or
   varrays
- :external+deker:class:`Array <deker.arrays.Array>` - array with/without data, can be read
   through subset: array[:].read()
- :external+deker:class:`VArray <deker.arrays.VArray>` - virtual array
- :external+deker:class:`Subset <deker.subset.Subset>` - subset of Array data with set bounds
   and shape, can read, update and clear the data within the array
- :external+deker:class:`VSubset <deker.subset.VSubset>` - virtual subset of VArray data with
   set bounds and shape
- :external+deker:class:`ArraySchema <deker.schemas.ArraySchema>` - schema with arrays
   attributes, dimensions and dtype, needed to create collection
- :external+deker:class:`VArraySchema <deker.schemas.VArraySchema>` - ArraySchema with vgrid:
   an ordered sequence of positive integers, used for splitting virtual array into ordinary arrays
- :external+deker:class:`DimensionSchema <deker.schemas.DimensionSchema>` - dimensions (data)
   schema, you can also use :external+deker:class:`DimensionSchema
   <deker.schemas.TimeDimensionSchema>`
- :external+deker:class:`AttributeSchema <deker.schemas.AttributeSchema>` - describes
   requirements for the primary or custom attribute of Array or VArray

Methods
------------------------
- use("name"): gets collection from client and saves it to 'collection' variable
- get_global_coll_variable: returns 'collection' global variable

Special thanks to
------------------------
- `Ptpython <https://github.com/prompt-toolkit/ptpython>`_ - advanced Python REPL
