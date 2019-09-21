Writing templates
=================

Writing templates is simple.

Non-hierarchical templates require small efforts to write, just take the data that need to be parsed and replace portion of it with match variables, so that after extraction 

XML Primer
----------

Core Functionality
------------------

TTP has a number of systems built into it:

* groups system - help to define hierarchy and data processing function with filtering
* parsing system - uses regular expressions derived out of templates to parse and process data
* input system - used to define various input data sets, pre-process them and map to the groups to parse them
* output system - can help to format parsing results and return them to certain destination (e.g. - store on local file system)