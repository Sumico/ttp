.. |br| raw:: html

   <br />

Match Indicators
================

Indicators or directives are strings of text that serve to change parsing logic or indicate certain events.
	 
.. list-table:: indicators
   :widths: 10 90
   :header-rows: 1
   
   * - Name
     - Description  
   * - `_exact_`_ 
     - Threats digits as is without replacing them with '\d+' pattern
   * - `_start_`_ 
     - Explicitly indicates start of the group
   * - `_end_`_ 
     - Explicitly indicates end of the group
   * - `_line_`_ 
     - If present any line will be matched

_exact_
------------------------------------------------------------------------------
``{{ name | _exact_ }}``

By default all digits in template replaced with '\d+' pattern, if _exact_ present all digits will stay as and will used for parsing

**Example**

Sample Data:
::
 vrf VRF-A
  address-family ipv4 unicast
   maximum prefix 1000 80
  !
  address-family ipv6 unicast
   maximum prefix 300 80
  !
  
If template is:
::
 <group name="vrfs">
 vrf {{ vrf }}
  <group name="ipv4_config">
  address-family ipv4 unicast {{ _start_ }}
   maximum prefix {{ limit }} {{ warning }}
  !{{ _end_ }}
  </group>
 </group>
   
Result will be:
::
 {
     "vrfs": {
         "ipv4_config": [
             {
                 "limit": "1000",
                 "warning": "80"
             },
             {
                 "limit": "300",
                 "warning": "80"
             }
         ],
         "vrf": "VRF-A"
     }
 }
 
As you can see ipv6 part of vrf configuration was matched as well and we got undesirable results, one of the possible solutions would be to use _exact_ directive to indicate taht "ipv4" should be matches exactly.

If template is:
::
 <group name="vrfs">
 vrf {{ vrf }}
  <group name="ipv4_config">
  address-family ipv4 unicast {{ _start_ }}{{ _exact_ }}
   maximum prefix {{ limit }} {{ warning }}
  !{{ _end_ }}
  </group>
 </group>
 
Result will be:
::
 {
     "vrfs": {
         "ipv4_config": {
             "limit": "1000",
             "warning": "80"
         },
         "vrf": "VRF-A"
     }
 }
 
_start_
------------------------------------------------------------------------------
``{{ name | _start_ }}`` or {{ _start_ }}

This directive can be used to explicitly indicate start of the group by matching certain line or if we have multiple lines that can indicate start of the same group.

**Example-1** 

In this example line "-------------------------" can serve as indicator of the beginning of the group, but we do not have any match variables defined in it.

Sample data:
::
 switch-a#show cdp neighbors detail 
 -------------------------
 Device ID: switch-b
 Entry address(es): 
   IP address: 131.0.0.1
 
 -------------------------
 Device ID: switch-c
 Entry address(es): 
   IP address: 131.0.0.2
   
Template is:
::
 <group name="cdp_peers">
 ------------------------- {{ _start_ }}
 Device ID: {{ peer_hostname }}
 Entry address(es): 
   IP address: {{ peer_ip }}
 </group>
 
Result:
::
 {
     "cdp_peers": [
         {
             "peer_hostname": "switch-b",
             "peer_ip": "131.0.0.1"
         },
         {
             "peer_hostname": "switch-c",
             "peer_ip": "131.0.0.2"
         }
     ]
 }
 
**Exaple-2**

Here two different lines can serve as an indicator of the start for the same group.

Sample Data:
::
 interface Tunnel2422
  description cpe-1
 !
 interface GigabitEthernet1/1
  description core-1
  
Template is:
::
 <group name="interfaces">
 interface Tunnel{{ if_id }}
 interface GigabitEthernet{{ if_id | _start_ }}
  description {{ description }}
 </group>
 
Result will be:
::
 {
     "interfaces": [
         {
             "description": "cpe-1",
             "if_id": "2422"
         },
         {
             "description": "core-1",
             "if_id": "1/1"
         }
     ]
 }
 
_end_
------------------------------------------------------------------------------
``{{ name | _end_ }}`` or ``{{ _end_ }}``

TBD

_line_
------------------------------------------------------------------------------
``{{ name | _line_ }}``

TBD