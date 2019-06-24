.. |br| raw:: html

   <br />

Match functions
===============

Description of ttp built-in functions that can be applied to match results. 

Action functions below act upon match result to transform it to desired state.
  
.. list-table:: action functions
   :widths: 10 90
   :header-rows: 1

   * - Name
     - Description
   * - `chain`_ 
     - add functions from chain variable 
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
   * - `replaceall`_ 
     - run replace against match for all given values
   * - `resuball`_ 
     - run re substitute against match for all given values
   * - `lookup`_ 
     - find match value in lookup table and return result
   * - `rlookup`_ 
     - find rlookup table key in match result and return assiciated values
 
Condition functions can perform various checks with match results and produce either True or False result

.. list-table:: condition functions
   :widths: 10 90
   :header-rows: 1
   
   * - Name
     - Description  
   * - `startswith_re`_ 
     - checks if match starts with certain string using regular expression
   * - `endswith_re`_ 
     - checks if match ends with certain string using regular expression
   * - `contains_re`_ 
     - checks if match contains certain string using regular expression
   * - `contains`_ 
     - checks if match contains certain string
   * - `notstartswith_re`_ 
     - checks if match not starts with certain string using regular expression
   * - `notendswith_re`_ 
     - checks if match not ends with certain string using regular expression
   * - `exclude_re`_ 
     - checks if match not contains certain string using regular expression
   * - `exclude`_ 
     - checks if match not contains certain string
   * - `isdigit`_ 
     - checks if match is digit string e.g. '42'
   * - `notdigit`_ 
     - checks if match is not digit string
   * - `greaterthan`_ 
     - checks if match is greater than given value
   * - `lessthan`_ 
     - checks if match is less than given value

Match indicators used to change parsing logic or indicate certain events.
	 
.. list-table:: indicators
   :widths: 10 90
   :header-rows: 1
   
   * - Name
     - Description  
   * - `_exact_`_ 
     - TBD
   * - `_start_`_ 
     - TBD
   * - `_end_`_ 
     - TBD
   * - `_line_`_ 
     - TBD

Regex formatters help to specify regular expressions that should be used to match certain variables. 
	 
.. list-table:: indicators
   :widths: 10 90
   :header-rows: 1
   
   * - Name
     - Description  
   * - `PHRASE`_ 
     - TBD
   * - `ORPHRASE`_ 
     - TBD
   * - `WORD`_ 
     - TBD
	 
Apart from ttp functions described above python objects built-in functions can be used as well. For instance string m

chain
------------------------------------------------------------------------------
``{{ name | chain(variable) }}``

* variable (mandatory) - string containing variable name

Description goes here... 
	
record
------------------------------------------------------------------------------
``{{ name | record(name) }}``

* name (mandatory) - a string containing variable name

Records match results in variable with given name after all functions run

truncate
--------
``{{ name | truncate(count) }}``

* count (mandatory) - integer to count the number of words to remove

Splits match result using " "(space) char and joins it back up to truncate value. This function can be useful to shorten long match results.

**Example**

If match is "foo bar foo-bar" and truncate(2) will produce "foo bar". 
  
joinmatches
------------------------------------------------------------------------------
``{{ name | joinmatches(char) }}``

* char (optional) - character to use to join matches, default is new line '\\n'

Join results from different matches into a single result string using provider charcter or string. 

**Example**

Sample data is:
::
    interface GigabitEthernet3/3
    switchport trunk allowed vlan add 138,166,173 
    switchport trunk allowed vlan add 400,401,410
 
If template is:
::
    interface {{ interface }}
    switchport trunk allowed vlan add {{ trunk_vlans | joinmatches(',') }}

Result will be:
::
    {
        "interface": "GigabitEthernet3/3"  
        "trunkVlans": "138,166,173,400,401,410"
    }
    
resub
------------------------------------------------------------------------------
``{{ name | resub(old, new) }}``

* old (mandatory) - pattern to be replaced
* new (mandatory) - pattern to be replaced with

Performs re.sub(old, new, match, count=1) on match result and returns produced value

**Example**

Sample data is:
::
    interface GigabitEthernet3/3
 
Template is:
::
    interface {{ interface | resub(old = '^GigabitEthernet'), new = 'Ge'}}

Result will be:
::
    {
        "interface": "Ge3/3"  
    }
    
join
------------------------------------------------------------------------------
``{{ name | match(char) }}``

* char (mandatory) - character to use to join match

Run joins against match result using provided character and return string


**Example**-1:

Match is a string here and running join against it will inser '.' in between each charscter 

Sample data is:
::
    description someimportantdescription
 
Template is:
::
    description {{ description | join('.') }}

Result will be:
::
    {
        "description": "s.o.m.e.i.m.p.o.r.t.a.n.t.d.e.s.c.r.i.p.t.i.o.n"  
    }
    
**Example**-2:

After running split function match result transformed into list object, running join against list will produce string with values separated by ":" character

Sample data is:
::
    interface GigabitEthernet3/3 
     switchport trunk allowed vlan add 138,166,173,400,401,410
 
If template is:
::
    interface {{ interface }}  
     switchport trunk allowed vlan add {{ trunk_vlans | split(',') | join(':') }}

Result will be:
::
    {
        "interface": "GigabitEthernet3/3"  
        "trunkVlans": "138:166:173:400:401:410"
    }
    
append
------------------------------------------------------------------------------
``{{ name | append(string) }}``

* string (mandatory) - string append to match rsult

Appends string to match result and returns produced value

**Example**

Sample data is:
::
    interface Ge3/3
 
Template is:
::
    interface {{ interface | append(' - non production') }}

Result will be:
::
    {
        "interface": "Ge3/3 - non production"  
    }
    
print
------------------------------------------------------------------------------
``{{ name | print }}``

Will print match result to terminal as is at the given position in chaing, can be used for debuggin purposes

**Example**

Sample data is:
::
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166,173  
 
If template is:
::
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans | split(',') | print | join(':') print }}

Output printer to terminal
::
    ['138', '166', '173'] 
    138:166:173
    
unrange
------------------------------------------------------------------------------
``{{ name | unrange('rangechar', 'joinchar') }}``

* rangechar (mandatory) - character to indicate range
* joinchar (mandatory) - character used to join range after it is unranged

If match result has integer range in it, this function can be used to extend that range to specific values, For instance if range is 100-105, after passing that result through this function result '101,102,103,104,105' will be produced. That is useful to extend trunk vlan ranges configured on interface.

**Example**

Sample data is:
::
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166,170-173
 
If template is:
::
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans | unrange(rangechar='-', joinchar=',') }}

Result will be:
::
    {
        "interface": "GigabitEthernet3/3"  
        "trunkVlans": "138,166,170,171,172,173"
    }
    
set
------------------------------------------------------------------------------
``{{ name | set('value') }}``

* value (mandatory) - string to set as a value for variable

Not all configuration statements have variables or values associated with them, but rather serve as an indicator if particular feature is disabled or enabled, to match such a cases *set* function can be used 

**Example**

Sample data
::
    interface GigabitEthernet3/3
     shutdown
     switchport mode trunk
 
Template
::
    interface {{ interface }}
     shutdown {{ interface_disabled | set('True') }}
     switchport mode trunk {{ switchport_mode | set('Trunk') }} {{ trunk_vlans | set('all') }}

Result
::
    {
        "interface": "GigabitEthernet3/3"  
        "interface_disabled": "True"  
        "switchport_mode": "Trunk"  
        "trunk_vlans": "all"
    }
    
.. note:: Multiple set statements are supported within the line, however, no other variables can be specified except with *set*, as match performed based on the string preceeding variables with *set* function, for instance below will not work: |br|
 switchport mode {{ mode }} {{ switchport_mode | set('Trunk') }} {{ trunk_vlans | set('all') }} 

replaceall
------------------------------------------------------------------------------
``{{ name | replaceall('value1', 'value2', ..., 'valueN') }}``

* value (mandatory) - string to replace in match

Run string replace method on match with *new* and *old* values derived using below rules.

**Case 1** If only one value given *new* set to '' empty value, if several values specified *new* set to first value

**Example-1.1** With *new* set to '' empty value

*Sample data*
::
    interface GigabitEthernet3/3 
    interface GigEthernet5/7 
    interface GeEthernet1/5
 
Template
::
    interface {{ interface | replaceall('Ethernet') }}

Result
::
    {'interface': 'Gigabit3/3'} 
    {'interface': 'Gig5/7'} 
    {'interface': 'Ge1/5'}
    
**Example-1.2** With *new* set to 'Ge'

Sample data
::
    interface GigabitEthernet3/3 
    interface GigEth5/7 
    interface Ethernet1/5
 
Template
::
    interface {{ interface | replaceall('Ge', 'GigabitEthernet', 'GigEth', 'Ethernet') }}

Result
::
    {'interface': 'Ge3/3'} 
    {'interface': 'Ge5/7'} 
    {'interface': 'Ge1/5'}
    
**Case 2** If value found in variables that variable used, if variable value is  a list, function will iterate over list and for each item run replace where *new* set either to "" empty or to first value and *old* equal to each list item

**Example-2.1** With *new* set to 'GE' value

Sample data
::
    interface GigabitEthernet3/3 
    interface GigEthernet5/7 
    interface GeEthernet1/5
 
Template
::
    <vars load="python">
    intf_replace = ['GigabitEthernet', 'GigEthernet', 'GeEthernet']
    </vars>
    
    <group name="ifs">
    interface {{ interface | replaceall('GE', 'intf_replace') }}
    <group>   
    
Result
::
    {
        "ifs": [
            {
                "interface": "GE3/3"
            },
            {
                "interface": "GE5/7"
            },
            {
                "interface": "GE1/5"
            }
        ]
    }
    
**Example-2.2** With *new* set to '' empty value

Sample data
::
    interface GigabitEthernet3/3 
    interface GigEthernet5/7 
    interface GeEthernet1/5
 
Template
::
    <vars load="python">
    intf_replace = ['GigabitEthernet', 'GigEthernet', 'GeEthernet']
    </vars>
    
    <group name="ifs">
    interface {{ interface | replaceall('intf_replace') }}
    <group>   
    
Result
::
    {
        "ifs": [
            {
                "interface": "3/3"
            },
            {
                "interface": "5/7"
            },
            {
                "interface": "1/5"
            }
        ]
    }
    
**Case 3** If value found in variables that variable used, if variable value is  a dictionary, function will iterate over dictioanry items and set *new* to item key and *old* to item value. 
* If item value is a list, function will iterate over list and run replace using each entrie as *old* value
* If item value is a string, function will use that strin as *old* value

**Example-3.1** With dictionary values as lists

Sample data
::
    interface GigabitEthernet3/3 
    interface GigEthernet5/7 
    interface GeEthernet1/5
    interface Loopback1/5
    interface TenGigabitEth3/3 
    interface TeGe5/7 
    interface 10GE1/5
 
Template
::
    <vars load="python">
    intf_replace = {
                    'Ge': ['GigabitEthernet', 'GigEthernet', 'GeEthernet'],
                    'Lo': ['Loopback'],
                    'Te': ['TenGigabitEth', 'TeGe', '10GE']
                    }
    </vars>
    
    <group name="ifs">
    interface {{ interface | replaceall('intf_replace') }}
    <group>   
    
Result
::
    {
        "ifs": [
            {
                "interface": "Ge3/3"
            },
            {
                "interface": "Ge5/7"
            },
            {
                "interface": "Ge1/5"
            },
            {
                "interface": "Lo1/5"
            },
            {
                "interface": "Te3/3"
            },
            {
                "interface": "Te5/7"
            }
        ]
    }
    
resuball
------------------------------------------------------------------------------
``{{ name | resuball('value1', 'value2', ..., 'valueN') }}``

* value(mandatory) - string to replace in match

Same as `replaceall`_ but instead of string replace this function runs python re substitute method, allowing the use of regular expression to match *old* values.

**Example**

If *new* set to "Ge" and *old* set to "GigabitEthernet", running string replace against "TenGigabitEthernet" match will produce "Ten" as undesirable result, to overcome that problem regular expressions can be used. For instance, regex "^GigabitEthernet" will only match "GigabitEthernet3/3" as "^" symbol indicates beginning of the string and will not match "GigabitEthernet" in "TenGigabitEthernet".

Data
::
 interface GigabitEthernet3/3 
 interface TenGigabitEthernet3/3 
 
Template
::
 <vars load="python">
 intf_replace = {
                 'Ge': ['^GigabitEthernet'],
                 'Te': ['^TenGigabitEthernet']
                 }
 </vars>
 
 <group name="ifs">
 interface {{ interface | replaceall('intf_replace') }}
 <group>   
 
Result
::
 {
     "ifs": [
         {
             "interface": "Ge3/3"
         },
         {
             "interface": "Ge5/7"
         },
         {
             "interface": "Ge1/5"
         },
         {
             "interface": "Lo1/5"
         },
         {
             "interface": "Te3/3"
         },
         {
             "interface": "Te5/7"
         }
     ]
 }
 
lookup
------------------------------------------------------------------------------
``{{ name | lookup('name', 'add_field') }}``

* name(mandatory) - lookup name and dot-separated path to data within which to perform lookup
* add_field(optional) - default is False, can be set to string that will indicate name of the new field

Lookup function takes match value and perform lookup on that value in lookup table. Lookup table is a dictionary data where keys checked if they are equal to math result.

If lookup was unsuccesful no changes introduces to match result, if it was successful we have two option on what to do with looked up values:
* if add_field is False - match result will be replaced with found values
* if add_field is not False - string passed as add_field value used as a name for additional field that will be added to group match results

**Example-1** *add_field* set to False

In this example, as 65101 will be looked up in the lookup table and replaced with found values

Data
::
 router bgp 65100
   neighbor 10.145.1.9
     remote-as 65101
   !
   neighbor 192.168.101.1
     remote-as 65102
 
Template
::
 <lookup name="ASNs" load="csv">
 ASN,as_name,as_description
 65100,Customer_1,Private ASN for CN451275
 65101,CPEs,Private ASN for FTTB CPEs
 </lookup>
 
 <group name="bgp_config">
 router bgp {{ bgp_as }}
  <group name="peers">
   neighbor {{ peer }}
     remote-as {{ remote_as | lookup('ASNs') }}
  </group>
 </group> 
 
Result
::
 {
     "bgp_config": {
         "bgp_as": "65100",
         "peers": [
             {
                 "peer": "10.145.1.9",
                 "remote_as": {
                     "as_description": "Private ASN for FTTB CPEs",
                     "as_name": "CPEs"
                 }
             },
             {
                 "peer": "192.168.101.1",
                 "remote_as": "65102"
             }
         ]
     }
 }

**Example-2** With additional field

Data
::
 router bgp 65100
   neighbor 10.145.1.9
     remote-as 65101
   !
   neighbor 192.168.101.1
     remote-as 65102
 
Template
::
 <lookup name="ASNs" load="csv">
 ASN,as_name,as_description
 65100,Customer_1,Private ASN for CN451275
 65101,CPEs,Private ASN for FTTB CPEs
 </lookup>
 
 <group name="bgp_config">
 router bgp {{ bgp_as }}
  <group name="peers">
   neighbor {{ peer }}
     remote-as {{ remote_as | lookup('ASNs', add_field='asn_details') }}
  </group>
 </group> 
 
Result
::
 {
     "bgp_config": {
         "bgp_as": "65100",
         "peers": [
             {
                 "asn_details": {
                     "as_description": "Private ASN for FTTB CPEs",
                     "as_name": "CPEs"
                 },
                 "peer": "10.145.1.9",
                 "remote_as": "65101"
             },
             {
                 "peer": "192.168.101.1",
                 "remote_as": "65102"
             }
         ]
     }
 }
 
rlookup
------------------------------------------------------------------------------
``{{ name | rlookup('name', 'add_field') }}``

* name(mandatory) - rlookup table name and dot-separated path to data within which to perform search
* add_field(optional) - default is False, can be set to string that will indicate name of the new field

This function searches rlookup table keys in match value. rlookup table is a dictionary data where keys checked if they are equal to math result.

If lookup was unsuccesful no changes introduces to match result, if it was successful we have two options:
* if add_field is False - match result will be replaced with found values
* if add_field is not False - string passed as add_field used as a name for additional field to be added to group results, value for that new field is a data from lookup table

**Example**

In this example, bgp neighbours descriptions set to hostnames of peering devices, usually hostnames tend to follow some naming convention to indicate physical location of device or its network role, in below examplenaming convention is *<state>-<city>-<role><num>* 

Data
::
 router bgp 65100
   neighbor 10.145.1.9
     description vic-mel-core1
   !
   neighbor 192.168.101.1
     description qld-bri-core1
 
Template
::
 <lookup name="locations" load="ini">
 [cities]
 -mel- : 7 Name St, Suburb A, Melbourne, Postal Code
 -bri- : 8 Name St, Suburb B, Brisbane, Postal Code
 </lookup>
 
 <group name="bgp_config">
 router bgp {{ bgp_as }}
  <group name="peers">
   neighbor {{ peer }}
     description {{ remote_as | rlookup('locations.cities', add_field='location') }}
  </group>
 </group> 
 
Result
::
 {
     "bgp_config": {
         "bgp_as": "65100",
         "peers": [
             {
                 "description": "vic-mel-core1",
                 "location": "7 Name St, Suburb A, Melbourne, Postal Code",
                 "peer": "10.145.1.9"
             },
             {
                 "description": "qld-bri-core1",
                 "location": "8 Name St, Suburb B, Brisbane, Postal Code",
                 "peer": "192.168.101.1"
             }
         ]
     }
 }
 
startswith_re
------------------------------------------------------------------------------
``{{ name | startswith_re('pattern') }}``

* pattern(mandatory) - string pattern to check

Python re search used to evaluate if match value starts with given string pattern, returns True if so and False otherwise

endswith_re
------------------------------------------------------------------------------
``{{ name | endswith_re('pattern') }}``

* pattern(mandatory) - string pattern to check

Python re search used to evaluate if match value ends with given string pattern, returns True if so and False otherwise

contains_re
------------------------------------------------------------------------------
``{{ name | contains_re('pattern') }}``

* pattern(mandatory) - string pattern to check

Python re search used to evaluate if match value contains given string pattern, returns True if so and False otherwise

contains
------------------------------------------------------------------------------
``{{ name | contains('pattern') }}``

* pattern(mandatory) - string pattern to check

This faunction evaluates if match value contains given string pattern, returns True if so and False otherwise.

notstartswith_re
------------------------------------------------------------------------------
``{{ name | notstartswith_re('pattern') }}``

* pattern(mandatory) - string pattern to check

Python re search used to evaluate if match value starts with given string pattern, returns False if so and True otherwise

notendswith_re
------------------------------------------------------------------------------
``{{ name | notendswith_re('pattern') }}``

* pattern(mandatory) - string pattern to check

Python re search used to evaluate if match value ends with given string pattern, returns False if so and True otherwise

exclude_re
------------------------------------------------------------------------------
``{{ name | exclude_re('pattern') }}``

* pattern(mandatory) - string pattern to check

Python re search used to evaluate if match value contains given string pattern, returns False if so and True otherwise

exclude
------------------------------------------------------------------------------
``{{ name | exclude('pattern') }}``

* pattern(mandatory) - string pattern to check

This faunction evaluates if match value contains given string pattern, returns False if so and True otherwise.

equal
------------------------------------------------------------------------------
``{{ name | equal('value') }}``

* value(mandatory) - string pattern to check

This faunction evaluates if match is equal to given value, returns True if so and False otherwise

notequal
------------------------------------------------------------------------------
``{{ name | notequal('value') }}``

* value(mandatory) - string pattern to check

This faunction evaluates if match is equal to given value, returns False if so and True otherwise

isdigit
------------------------------------------------------------------------------
``{{ name | isdigit }}``

This faunction checks if match is a digit, returns True if so and False otherwise

notdigit
------------------------------------------------------------------------------
``{{ name | notdigit }}``

This faunction checks if match is digit, returns False if so and True otherwise

greaterthan
------------------------------------------------------------------------------
``{{ name | greaterthan('value') }}``

* value(mandatory) - integer value to compare with

This faunction checks if match and supplied value are digits and performs comparison operation, if match is bigger than given value returns True and False otherwise

lessthan
------------------------------------------------------------------------------
``{{ name | lessthan('value') }}``

* value(mandatory) - integer value to compare with

This faunction checks if match and supplied value are digits and performs comparison, if match is smaller than provided value returns True and False otherwise