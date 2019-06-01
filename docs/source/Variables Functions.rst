Variables Functions
===================

Description of variables' built-in functions.

Functions can be of below logical types:
  - *Action* - performs action with match result to transform it to desired output
  - *Condition* - checks condition against match result, returns *True* if condition was satisfied and *False* otherwise
  - *Indicator* - indicates additional logic that needs to be accounted for during script execution

**Action Functions**

.. list-table:: Built-in Functions
   :widths: 10 90
   :header-rows: 1

   * - Name
     - Description
   * - `upper`_  
     - Transforms match result to upper case
   * - `lower`_ 
     - Transforms match result to lower case
   * - `title`_ 
     - Transforms match result to title
   * - `strip`_ 
     - Returns match result with leading and trailing chars stripped
   * - `rstrip`_ 
     - Returns match result with trailing chars stripped
   * - `lstrip`_ 
     - Returns match result with leading chars stripped
   * - `record`_ 
     - Save match result to variable with given name, which can be referenced by actions
   * - `truncate`_ 
     - truncate match results
	 
upper
-----
``{{ variable | upper }}``

Transforms match result to upper case using python string upper method

lower
-----
``{{ variable | lower }}``

Transforms match result to lower case using python string lower method

title
-----
``{{ variable | title }}``

Transforms match result to title case using Python String `Title <https://docs.python.org/3/library/stdtypes.html#str.title>`_ method

strip
-----
``{{ variable | strip(chars) }}``

* chars (optional) - a string specifying the set of characters to be removed

Returns a copy of the match result with both leading and trailing characters removed, if no argument provided space characters will removed

rstrip
------
``{{ variable | rstrip(chars) }}``

* chars (optional) - a string specifying the set of characters to be removed

same as `strip`_ but for leading chracters only

lstrip
------
``{{ variable | lstrip(chars) }}``

* chars (optional) - a string specifying the set of characters to be removed

same as `strip`_ but for trailing chracters only

record
------
``{{ variable | record(name) }}``

* name (mandatory) - a string containing variable name

Records match results in variable with given name after all functions run

truncate
--------
``{{ variable | truncate(count) }}``

* count (mandatory) - integer to count the number of words to remove

Splits match result using " "(space) char and joins it back up to truncate value. This function can be useful to shorten long match results.

Eamples:
  "123 abc qwer" and truncate(2) will produce "123 abc". 