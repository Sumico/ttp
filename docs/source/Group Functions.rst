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
   * - `contains`_ 
     - checks if group result contains matche at least for one of given variables
	 
containsall
------------------------------------------------------------------------------
``containsall="variable1, variable2, variableN"``

* variable (mandatory) - a comma-separated string that contains match variable names. This function
checks if group results contain specified variable, if at least one variable not found in results, whole group
result discarded

**Example**

For instance we want to get results only for interfaces that has IP address configured on them **and** vrf, 
all the rest of interfaces should not make it to results.

Data:

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

Template:

.. code-block:: html

    <group name="interfaces" containsall="ip, vrf">
    interface {{ interface }}
      description {{ description }}
      ip address {{ ip }}/{{ mask }}
      vrf {{ vrf }}
    </group>

Result:

.. code-block::

    {
        "interfaces": {
            "description": "Management",
            "interface": "Vlan777",
            "ip": "192.168.0.1",
            "mask": "24",
            "vrf": "MGMT"
        }
    }

contains
------------------------------------------------------------------------------
``contains="variable1, variable2, variableN"``

* variable (mandatory) - a comma-separated string that contains match variable names. This function
checks if group results contains *any* of specified variable, if no variables found in results, whole group
result discarded, if at least one variable found in results, this check is satisfied.

**Example**

For instance we want to get results only for interfaces that has IP address configured on them **or** vrf.

Data:

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

Template:

.. code-block:: html

    <group name="interfaces" contains="ip, vrf">
    interface {{ interface }}
      description {{ description }}
      ip address {{ ip }}/{{ mask }}
      vrf {{ vrf }}
    </group>

Result:

.. code-block::

    {
        "interfaces": [
            {
                "description": "RID",
                "interface": "Loopback0",
                "ip": "10.0.0.3",
                "mask": "24"
            },
            {
                "description": "Management",
                "interface": "Vlan777",
                "ip": "192.168.0.1",
                "mask": "24",
                "vrf": "MGMT"
            }
        ]
    }