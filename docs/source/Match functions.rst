Match functions
===============

Description of ttp match's built-in functions.

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
   * - `record`_ 
     - Save match result to variable with given name, which can be referenced by actions
   * - `truncate`_ 
     - truncate match results
   * - `joinmatches`_ 
     - join matches using provided character
   * - `resub`_ 
     - replace old patter with new pattern in match using re substitute method
   * - `join`_ 
     - join match using provided character
	 
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

Example:
  If match is "foo bar foo-bar" and truncate(2) will produce "foo bar". 
  
joinmatches
-----------
``{{ variable | joinmatches(char) }}``

* char (optional) - character to use to join matches, default is new line '\n'

Splits match result using " "(space) char and joins it back up to truncate value. This function can be useful to shorten long match results.

Example:
    * Sample data is:
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166,173  
     switchport trunk allowed vlan add 400,401,410
     
    * If template is:
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans | joinmatches(',') }}
    
    * Result will be:
    {
        "interface": "GigabitEthernet3/3"  
        "trunkVlans": "138,166,173,400,401,410"
    }
	
resub
-----
``{{ variable | resub(old, new) }}``

* old (mandatory) - pattern to be replaced
* new (mandatory) - pattern to be replaced with

Performs re.sub(old, new, match, count=1) on match result and returns produced value

Example:
    * Sample data is:
    interface GigabitEthernet3/3
     
    * Template is:
    interface {{ interface | resub(old = '^GigabitEthernet'), new = 'Ge'}}
    
    * Result will be:
    {
        "interface": "Ge3/3"  
    }
	
join
----
``{{ variable | match(char) }}``

* char (mandatory) - character to use to join match

Joins match result using provided character

Example:
