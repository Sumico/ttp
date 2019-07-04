Group Attributes
================

Each group tag (<g>, <grp>, <group>)can have a number of attributes, they used during module execution to provide desired results. Attributes can be mandatory or optional. Each attribute is a string of data formatted in certain way.

.. list-table:: group attributes
   :widths: 10 90
   :header-rows: 1

   * - Attribute
     - Description
   * - `name`_   
     - Uniquely identifies group within template and specifies results path location
   * - `input`_  
     - Used to provide the name of input tag which will beparsed bygiven group, 
	   alternatively can contain OS path string to files location that needs to be parsed by this group
   * - `default`_   
     - Contains default value that should be used for all match variables
   * - `method`_   
     - Indicates parsing method, supported values are *group* or *table*	 

name
------------------------------------------------------------------------------
``name="path_string"``

* path_string (mandatory) - this is the only one attribute that must be set for each group, path is a dot separated string that indicates group results placement in results structure

TBD

input
------------------------------------------------------------------------------
``input="input_name"``

* input_name (optional)

TBD

default
------------------------------------------------------------------------------
``default="value"``

* value (optional)

TBD

method
------------------------------------------------------------------------------
``method="value"``

* value (optional) - default value is *group*, other supported value is *table*

TBD