Lookups
=======
   
Lookups tag allows to define a lookup table, table that can be used to lookup values to include them into parsing results. Lookup table can be called from match variable functions chain using *lookup* function.

.. list-table:: lokup tag attributes
   :widths: 10 90
   :header-rows: 1

   * - Name
     - Description
   * - `name`_ 
     - name of the lookup table to reference in match variable *lookup* function
   * - `load`_ 
     - name of the lookup table to reference in match variable *lookup* function 
   * - `include`_   
     - Specifies location of the file to load lookup table from
   * - `key`_   
     - If csv loader used, *key* specifies column name to use as a key

name
------------------------------------------------------------------------------
``name="lookup_table_name"``

* lookup_table_name(mandatory) - string to use as a name for lookup table, that is required attribute without it lookup data will not be loaded.
	 
load
------------------------------------------------------------------------------
``load="loader_name"``	

* loader_name (optional) - name of the loader to use to render supplied variables data, default is python.

Supported loaders:

* python - uses python *exec* method to load data structured in native Python formats
* yaml - relies on PyYAML to load YAML structured data
* json - used to load json formatted variables data
* ini - *configparser* Python standart module used to read variables from ini structured file
* csv - csv formatted data loaded with Python *csv* standart library module

include
------------------------------------------------------------------------------
``include="path"``	

* path - absolute OS path to text file with lookup table data.

key
------------------------------------------------------------------------------
``key="column_name"``	

* column_name - optional string attribute that can be used by csv loader to use given column values as a key for dictionary constructed out of csv data.


Example
------------------------------------------------------------------------------

Template

.. code-block:: html

    TBD

Result

.. code-block::

    TBD