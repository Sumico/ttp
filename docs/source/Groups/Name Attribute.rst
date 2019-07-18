Name Attribute
==============

Group attribute *name* used to uniquely identify group and its results within restults structure. This attribute is a dot separated string, there is every dot represents a next level in hierarchy. This string is split into **path items** using dot character and converted into nested hierarchy of dictionaries and/or lists.

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
	
Name attribute allows to from arbitrary (from practical perspective) depth structure in a deterministic fashion, enabling further programmatic consumption of produced results.

Path formatters
---------------

Group *name* attribute supports path formatters \* and \*\* following below rules:

* If single start character \* used as a suffix (append to the end) of path item, next level (child) of this path item will be a list structure
* If double start character \*\* used as a suffix (append to the end) of path item, next level (child) of this path item will be a dictionary structure

**Example**

Consider this group with name attribute formed in such a way that interfaces child will be a list and child of L3 path item also will be a list for whatever reason.

.. code-block:: html

    <group name="interfaces*.vlan.L3*.vrf-enabled" containsall="ip, vrf">
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
            "interfaces": [              <----this is the start of nested list
                {
                    "vlan": {
                        "L3": [          <----this is the start of another nested list
                            {
                                "vrf-enabled": {
                                    "description": "Management",
                                    "interface": "Vlan777",
                                    "ip": "192.168.0.1",
                                    "mask": "24",
                                    "vrf": "MGMT"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    ]
	
Dynamic Path
------------

Above are examples of static path, where all the path items are known and predefined beforehand, however, ttp suppots dynamic path formation using match variable results for certain match variable names, i.e we have match variable name set to *interface* and correspondent match result would be Gi0/1, it is possible to use Gi0/1 as a path item. 

Search for dynamic path item value happens using below sequence:
*First* group match results searched for path item value, if not found, 
*Second*, upper group results cache (latest values) used, if not found, 
*Third*, template variables searched for path item value, if not found 
*Last*, group results discarded as invalid

**Example-1**

Data:

.. code-block::

    interface Port-Chanel11
      description Storage
    !
    interface Loopback0
      description RID
      ip address 10.0.0.3/24
    !
    interface Vlan777
      description Management
      ip address 192.168.0.1/24
      vrf MGMT
	  
Template:

.. code-block:: html

    <group name="interfaces.{{ interface }}">
    interface {{ interface }}
      description {{ description }}
      ip address {{ ip }}/{{ mask }}
      vrf {{ vrf }}
    </group>
	  
Result:

.. code-block::

    [
        {
            "interfaces": {
                "Loopback0": {
                    "description": "RID",
                    "ip": "10.0.0.3",
                    "mask": "24"
                },
                "Port-Chanel11": {
                    "description": "Storage"
                },
                "Vlan777": {
                    "description": "Management",
                    "ip": "192.168.0.1",
                    "mask": "24",
                    "vrf": "MGMT"
                }
            }
        }
    ]
	
As a result interface varibale match value used as a key to form path for the group.

Because each path item is a string, and each item produced by spilling name attributes using '.' dot character, it is possible to produce dynamic path there portions of path item will be dynamically substituted.


Data:

.. code-block::

    interface Port-Chanel11
      description Storage
    !
    interface Loopback0
      description RID
      ip address 10.0.0.3/24
    !
    interface Vlan777
      description Management
      ip address 192.168.0.1/24
      vrf MGMT
	  
Template:

.. code-block:: html

    <group name="interfaces.cool_{{ interface }}_interface">
    interface {{ interface }}
      description {{ description }}
      ip address {{ ip }}/{{ mask }}
      vrf {{ vrf }}
    </group>
	  
Result:

.. code-block::

    [
        {
            "interfaces": {
                "cool_Loopback0_interface": {
                    "description": "RID",
                    "ip": "10.0.0.3",
                    "mask": "24"
                },
                "cool_Port-Chanel11_interface": {
                    "description": "Storage"
                },
                "cool_Vlan777_interface": {
                    "description": "Management",
                    "ip": "192.168.0.1",
                    "mask": "24",
                    "vrf": "MGMT"
                }
            }
        }
    ]
	
Nested hierarchies also supported with dynamic path, as if no variable found in the group match results ttp will try ti find variable in the dynamic path cache or template variables.

**Example-3**

Data:

.. code-block::

    ucs-core-switch-1#show run | section bgp
    router bgp 65100
      vrf CUST-1
        neighbor 59.100.71.193
          remote-as 65101
          description peer-1
          address-family ipv4 unicast
            route-map RPL-1-IMPORT-v4 in
            route-map RPL-1-EXPORT-V4 out
          address-family ipv6 unicast
            route-map RPL-1-IMPORT-V6 in
            route-map RPL-1-EXPORT-V6 out
        neighbor 59.100.71.209
          remote-as 65102
          description peer-2
          address-family ipv4 unicast
            route-map AAPTVRF-LB-BGP-IMPORT-V4 in
            route-map AAPTVRF-LB-BGP-EXPORT-V4 out
	  
Template:

.. code-block:: html

    <vars>
    hostname = "gethostname"
    </vars>
    
    <group name="{{ hostname }}.router.bgp.BGP_AS_{{ asn }}">
    router bgp {{ asn }}
      <group name="vrfs.{{ vrf_name }}">
      vrf {{ vrf_name }}
        <group name="peers.{{ peer_ip }}">
        neighbor {{ peer_ip }}
          remote-as {{ peer_asn }}
          description {{ peer_description }}
    	  <group name="afi.{{ afi }}.unicast">
          address-family {{ afi }} unicast
            route-map {{ rpl_in }} in
            route-map {{ rpl_out }} out
    	  </group>
    	</group>
       </group>
    </group>
	
Result:

.. code-block:: yaml

    - ucs-core-switch-1:
        router:
          bgp:
            BGP_AS_65100:
              vrfs:
                CUST-1:
                  peers:
                    59.100.71.193:
                      afi:
                        ipv4:
                          unicast:
                            rpl_in: RPL-1-IMPORT-v4
                            rpl_out: RPL-1-EXPORT-V4
                        ipv6:
                          unicast:
                            rpl_in: RPL-1-IMPORT-V6
                            rpl_out: RPL-1-EXPORT-V6
                      peer_asn: '65101'
                      peer_description: peer-1
                    59.100.71.209:
                      afi:
                        ipv4:
                          unicast:
                            rpl_in: RPL-2-IMPORT-V6
                            rpl_out: RPL-2-EXPORT-V6
                      peer_asn: '65102'
                      peer_description: peer-2