Group functions
===============

Group functions can be applied to group results to transform them in a desired way, functions can also be used to validate and filter match results. 

Condition functions help to evaluate group results and return *False* or *True*, if *False* returned, group results will be discarded.
  
.. list-table:: group functions
   :widths: 10 90
   :header-rows: 1

   * - Name
     - Description
   * - `containsall`_ 
     - checks if group result contains matches for all given variables
   * - `containsany`_ 
     - checks if group result contains matche at least for one of given variables
	 
containsall
------------------------------------------------------------------------------
``containsall="variable1, variable2, variableN"``

* variable (mandatory) - a comma-separated string that contains match variable names

TBD

containsany
------------------------------------------------------------------------------
``containsany="variable1, variable2, variableN"``

* variable (mandatory) - a comma-separated string that contains match variable names

TBD