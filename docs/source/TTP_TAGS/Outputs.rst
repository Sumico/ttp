Outputs
=======

Outputs system allows to process parsing results, format them in certain way and return results to various destination. For instance, using yaml formatter results can take a form of YAML syntax and using file returner these results can be saved into file.

Outputs can be chained, say results after passing through first outputter will serve as an input for next outputter. That allows to implement complex processing logic of results produced by ttp.

The opposite way would be that each output defined in template will work with parsing results, transform them in different way and return to different destinations. An example of such a behavior might be the case when first outputter form csv table and saves it onto the file, while second outputter will render results with Jinja2 template and print them to the screen.

In addition two types of outputter exists - template specific and group specific. Template specific outputs will process template overall results, while group-specific will work with results of this particular group only.

There is a set of function available in outputs to process/modify results further.

.. note:: If several outputs provided - they run sequentially in the order defined in template. Within single output, processing order is - functions run first, after that formatters, followed by returners. 

There are a number of attributes that outputs system can use. Some attribute can be specific to output itself (name, description), others can be used by formatters or returners. 

Output attributes
-----------------

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Name
     - Description
   * - `name`_ 
     - name of the output, can be referenced in group *output* attribute
   * - `description`_ 
     - attribute to contain description of outputter
   * - `load`_ 
     - name of the loader to use to load output tag text
   * - `returner`_ 
     - returner to use to return data e.g. self, file, terminal
   * - `format`_ 
     - formatter to use to format results
   * - `functions`_ 
     - pipe separated list of functions to run results through		 

name
******************************************************************************
``name="output_name"``

* output_name - name of the output, can be used to reference it in groups :ref:`Groups/Attributes:output` attribute, in that case that output will become group specific and will only process results for this group.

description
******************************************************************************
``name="descrition_string"``

* descrition_string - string that contains output description or notes, can serve documentation purposes.
	 
Functions
---------

Output system provide support for a number of functions. Functions process output results first with intention to modify or check overall data in certain way.

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Name
     - Description
   * - `is_equal`_ 
     - checks if results equal to structure loaded from the output tag text 
	 
Returners
---------
	 
TTP has `file`_, `terminal`_ and `self`_ returners. Returners provide support for a number of attributes.

.. list-table::
   :widths: 10 10 80
   :header-rows: 1
   
   * - Attribute
     - Returner
     - Description   
	 
   * - `url`_ 
     - file
     - OS path to folder there to save results
   * - `filename`_ 
     - file
     - name of the file to save data in	 
   * - `method`_
     - file   
     - not implemented, indicate if to dump all data in one or several files
	 
Formatters
----------

TTP supports `raw`_, `yaml`_, `json`_, `csv`_, `jinja2`_, `pprint`_, `tabulate`_, `table`_ formatters. Formatters have a number of attributes that can be used to supply additional information or modify behavior.

.. list-table::
   :widths: 30 10 60
   :header-rows: 1
   
   * - Formatter
     - Attribute
     - Description  
   * - table and its derivatives - csv, tabulate 
     - `path`_ 
     - dot separated string that denotes path to data within results tree
   * - tabulate
     - `format_attributes`_ 
     - string of *args, **kwargs to pass to formatter
   * - table and its derivatives - csv, tabulate
     - `headers`_    
     - comma separated string of table headers	
   * - csv
     - `sep`_ 
     - character to separate items, by default it is comma
   * - table and its derivatives - csv, tabulate 
     - `missing`_ 
     - string to replace missing items based on provided headers
   * - table and its derivatives - csv, tabulate 
     - `key`_ 
     - string to use while flattening dictionary of data results

raw
******************************************************************************

TBD

yaml
******************************************************************************

TBD

JSON
******************************************************************************

TBD

pprint
******************************************************************************

TBD

table
******************************************************************************

TBD

csv
******************************************************************************

TBD

jinja2
******************************************************************************

TBD

tabulate
******************************************************************************

TBD
