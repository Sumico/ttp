.. |br| raw:: html

   <br />

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
   * - `append`_ 
     - append provided string to match result
   * - `print`_ 
     - print match result to terminal
   * - `unrange`_ 
     - unrange match result using given parameters
   * - `set`_ 
     - set result to specific value based if certain string was matched
	 
record
------------------------------------------------------------------------------
``{{ variable | record(name) }}``

* name (mandatory) - a string containing variable name

Records match results in variable with given name after all functions run

truncate
--------
``{{ variable | truncate(count) }}``

* count (mandatory) - integer to count the number of words to remove

Splits match result using " "(space) char and joins it back up to truncate value. This function can be useful to shorten long match results.

**Example**:
  If match is "foo bar foo-bar" and truncate(2) will produce "foo bar". 
  
joinmatches
------------------------------------------------------------------------------
``{{ variable | joinmatches(char) }}``

* char (optional) - character to use to join matches, default is new line '\\n'

Join results from different matches into a single result string using provider charcter or string. 

**Example**:
    * Sample data is:
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166,173 |br|
     switchport trunk allowed vlan add 400,401,410
     
    * If template is:
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans | joinmatches(',') }}
    
    * Result will be:
    {
        "interface": "GigabitEthernet3/3"  |br|
        "trunkVlans": "138,166,173,400,401,410"
    }
	
resub
------------------------------------------------------------------------------
``{{ variable | resub(old, new) }}``

* old (mandatory) - pattern to be replaced
* new (mandatory) - pattern to be replaced with

Performs re.sub(old, new, match, count=1) on match result and returns produced value

**Example**:
    * Sample data is:
    interface GigabitEthernet3/3
     
    * Template is:
    interface {{ interface | resub(old = '^GigabitEthernet'), new = 'Ge'}}
    
    * Result will be:
    {
        "interface": "Ge3/3"  
    }
	
join
------------------------------------------------------------------------------
``{{ variable | match(char) }}``

* char (mandatory) - character to use to join match

Run joins against match result using provided character and return string


**Example**-1:
    Match is a string here and running join against it will inser '.' in between each charscter 
    * Sample data is:
    description someimportantdescription
     
    * Template is:
    description {{ description | join('.') }}
    
    * Result will be:
    {
        "description": "s.o.m.e.i.m.p.o.r.t.a.n.t.d.e.s.c.r.i.p.t.i.o.n"  
    }
	
**Example**-2:
    After running split function match result transformed into list object, running join against list will produce string with values separated by ":" character
	
    * Sample data is:
    interface GigabitEthernet3/3 |br|
     switchport trunk allowed vlan add 138,166,173,400,401,410
     
    * If template is:
    interface {{ interface }}  |br|
     switchport trunk allowed vlan add {{ trunk_vlans | split(',') | join(':') }}
    
    * Result will be:
    {
        "interface": "GigabitEthernet3/3"  |br|
        "trunkVlans": "138:166:173:400:401:410"
    }
	
append
------------------------------------------------------------------------------
``{{ variable | append(string) }}``

* string (mandatory) - string append to match rsult

Appends string to match result and returns produced value

**Example**:
    * Sample data is:
    interface GigabitEthernet3/3
     
    * Template is:
    interface {{ interface | append(' - non production') }}
    
    * Result will be:
    {
        "interface": "Ge3/3 - non production"  
    }
	
print
------------------------------------------------------------------------------
``{{ variable | print }}``

Will print match result to terminal as is at the given position in chaing, can be used for debuggin purposes

**Example**:
    * Sample data is:
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166,173  
     
    * If template is:
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans | split(',') | print | join(':') print }}
    
    * Output printer to terminal
    ['138', '166', '173'] |br|
    138:166:173
	
unrange
------------------------------------------------------------------------------
``{{ variable | unrange(rangechar, joinchar) }}``

* rangechar (mandatory) - character to indicate range
* joinchar (mandatory) - character used to join range after it is unranged

If match result has integer range in it, this function can be used to extend that range to specific values, For instance if range is 100-105, after passing that result through this function result '101,102,103,104,105' will be produced. That is useful to extend trunk vlan ranges configured on interface.

**Example**:
    * Sample data is:
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166,170-173
     
    * If template is:
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans | unrange(rangechar='-', joinchar=',') }}
    
    * Result will be:
    {
        "interface": "GigabitEthernet3/3"  |br|
        "trunkVlans": "138,166,170,171,172,173"
    }
	
set
------------------------------------------------------------------------------
``{{ variable | set(value) }}``

* value (mandatory) - string to set as a value for variable

Not all configuration statements have variables or values associated with them, but rather serve as an indicator if particular feature is disabled or enabled, to match such a cases *set* function can be used 

**Example**:
    * Sample data is:
    interface GigabitEthernet3/3
     shutdown
	 switchport mode trunk
     
    * If template is:
    interface {{ interface }}
     shutdown {{ interface_disabled | set('True') }}
	 switchport mode trunk {{ switchport_mode | set('Trunk') }} {{ trunk_vlans | set('all') }}
    
    * Result will be:
    {
        "interface": "GigabitEthernet3/3"  |br|
        "interface_disabled": "True" |br|
		"switchport_mode": "Trunk" |br|
		"trunk_vlans": "all"
    }
	
Multiple set statements are supported within the line, however, no other variables can be specified except with *set*, for instance below will not work together: |br|
switchport mode {{ mode }} {{ switchport_mode | set('Trunk') }} {{ trunk_vlans | set('all') }} |br|
as match performed based on the string preceeded variables with *set* function