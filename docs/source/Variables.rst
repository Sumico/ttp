Variables
=========
   
ttp supports definition of custom variables using dedicated xml tags <v>, <vars> or <variables>. Withing this tags variables can be defined in various formats and loaded using one of supported loaders. Variables can also be defined in external text files using *include* attribute. 

Custom variables can be used in a number of places within the templates, primarily in match variable functions, to store data off the groups definitions.

Data can also be recorded in variables during parsing and referenced later to construct dynamic path or within variables functions.

Variable tag attributes
-----------------------

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Attribute
     - Description
   * - `load`_   
     - Indicates which loader to use to read tag data, default is *python*
   * - `include`_   
     - Specifies location of the file with variables data to load`_

load
------------------------------------------------------------------------------
``load="loader_name"``	

* loader_name (optional) - name of the loader to use to render supplied variables data

Supported loaders:

* python - default, uses python *exec* method to load data structured in native Python formats
* yaml - relies on PyYAML to load YAML structured data
* json - used to load json formatted variables data
* ini - *configparser* Python standart module used to read variables from ini structured file

**Example**

Template
::
<!--Python formatted variables data-->
<v>
domains = ['.lab.local', '.static.on.net', '.abc']
</v>

<!--YAML formatted variables data-->
<vars load="yaml">
domains:
  - '.lab.local'
  - '.static.on.net'
  - '.abc'
</vars>

<!--Json formatted variables data-->
<vars load="json">
{
    "data": [
        ".lab.local",
        ".static.on.net",
        ".abc"
    ]
}
</vars>

<!--INI formatted variables data-->
<variables load="ini">
[domains]
'.lab.local'
'.static.on.net'
'.abc'
</variables>