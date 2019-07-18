Inputs
======
.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
Inputs can used to specify data location and how it should be loaded or filtered. Inputs can be attached to groups for pasrsing, say that this particualr iput data should be parsed by this set of groups only. That can help to increase the overall performance as only data belonging to parsticular group will be parsed. 

.. list-table:: input attributes
   :widths: 10 90
   :header-rows: 1

   * - Attribute
     - Description
   * - `name`_   
     - Uniquely identifies input within template
   * - `groups`_   
     - Specifies group(s) that should be used to parse input data
   * - `load`_   
     - Identifies thae loader that should be used to load text data for input tag itself

name
------------------------------------------------------------------------------
``name="string"``

* string (optional) - name of the input that can used to reference in group *input* attributes. Default value is "Default_Input" and used internaly to store set of data that should be parsed by all groups.

groups
------------------------------------------------------------------------------
``groups="group1, group2, ... , groupN"``

* groupN (optional) - Default value is "all", comma separated string of group names that should be used to parse given input data. If value is "all" - input data will be parsed by each group

load
------------------------------------------------------------------------------
``load="loader_name"``

* loader_name (optional) - name of the loader that should be used to load input tag text data, supported values are python, yaml, json or text. If text used as a loader, text data within input tag itself used as an input data and parsed by a set of given groups or by all groups.

**Example**

Below template contains data that should be parsed within input itself, that is useful for example for testing purposes.

Template:

.. code-block:: html

    <input name="test1" load="text" groups="interfaces.trunks">
    interface GigabitEthernet3/3
     switchport trunk allowed vlan add 138,166-173 
    !
    interface GigabitEthernet3/4
     switchport trunk allowed vlan add 100-105
    !
    interface GigabitEthernet3/5
     switchport trunk allowed vlan add 459,531,704-707
    </input>
    
    <group name="interfaces.trunks">
    interface {{ interface }}
     switchport trunk allowed vlan add {{ trunk_vlans }}
    </group>

Result:

.. code-block::

    [
        {
            "interfaces": {
                "trunks": [
                    {
                        "interface": "GigabitEthernet3/3",
                        "trunk_vlans": "138,166-173"
                    },
                    {
                        "interface": "GigabitEthernet3/4",
                        "trunk_vlans": "100-105"
                    },
                    {
                        "interface": "GigabitEthernet3/5",
                        "trunk_vlans": "459,531,704-707"
                    }
                ]
            }
        }
    ]