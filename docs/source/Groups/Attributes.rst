Attributes
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
     - Used to provide the name of input tag or OS path string to files location that needs to be parsed by this group
   * - `default`_   
     - Contains default value that should be set for all variables if nothing been matched
   * - `method`_   
     - Indicates parsing method, supported values are *group* or *table*
   * - `output`_   
     - Specify group specific outputs to run group result through	 

name
------------------------------------------------------------------------------
``name="path_string"``

* path_string (mandatory) - this is the only attribute that *must* be set for each group, path is a dot separated string that indicates group results placement in results structure.

More on name attribute: Group Name Attribute

input
------------------------------------------------------------------------------
``input="input1, input2, ... , inputN"``

* inputN (optional) - comma separated string that contains names of the input tags that should be used to source data for this group. Order of inputs defined not preserved, i.e. even though input2 comes after input1, input2 data might be run first by the group, followed by input1 data. Input value can also be Operating System fully qualified path to location of text file(s) that should be parsed by this group.

.. note:: Input attributed only supported byt top group, nested groups' input attributes are ignored.

**Example**

Template:

.. code-block:: html

    <input name="test1" load="text">
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166-173 
    </input>
    
    <group name="interfaces" input="test1">
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans }}
    </group>
	
Result:

.. code-block::

    [
        {
            "interfaces": {
                "interface": "GigabitEthernet3/3",
                "trunk_vlans": "138,166-173"
            }
        }
    ]

default
------------------------------------------------------------------------------
``default="value"``

* value (optional) - string that should be used as a default value for all variables within this group.

**Example**

Template: 

.. code-block:: html

    <input name="test1" load="text">
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166-173 
    </input>
    
    <group name="interfaces" input="test1" default="some_default_value">
    interface {{ interface }}
     description {{ description }}
     switchport trunk allowed vlan add {{ trunk_vlans }}
     ip address {{ ip }}
    </group>

Result:

.. code-block::

    [
        {
            "interfaces": {
                "description": "some_default_value",
                "interface": "GigabitEthernet3/3",
                "ip": "some_default_value",
                "trunk_vlans": "138,166-173"
            }
        }
    ]

method
------------------------------------------------------------------------------
``method="value"``

* value (optional) - [group | table] default is *group*. If method it *group* only first regular expression in group considered as group-start-re, in addition template lines that contain *_start_* indicator also used as group-start-re.

On the other hadn, if maethod set to *table* each and every regular expression in the group considered as group-start-re, that is very useful if semi-table data structure parsed, and we have several variations of row.

**Example**

In this example arp table needs to be parsed, but to match all the variations we have
to define several tamplate expressions.

Data:

.. code-block::

    CSR1Kv-3-lab#show ip arp
    Protocol  Address          Age (min)  Hardware Addr   Type   Interface
    Internet  10.1.13.1              98   0050.5685.5cd1  ARPA   GigabitEthernet2.13
    Internet  10.1.13.3               -   0050.5685.14d5  ARPA   GigabitEthernet2.13

Template:

This is the template with default method *group*

.. code-block:: html

    <group name="arp">
    Internet  {{ ip }}  {{ age | DIGIT }}   {{ mac }}  ARPA   {{ interface }}
    Internet  {{ ip }}  -                   {{ mac }}  ARPA   {{ interface| _start_}}
    </group>

This is functionally the same template but with method *table*

.. code-block:: html

    <group name="arp" method="table">
    Internet  {{ ip }}  {{ age | DIGIT }}   {{ mac }}  ARPA   {{ interface }}
    Internet  {{ ip }}  -                   {{ mac }}  ARPA   {{ interface }}
    </group>

Result:

.. code-block::

    [
        {
            "arp": [
                {
                    "age": "98",
                    "interface": "GigabitEthernet2.13",
                    "ip": "10.1.13.1",
                    "mac": "0050.5685.5cd1"
                },
                {
                    "interface": "GigabitEthernet2.13",
                    "ip": "10.1.13.3",
                    "mac": "0050.5685.14d5"
                }
            ]
        }
    ]
	
	
output
------------------------------------------------------------------------------
``output="output1, output2, ... , outputN"``

* outputN (optional) - comma separated string of output tag names that should be used to run group results through. The sequence of outputs provided *are preserved* and run sequentially, meaning that output2 will run only after output1.

.. note:: only top group supports output attribute, nested groups' output attributes are ignored.