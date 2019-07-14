Group Name Attribute
====================

Group attribute *name* used to uniquely identify group and its results within restults structure. This attribute is a dot separated string, there is every dot represents a next level in hierarchy. This string is plit into items using dot character and converted into nested hierarchy of dictionarie/lists.

Consider a group with this name attribute value:

.. code-block:: html

    <group name="interfaces.vlan.L3.vrf-enabled" containsall="ip, vrf">
    interface {{ interface }}
      description {{ description }}
      ip address {{ ip }}/{{ mask }}
      vrf {{ vrf }}
    </group>
	
If below data parsed with that template:

.. code-block::

    interface Port-Chanel11
      description Storage Management
    !
    interface Loopback0
      description RID
      ip address 10.0.0.3/24
    !
    interface Vlan777
      description Management
      ip address 192.168.0.1/24
      vrf MGMT
	  
This result will be prodiced:

.. code-block::

    [
        {
            "interfaces": {
                "SVIs": {
                    "L3": {
                        "vrf-enabled": {
                            "description": "Management",
                            "interface": "Vlan777",
                            "ip": "192.168.0.1",
                            "mask": "24",
                            "vrf": "MGMT"
                        }
                    }
                }
            }
        }
    ]
	
Name attribute allows to from arbitrary (from prectical perspective) depth structure in a deterministic fashion, enabling and easieng further programmatic consumption of produced results.
