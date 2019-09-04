Match Variables
===============

Match variables used to denote the names of pieces of information that needs to be extracted from text data. For instance in this template::

    <group name="interfaces">
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans }}
    </group>
	
match variables are 'interface' and 'trunk_vlans' will store matching results extracted from text data that might look like this::

    interface GigabitEthernet3/4
     switchport trunk allowed vlan add 771,893
	!
    interface GigabitEthernet3/5
     switchport trunk allowed vlan add 138,166-173 

In other works if above data tobe parsed with given emplate, results will look like::

    [
        {
            "interfaces": {
                "interface": "GigabitEthernet3/4",
                "trunk_vlans": "771,893"
            },
            {
                "interface": "GigabitEthernet3/5",
                "trunk_vlans": "138,166-173"
            }
        }
    ]
	
In addition match variables can be accompanied with various function to process data during parsing, or regular expression patterns can be added to use for data parsing. Match variables combined with groups defines the way how data parsed, processed and stored. 

Match Variables reference
-------------------------

.. toctree::
   :maxdepth: 2
   
   Indicators
   Functions
   Patterns