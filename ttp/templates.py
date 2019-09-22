test = """
interface {{ interface | replaceall('Ethernet') }}
!{{ end }}
"""

test1 = """
<vars load="python">
intf_replace = {
                'Ge': ['GigabitEthernet', 'GigEthernet', 'GeEthernet'],
                'Lo': ['Loopback'],
                'Te': ['TenGigabitEth', 'TeGe', '10GE']
                }
</vars>

<group name="ifs">
interface {{ interface | replaceall('GE', 'intf_replace') }}
</group>  
"""

test2 = """
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
"""

test3 = """
<lookup name="locations" load="ini">
[cities]
-mel- : 7 Name St, Suburb A, Melbourne, Postal Code
-bri- : 8 Name St, Suburb B, Brisbane, Postal Code
</lookup>

<group name="bgp_config">
router bgp {{ bgp_as }}
 <group name="peers">
  neighbor {{ peer }}
    description {{ description | rlookup('locations.cities', add_field='location') }}
 </group>
</group> 
"""

test4 = """
<vars>
vlans = "unrange(rangechar='-', joinchar=',') | split(',') | join(':') | joinmatches(':')"
</vars>

<group name="interfaces">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans | chain('vlans') }}
</group>
"""

test5 = """
<group name="vrfs">
vrf {{ vrf }}
 <group name="ipv4_config">
 address-family ipv4 unicast {{ _start_ }}
  maximum prefix {{ limit }} {{ warning }}
 !{{ _end_ }}
 </group>
</group>
"""

test6 = """
<group name="vrfs">
vrf {{ vrf }}
 <group name="ipv4_config">
 address-family ipv4 unicast {{ _start_ }}{{ _exact_ }}
  maximum prefix {{ limit }} {{ warning }}
 !{{ _end_ }}
 </group>
</group>
"""

test7 = """
<group name="cdp_peers">
------------------------- {{ _start_ }}
Device ID: {{ peer_hostname }}
Entry address(es): 
  IP address: {{ peer_ip }}
</group>
"""

test8 = """
<group name="interfaces">
interface Tunnel{{ if_id }}
interface GigabitEthernet{{ if_id | _start_ }}
 description {{ description }}
</group>
"""

test9 = """
<group name="interfaces">
interface {{ interface | contains("Vlan") }}
 description {{ description }}
</group>
"""

test10 = """
<input load="text">
interface Tunnel2422
 description core-1
!
interface GigabitEthernet1/1
 description core-11
</input>
<group name="interfaces">
interface {{ interface | upper }}
 description {{ description | split('-') | index("core") }}
</group>
"""

test11 = """
<vars>
hostname = 'gethostname'
</vars>

<group name="interfaces.SVIs">
interface {{ interface | contains('Vlan') }}
 description {{ description | ORPHRASE}}
 ip address {{ ip }} {{ mask }}
{{ hostname | let('hostname') }}
</group>

<output 
description="tabulate test https://pyhdust.readthedocs.io/en/latest/tabulate.html"
format="tabulate"
path="interfaces.SVIs"
headers="hostname, interface, ip, mask, description"
format_attributes = "tablefmt='fancy_grid'"
/>

<output 
format="json"
/>
"""

test12 = """
<input name="test11" load="text">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
 switchport trunk allowed vlan add 400,401,410
</input>

<vars>
vlans = "unrange(rangechar='-', joinchar=',') | joinmatches(',')"
</vars>

<group name="interfaces">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans | chain("vlans") }}
</group>
"""




TESTS_TEMPLATES = """
<template>

<!--template to test contains('Vlan')-->
<template 
name="template_test1" 
description="template to run tests with contains('Vlan')"
>
<input name="test1" load="text">
interface Vlan123
 description Desks vlan
 ip address 192.168.123.1 255.255.255.0
!
interface GigabitEthernet1/1
 description to core-1
!
interface Vlan222
 description Phones vlan
 ip address 192.168.222.1 255.255.255.0
!
interface Loopback0
 description Routing ID loopback
</input>

<group name="SVIs">
interface {{ interface | contains("Vlan") }}
 description {{ description | ORPHRASE}}
 ip address {{ ip }} {{ mask }}
</group>

<output 
name="test1" 
load="python" 
functions="is_equal" 
description="test that only interaces with vlan got to results"
returner="terminal"
format="tabulate"
format_attributes="tablefmt='fancy_grid'"
>
[{'SVIs': [{'interface': 'Vlan123', 'description': 'Desks vlan', 'ip': '192.168.123.1', 'mask': '255.255.255.0'}, {'interface': 'Vlan222', 'description': 'Phones vlan', 'ip': '192.168.222.1', 'mask': '255.255.255.0'}]}]
</output>

</template>



<!--template to test chain with unrange and joinmatches-->
<template name="test12">
<input name="test12" load="text">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
 switchport trunk allowed vlan add 400,401,410
</input>

<vars>
vlans = "unrange(rangechar='-', joinchar=',') | joinmatches(',')"
</vars>

<group name="interfaces">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans | chain("vlans") }}
</group>

<output 
name="test12" 
load="json" 
functions="is_equal" 
description="test vlans unrange and joinmatches functions" 
returner="terminal"
format="tabulate"
format_attributes = "tablefmt='fancy_grid'"
>
[{
    "interfaces": {
        "interface": "GigabitEthernet3/3",
        "trunk_vlans": "138,166,167,168,169,170,171,172,173,400,401,410"
    }
}]
</output>
</template>



</template>
"""


TESTS_GROUPS = """
<vars>
vlans = "unrange(rangechar='-', joinchar=',') | joinmatches(',')"
</vars>

<!--template to test chain with unrange and joinmatches-->
<input name="test1" load="text" groups="interfaces">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
 switchport trunk allowed vlan add 400,401,410
</input>

<group name="interfaces" output="test1">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans | chain("vlans") }}
</group>

<output 
name="test1" 
load="json" 
functions="is_equal" 
description="test vlans unrange and joinmatches functions" 
>
{
    "interfaces": {
        "interface": "GigabitEthernet3/3",
        "trunk_vlans": "138,166,167,168,169,170,171,172,173,400,401,410"
    },
    "vars": {
        "vlans": "unrange(rangechar='-', joinchar=',') | joinmatches(',')"
    }
}
</output>


<!--test contains('vlan') for interfaces-->
<input name="test2" load="text" groups="SVIs">
interface Vlan123
 description Desks vlan
 ip address 192.168.123.1 255.255.255.0
!
interface GigabitEthernet1/1
 description to core-1
!
interface Vlan222
 description Phones vlan
 ip address 192.168.222.1 255.255.255.0
!
interface Loopback0
 description Routing ID loopback
</input>

<group name="SVIs" output="test2">
interface {{ interface | contains("Vlan") }}
 description {{ description | ORPHRASE}}
 ip address {{ ip }} {{ mask }}
</group>

<output 
name="test2" 
load="python" 
functions="is_equal" 
description="test that only interaces with vlan got to results"
>
{'vars': {"vlans": "unrange(rangechar='-', joinchar=',') | joinmatches(',')"}, 'SVIs': [{'interface': 'Vlan123', 'description': 'Desks vlan', 'ip': '192.168.123.1', 'mask': '255.255.255.0'}, {'interface': 'Vlan222', 'description': 'Phones vlan', 'ip': '192.168.222.1', 'mask': '255.255.255.0'}]}
</output>



<output 
functions="join_results"
format="tabulate"
returner="terminal"
format_attributes = "tablefmt='fancy_grid'"
/>
"""

test123 = """
<input name="test1" load="text">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
</input>

<group name="interfaces" input="test1">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
</group>
"""

test124 = """
<input name="test1" load="text">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
</input>

<group name="interfaces" input="test1" default="some_default_value">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 ip address {{ ip }}
 description {{ description }}
</group>
"""

test125 = """
<group name="interfaces" containsall="ip, vrf">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
</group>
"""

test128="""
<group name="interfaces" contains="ip, vrf">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
</group>
"""

test126="""
<group name="arp" method="table">
Internet  {{ ip }}  {{ age | DIGIT }}   {{ mac }}  ARPA   {{ interface }}
Internet  {{ ip }}  -                   {{ mac }}  ARPA   {{ interface }}
</group>
"""

test127="""
<group name="arp">
Internet  {{ ip }}  {{ age | DIGIT }}   {{ mac }}  ARPA   {{ interface }}
Internet  {{ ip }}  -                   {{ mac }}  ARPA   {{ interface | _start_ }}
</group>
"""

test129="""
<group name="interfaces.SVIs.L3.vrf-enabled" containsall="ip, vrf">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
</group>
"""

test130="""
<vars name="vars.info*.bla">
hostname='gethostname' 
</vars>

<vars name=''>
caps = "ORPHRASE | upper"
</vars>

<vars name="vars.info*.bla">
filename='getfilename' 
</vars>

<group name="interfaces" contains="ip">
interface {{ interface }}
 description {{ description }}
 ip address {{ ip }} {{ mask }}
 vrf {{ vrf }}
</group>
"""

test131="""
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
"""

test132="""
<group name="interfaces*.vlan.L3*.vrf-enabled" containsall="ip, vrf">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
</group>
"""

test133 = """
<group name="interfaces.{{ interface }}">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
</group>
"""

test134 = """
<group name="interfaces.cool_{{ interface }}_interface">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
</group>
"""

test135="""
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
"""

test136="""
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
"""

test137 = """
<group name="interfaces" contains="helpers" output="out_jinja, out_tabulate">
interface {{ interface }}
 description {{ description | ORPHRASE }}
 vrf forwarding {{ vrf }}
 ip address {{ ip }} {{ mask }}
 ip helper-address {{ helpers | joinmatches(";") }}
! {{ _end_ }}
</group>

<output 
name="out_jinja"
format="jinja2"
returner="terminal"
>
{% for interface in _data_.interfaces %}
{% set helpers = ["10.229.19.28", "10.229.20.28"] %}
interface {{ interface.interface }}
{% for helper in helpers %}
 ip helper-address {{ helper }}
{% endfor %}
!
{% endfor %}
</output>

<output
name="out_tabulate"
headers="hostname, interface, vrf, ip, mask, helpers, description"
returner="terminal"
format="tabulate"
format_attributes = "tablefmt='jira'"
path="interfaces"
/>
"""

test138="""
<template>
<!--test csv and tabulate outputters-->
<input name="test1" load="text" groups="interfaces.trunks, interfaces2.trunks2">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
 description some description
!
interface GigabitEthernet3/4
 switchport trunk allowed vlan add 100-105
!
interface GigabitEthernet3/5
 switchport trunk allowed vlan add 459,531,704-707
 ip address 1.1.1.1 255.255.255.255
 vrf forwarding ABC_VRF
!
</input>

<input name="test1_1" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/7
 switchport trunk allowed vlan add 138,166-173 
 description some description
!
interface GigabitEthernet3/8
 switchport trunk allowed vlan add 100-105
!
interface GigabitEthernet3/9
 switchport trunk allowed vlan add 459,531,704-707
 ip address 1.1.1.1 255.255.255.255
 vrf forwarding ABC_VRF
!
</input>

<!--group for global outputs:-->
<group name="interfaces.trunks">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 vrf forwarding {{ vrf }}
 ip address {{ ip }} {{ mask }}
!{{ _end_ }}
</group>

<!--global outputs:-->
<out
name="out_csv"
path="interfaces.trunks"
format="csv"
returner="terminal"
sep=","
missing="undefined"
load="python"
/>

<out
name="out_tabulate"
path="interfaces.trunks"
format="tabulate"
returner="terminal"
headers="interface, vrf, ip, mask, description"
format_attributes = "tablefmt='fancy_grid'"
/>


<out
name="out_table"
path="interfaces.trunks"
format="table"
returner="terminal"
headers="interface, vrf, ip, mask, description"
/>

<!--group with group specific outputs:-->
<group name="interfaces2.trunks2" output="out_tabulate2, out_csv2">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 vrf forwarding {{ vrf }}
 ip address {{ ip }} {{ mask }}
!{{ _end_ }}
</group>

<!--group specific outputs:-->
<out
name="out_csv2"
path="interfaces2.trunks2"
format="csv"
returner="terminal"
sep=","
missing="undefined"
load="python"
/>

<out
name="out_tabulate2"
path="interfaces2.trunks2"
format="tabulate"
returner="terminal"
/>
</template>
"""

test139="""
<input 
name="test7" 
load="text" 
>
interface GigabitEthernet3/4
 switchport mode access 
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport nonegotiate
!
interface GigabitEthernet3/7
 switchport mode access 
 switchport mode trunk
 switchport nonegotiate
!
</input>

<group name="interfaces" input="test7" output="test7">
interface {{ interface }}
 switchport mode access {{ mode_access | set("True") }}
 switchport trunk encapsulation dot1q {{ encap | set("dot1q") }}
 switchport mode trunk {{ mode | set("Trunk") }} {{ vlans | set("all_vlans") }}
 shutdown {{ disabled | set("True") }}
!{{ _end_ }}
</group>

<output name="test7"
description="test dynamic path"
returner="terminal"
format="raw"
>
</output>
"""


test140="""
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

<input name="test2" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/6
 switchport trunk allowed vlan add 138,166-173 
!
interface GigabitEthernet3/7
 switchport trunk allowed vlan add 100-105
!
interface GigabitEthernet3/8
 switchport trunk allowed vlan add 459,531,704-707
</input>

<group name="interfaces.trunks">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
</group>

<output 
format="json"
returner="terminal"
/>
"""

test141="""
<group name="facts.os_version">
Cisco IOS XE Software, Version {{ os_version }}
<group name="uptime">
{{ ignore }} uptime is {{ weeks | DIGIT }} weeks, {{ days | DIGIT }} days, {{ minutes | DIGIT }} minutes
</group>
System image file is {{ system_file | strip('"') }}
Last reload reason: {{ last_reload_reason | ORPHRASE }}
License Level: {{ license_level }}
License Type: {{ license_type | ORPHRASE }}
Next reload license Level: {{ next_reload_license_level}}
Smart Licensing Status: {{ smart_licencing | ORPHRASE }}
{{ GE_intfs_count }} Gigabit Ethernet interfaces
{{ non_volatile_mem_Kbytes | DIGIT }} bytes of non-volatile configuration memory.
{{ RAM_Kbytes | DIGIT }} bytes of physical memory.
{{ bootflash_mem_Kbytes | DIGIT }} bytes of virtual hard disk at bootflash:.
Configuration register is {{ config_register }}
</group>
"""

test142="""
<group name="platform">
cisco {{ platform }} ({{ ignore }}) processor (revision {{ ignore }}) with {{ ignore }} bytes of memory.
</group>
"""

test143="""
<vars load="ini" name="vars">
[my_vars]
hostname=gethostname
abc=xyz
</vars>

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

<output 
format="json"
returner="terminal"
/>
"""

test144="""
<input name="test1" load="text" groups="interfaces2.trunks2">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
 description some description
!
interface GigabitEthernet3/4
 switchport trunk allowed vlan add 100-105
!
interface GigabitEthernet3/5
 switchport trunk allowed vlan add 459,531,704-707
 ip address 1.1.1.1 255.255.255.255
 vrf forwarding ABC_VRF
!
</input>

<group name="interfaces2.trunks2" output="out_csv2, test_csv_is_equal">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 vrf forwarding {{ vrf }}
 ip address {{ ip }} {{ mask }}
!{{ _end_ }}
</group>

<!--group specific outputs:-->
<out
name="out_csv2"
path="interfaces2.trunks2"
format="csv"
sep=","
missing="undefined"
/>

<out 
name="test_csv_is_equal"
load="text"
returner="terminal"
functions="is_equal"
description="test csv outputter"
>description,interface,ip,mask,trunk_vlans,vrf
some description,GigabitEthernet3/3,undefined,undefined,138,166-173,undefined
undefined,GigabitEthernet3/4,undefined,undefined,100-105,undefined
undefined,GigabitEthernet3/5,1.1.1.1,255.255.255.255,459,531,704-707,ABC_VRF</out>
"""

test145="""
<input load="text">
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
!
</input>

<group name="interfaces*.{{ interface }}">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
</group>
"""

test146="""
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
!{{_end_}}
"""

test147="""
<input load="text">
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
!
</input>

<group>
interface {{ interface }}
  description {{ description }}
<group name = "ips">
  ip address {{ ip }}/{{ mask }}
</group>
  vrf {{ vrf }}
!{{_end_}}
</group>
"""

test148 = """
<group name="interfaces.cool_{{ interface }}_interface_{{ interface }}">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
</group>
"""

test149="""
<input load="text">
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
!
</input>

<group>
interface {{ interface }}
  description {{ description }}
<group>
  ip address {{ ip }}/{{ mask }}
</group>
  vrf {{ vrf }}
!{{_end_}}
</group>
"""


test150="""
<input load="text">
interface Vlan777
  description Management
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan778
  description Management
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan779
  ip address 192.168.0.1/24
  vrf MGMT
!
</input>

<vars>
my_var = "L2VC"
</vars>

<group default="None">
interface {{ interface }}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
  {{ interface_role | let("Uplink") }}
  {{ provider | let("my_var") }}
!{{_end_}}
</group>
"""

test151="""
<input load="text">
NAME: "Chassis", DESCR: "Cisco ISR4331 Chassis"
PID: ISR4331/K9        , VID: V04, SN: FDO2126A1JS

NAME: "Power Supply Module 0", DESCR: "250W AC Power Supply for Cisco ISR 4330"
PID: PWR-4330-AC       , VID: V02, SN: PST2122N02Q

NAME: "Fan Tray", DESCR: "Cisco ISR4330 Fan Assembly"
PID: ACS-4330-FANASSY  , VID:    , SN:            

</input>

<group name="inventory" default="Undefined">
NAME: "{{ item_name | ORPHRASE }}", DESCR: "{{ description | ORPHRASE }}"
PID: {{ part_id }}       , VID:{{ ignore("[\S ]+?") }}, SN: {{ serial }}
## PID: {{ part_id }}       , VID: {{ ignore }}, SN: {{ serial }}
## PID: {{ part_id }}       , VID:               , SN: {{ serial }}
PID: {{ part_id }}       , VID:               , SN:
PID:                     , VID:               , SN: {{ serial }}
</group>
"""

test152="""
<input load="text">
-------------------------
Device ID: switch-2.lab.com
Interface: GigabitEthernet4/6,  Port ID (outgoing port): GigabitEthernet1/5

-------------------------
Device ID: switch-1.lab.com
Interface: GigabitEthernet1/1,  Port ID (outgoing port): GigabitEthernet0/1
</input>

<g name="cdp">
Device ID: {{ peer_hostname | split('.') | item(0) }} 
Interface: {{ Interface | item(-40) }},  Port ID (outgoing port): {{ peer_interface | item(40) }}
</g>
"""


test153="""
<input load="text">
interface Vlan777
  description Management
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan778
  description Management
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan779
  ip address 192.168.0.1/24
  vrf MGMT
!
</input>

<macro>
def check(data):
    if data == "Vlan779":
        return data + "1000"
</macro>

<macro>
def check2(data):
    if "778" in data:
        return {"data": data, "key_vlan": True, "field2": 5678}
</macro>

<group default="None">
interface {{ interface | macro("check") | macro("check2")}}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
!{{_end_}}
</group>
"""

test154="""
<input load="text">
VRF NPGMPLS (VRF Id = 4); default RD 12345:24;
  Old CLI format, supports IPv4 only
  Flags: 0xC
  Interfaces:
    Te0/3/0.401              Te0/3/0.302              Te0/3/0.315             
    Te0/3/0.316              Te0/3/0.327              Te0/3/0.371             
    Te0/3/0.373              Te0/3/0.15               Te0/3/0.551             
    Te0/3/0.552              Te0/3/0.2527             Te0/3/0.711             
    Te0/3/0.500              Te0/3/0.325              Te0/3/0.324   
    Te0/3/0.32787 
Address family ipv4 unicast (Table ID = 0x4):
  Flags: 0x0
  Export VPN route-target communities
    RT:12345:24              
  Import VPN route-target communities
    RT:12345:24               RT:12345:7544             RT:9942:17
    RT:9942:31546            RT:12345:89900            RT:12345:650
    RT:12345:89564            RT:12345:89611           
  No import route-map
  No global export route-map
  No export route-map
  Route limit 4000, warning limit 80% (3200), current count 1609
  VRF label distribution protocol: not configured
  VRF label allocation mode: per-prefix
</input>
<group name="vrf.{{ vrf_name }}"> 
VRF {{ vrf_name }} (VRF Id = {{ vrf_id}}); default RD {{ vrf_rd }};
<group name="interfaces">
  Interfaces: {{ _start_ }}
    {{ interfaces | joinmatches(",") | ROW | resub(" +", ",", 5) | split(',') }}
    {{ interfaces | joinmatches(",") | split(',') }}
</group>
<group name="afis.{{ afi }}">
Address family {{ afi }} unicast (Table ID = {{ ignore }}):
<group name="export_rt">
  Export VPN route-target communities {{ _start_ }}
    {{ export_rt | joinmatches(",") | ROW | resub(" +", ",", 5) | split(',') }}
    {{ export_rt | joinmatches(",") | split(',') }}
</group>
<group name="import_rt">
  Import VPN route-target communities {{ _start_ }}
    {{ import_rt | joinmatches(",") | ROW | resub(" +", ",", 5) | split(',') }}
    {{ import_rt | joinmatches(",") | split(',') }}
</group>
  Import route-map: {{ import_route_map | default(None) }}
  Export route-map: {{ export_route_map | default(None) }}
  Route limit {{ route_limit }}, warning limit {{ route_limit_warning }}% (3200), current count {{ routes_count }}
  VRF label distribution protocol: {{ label_dist_proto | ORPHRASE }}
  VRF label allocation mode: {{ label_alloc_mode }}
</group>
</group>
"""

test155="""
<input load="text">
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
!
</input>

<group>
interface {{ interface }}
  description {{ description | append(" some append") }}
  ip address {{ ip | split('.') | append(777) | prepend(555) }}/{{ mask | prepend("mask - ") }}
  vrf {{ vrf }}
!{{_end_}}
</group>
"""


test156="""
<input load="text">
interface Loopback0
 description RID
 ip address 1.0.0.3 255.255.255.0
!
interface Vlan777
 description Management
 ip address 192.168.0.1 255.255.255.248
 vrf MGMT
!
interface Vlan778
 description Management
 ip address 192.168.0.2 24
 vrf MGMT
!
</input>

<group>
interface {{ interface }}
 description {{ description | append(" some append") }}
 ip address {{ ip | to_ip | is_private | to_str }} {{ mask | to_cidr | to_str }}
 vrf {{ vrf }}
!{{_end_}}
</group>
"""

test157="""
<input load="text">
interface Loopback0
 description RID
 ip address 1.0.0.3/255.255.255.0
!
interface Vlan777
 description Management
 ip address 192.168.0.3 255.255.255.248
 vrf MGMT
!
interface Vlan778
 description Management
 ip address 192.168.0.0/24
 vrf MGMT
!
interface Vlan779
 description Management
 ip address 192.168.0.1 24
 vrf MGMT
!
</input>

<group>
interface {{ interface }}
 description {{ description | append(" some append") }}
 ip address {{ ip | ORPHRASE | to_ip | is_private | to_str }}
 vrf {{ vrf }}
!{{_end_}}
</group>
"""



test158="""
<input load="text">
interface Loopback0
 description RID
 ip address 1.0.0.3 255.255.255.0
!
interface Vlan777
 description Management
 ip address fe::80 255.255.255.248
 vrf MGMT
!
</input>

<group>
interface {{ interface }}
 description {{ description | append(" some append") }}
 ip address {{ ip  | ip_info }} {{ mask | to_cidr }}
 vrf {{ vrf }}
!{{_end_}}
</group>
"""


test159="""
<input load="text">
interface Loopback0
 description RID
 ip address 1.0.0.3/24
!
interface Vlan777
 description Management
 ip address 192.168.0.3 255.255.255.248
 vrf MGMT
!
interface Vlan777
 description Management
 ip address fe::98/64
 vrf MGMT
!
</input>

<group>
interface {{ interface }}
 description {{ description | append(" some append") }}
 ip address {{ ip | ORPHRASE | to_ip | ip_info }}
 vrf {{ vrf }}
!{{_end_}}
</group>
"""



test160="""
<input load="text">
interface Loopback0
 description RID
 ip address 1.0.0.3/24
!
interface Vlan777
 description Management
 ip address 192.168.0.3 255.255.255.248
 vrf MGMT
!
interface Vlan777
 description Management
 ip address fe::98/64
 vrf MGMT
!
</input>

<group>
interface {{ interface }}
 description {{ description | append(" some append") }}
 ip address {{ ip | ORPHRASE | cidr_match("192.168.0.0/16") }} {{ mask }}
 vrf {{ vrf }}
!{{_end_}}
</group>
"""

test161="""
<input load="text">
interface Vlan777
  description Management
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan778
  description Management
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan779
  ip address 192.168.0.1/24
  vrf MGMT
!
</input>

<macro>
def check(data):
    if data == "Vlan779":
        return data + "1000"
</macro>

<macro>
def check2(data):
    if "778" in data:
        return data, {"key_vlan": True, "field2": 5678}
</macro>

<group default="None">
interface {{ interface | macro("check") | macro("check2")}}
  description {{ description }}
  ip address {{ ip }}/{{ mask }}
  vrf {{ vrf }}
!{{_end_}}
</group>
"""


test162="""
<input load="text">
interface Vlan777
  description Management
  switchport trunk allowed vlans none
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan778
  description Management
  switchport trunk allowed vlans 23,24,37
  ip address 192.168.0.1/24
  vrf MGMT
!
</input>

<group name="vlans_trunk">
interface {{ interface }}
  description {{ description }}
  switchport trunk allowed vlans {{ trunk_vlans | notequal("none") | default([]) | split(",") }}
  vrf {{ vrf }}
!{{_end_}} 
</group>
"""


test163="""
<input load="text">
interface Vlan777
  description Management
  switchport trunk allowed vlans none
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan778
  description Management
  switchport trunk allowed vlans 23,24,37
  ip address 192.168.0.1/24
  vrf MGMT
!
</input>

<group name="vlans_trunk">
interface {{ interface }}
  description {{ description }}
  switchport trunk allowed vlans {{ trunk_vlans | notequal("none")| split(",") }}
  switchport trunk allowed vlans none {{ trunk_vlans | set([]) }}
  vrf {{ vrf }}
!{{_end_}} 
</group>
"""


test164="""
<input load="text">
interface Vlan777
  description Management
  switchport trunk allowed vlans none
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan778
  description Management
  switchport trunk allowed vlans 23,24,37
  ip address 192.168.0.1/24
  vrf MGMT
!
</input>

<macro>
def empty_list_if_none(data):
    if data == "none":
        return []
    else:
        return data
</macro>

<group name="vlans_trunk">
interface {{ interface }}
  description {{ description }}
  switchport trunk allowed vlans {{ trunk_vlans | macro("empty_list_if_none") | split(",") }}
  vrf {{ vrf }}
!{{_end_}} 
</group>
"""


test165="""
<input load="text">
interface Vlan777 bla
  description Management
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan778 somebla
  description Management
  switchport trunk allowed vlans 23,24,37   bla2, bla2, bla2
  ip address 192.168.0.1/24
  vrf MGMT
!
</input>

<group name="vlans_trunk">
interface {{ interface }} {{ ignore("WORD") }}
  description {{ description }}
  switchport trunk allowed vlans {{ trunk_vlans | split(",") }}   {{ ignore("ORPHRASE") }}
  vrf {{ vrf }}
!{{_end_}} 
</group>
"""


test166="""
<input load="text">
interface Vlan777
  description Management
  ip address 192.168.0.1/24
  vrf MGMT
!
interface Vlan778
  description Management
  switchport mode trunk
  switchport trunk allowed vlans 23,24,37
  ip address 192.168.0.1/24
  vrf MGMT
!
</input>

<vars>
my_var = "L2VC"
</vars>

<group name="vlans_trunk">
interface {{ interface }}
  description {{ description }}
  switchport mode trunk {{ mode | set("trunk") }} {{ vlans_trunk | set("1-4096") }}
  switchport trunk allowed vlans {{ trunk_vlans | split(",") }}
  vrf {{ vrf }}
  {{ var1 | set("my_value1") }}
{{ var2 | set("my_value2") }}
{{ var3 | set("my_value3") }} {{ var4 | set("my_value4") }}
{{ var5 | set("my_var") }}
!{{_end_}} 
</group>
"""


test167="""
<input load="text">
interface Vlan777
  description Management-1
  switchport mode trunk
!
interface Vlan778
  description Management-2
  switchport mode trunk
  switchport trunk allowed vlans 23,24,37
!
</input>

<macro>
def check_trunk_vlans(data):
    if data.get("mode", None):
        if data["mode"] is "trunk":
            if "trunk_vlans" not in data:
                data["trunk_vlans"] = "all"
    return data
</macro>

<group name="vlans_trunk" macro="check_trunk_vlans">
interface {{ interface }}
  description {{ description }}
  switchport mode trunk {{ mode | set("trunk") }}
  switchport trunk allowed vlans {{ trunk_vlans | split(",") }}
  vrf {{ vrf }}
!{{_end_}} 
</group>
"""


test168="""
<input load="text">
interface Vlan123
 description Desks vlan
 ip address 192.168.123.1 255.255.255.0
!
interface GigabitEthernet1/1
 description to core-1
!
interface Vlan222
 description Phones vlan
 ip address 192.168.222.1 255.255.255.0
!
interface Loopback0
 description Routing ID loopback
!
</input>

 <macro>
def check_if_svi(data):
    if "Vlan" in data:
        return data, {"is_svi": True}
    else:
       return data, {"is_svi": False}
        
def check_if_loop(data):
    if "Loopback" in data:
        return data, {"is_loop": True}
    else:
       return data, {"is_loop": False}
 </macro>
 
 <macro>
def description_mod(data):
    # To revert words order in descripotion
    words_list = data.split(" ")
    words_list_reversed = list(reversed(words_list))
    words_reversed = " ".join(words_list_reversed) 
    return words_reversed
 </macro>
 
<group name="interfaces_macro">
interface {{ interface | macro("check_if_svi") | macro("check_if_loop") }}
 description {{ description | ORPHRASE | macro("description_mod")}}
 ip address {{ ip }} {{ mask }}
</group>
"""

test169="""
<input load="text">
interface Vlan123
 ip address 192.168.123.1 255.255.255.0
!
interface Loopback0
 description Routing ID loopback
!
</input>
 
 <macro>
def description_mod(data):
    # To revert words order in descripotion
    words_list = data.get("description", "").split(" ")
    words_list_reversed = list(reversed(words_list))
    words_reversed = " ".join(words_list_reversed) 
    data["description"] = words_reversed
    return data
 </macro>
 
<group name="interfaces_macro" macro="description_mod">
interface {{ interface }}
 description {{ description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
"""


test170="""
<input load="text">
interface GigabitEthernet1/1
 description to core-1
!
interface Vlan222
 description Phones vlan
!
interface Loopback0
 description Routing ID loopback
!
</input>

 <macro>
def check_if_svi(data):
    if "Vlan" in data["interface"]:
        data["is_svi"] = True
    else:
        data["is_svi"] = False
    return data
        
def check_if_loop(data):
    if "Loopback" in data["interface"]:
        data["is_loop"] = True
    else:
        data["is_loop"] = False
    return data
 </macro>
 
 <macro>
def description_mod(data):
    # To revert words order in descripotion
    words_list = data.get("description", "").split(" ")
    words_list_reversed = list(reversed(words_list))
    words_reversed = " ".join(words_list_reversed) 
    data["description"] = words_reversed
    return data
 </macro>
 
<group name="interfaces_macro" macro="description_mod, check_if_svi, check_if_loop">
interface {{ interface }}
 description {{ description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
"""


test171="""
<input load="text">
interface Vlan123
 ip address 192.168.123.1 255.255.255.0
!
interface GigabitEthernet1/1
 description to core-1
!
interface Vlan222
 description Phones vlan
!
interface Loopback0
 description Routing ID loopback
!
</input>

<lookup name="AUX" load="ini">
[interfaces]
Vlan222 : add value to result
</lookup>

<group name="interfaces">
interface {{ interface | rlookup("AUX.interfaces", "looked_up_data")}}
 description {{ description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
"""


test172="""
<input load="text">
interface GigabitEthernet1/1
 description to core-1
 ip address 192.168.123.1 255.255.255.0
!
interface Vlan222
 description Phones vlan
!
interface Loopback0
 description Routing ID loopback
 ip address 192.168.222.1 255.255.255.0
!
</input>

 <macro>
def check_if_svi(data):
    if "Vlan" in data["interface"]:
        data["is_svi"] = True
    else:
        data["is_svi"] = False
    return data
        
def check_if_loop(data):
    if "Loopback" in data["interface"]:
        data["is_loop"] = True
    else:
        data["is_loop"] = False
    return data
 </macro>
 
 <macro>
def description_mod(data):
    # To revert words order in descripotion
    words_list = data.get("description", "").split(" ")
    words_list_reversed = list(reversed(words_list))
    words_reversed = " ".join(words_list_reversed) 
    data["description"] = words_reversed
    return data
 </macro>
 
<group name="interfaces_macro" functions="contains('ip') | macro('description_mod') | macro('check_if_svi') | macro('check_if_loop')">
interface {{ interface }}
 description {{ description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
"""

test173="""
<input load="text">
interface GigabitEthernet1/1
 ip address 192.168.123.1 255.255.255.0
!
</input>

<!--Python formatted variables data-->
<vars name="vars">
python_data = ['.lab.local', '.static.on.net', '.abc']
</vars>

<!--YAML formatted variables data-->
<vars load="yaml" name="vars">
yaml_data:
  - '.lab.local'
  - '.static.on.net'
  - '.abc'
</vars>

<!--Json formatted variables data-->
<vars load="json" name="vars">
{
    "json_data": [
        ".lab.local",
        ".static.on.net",
        ".abc"
    ]
}
</vars>

<!--INI formatted variables data-->
<variables load="ini" name="vars">
[ini_data]
1: '.lab.local'
2: '.static.on.net'
3: '.abc'
</variables>

<!--CSV formatted variables data-->
<variables load="csv" name="vars.csv_data">
id, domain
1,  .lab.local
2,  .static.on.net
3,  .abc
</variables>

<group name="interfaces">
interface {{ interface }}
 ip address {{ ip }} {{ mask }}	
</group>
"""


test174="""
<input load="text">
interface Loopback0
 ip address 1.0.0.3 255.255.255.0
!
interface Vlan777
 ip address 192.168.0.1/24
!
</input>

<group name="interfaces_ip_test1_19">
interface {{ interface }}
 ip address {{ ip | PHRASE | to_ip | with_prefixlen }}
 ip address {{ ip | to_ip | with_netmask }}
</group>
"""


test175="""
<input load="text">
RP/0/0/CPU0:XR4#show route
i L2 10.0.0.2/32 [115/20] via 10.0.0.2, 00:41:40, tunnel-te100
i L2 172.16.0.3/32 [115/10] via 10.1.34.3, 00:45:11, GigabitEthernet0/0/0/0.34
i L2 1.1.23.0/24 [115/20] via 10.1.34.3, 00:45:11, GigabitEthernet0/0/0/0.34
</input>

<group name="routes">
{{ code }} {{ subcode }} {{ net | to_net | is_private | to_str }} [{{ ad }}/{{ metric }}] via {{ nh_ip }}, {{ age }}, {{ nh_interface }}
</group>
"""

test176="""
<input load="text">
interface Loopback0
 ip address 1.0.0.3 255.255.255.0
!
interface Vlan777
 ip address 192.168.0.1/24
!
interface Vlan777
 ip address fe80::fd37/124
!
</input>

<group name="interfaces">
interface {{ interface }}
 ip address {{ ip | to_ip | ip_info }} {{ mask }}
 ip address {{ ip | to_ip | ip_info }}
</group>
"""


test176="""
<input load="text">
interface Loopback0
 ip address 192.168.0.113/24
!
interface Loopback1
 ip address 192.168.1.113/24
!
interface Vlan777
 ip address 2001::fd37/124
!
interface Vlan778
 ip address 2002::fd37/124
!
</input>

<group name="interfaces">
interface {{ interface }}
 ip address {{ ip | to_ip | ip_info }} {{ mask }}
 ip address {{ ip | to_ip | ip_info }}
</group>
"""


test177="""
<input load="text">
interface Loopback0
 ip address 192.168.0.113/24
!
interface Loopback1
 ip address 192.168.1.341/24
!
</input>

<group name="interfaces">
interface {{ interface }}
 ip address {{ ip | is_ip }}
</group>
"""


test178="""
<input load="text">
interface Loopback0
 ip address 192.168.0.113/24
!
interface Loopback1
 ip address 192.168.1.341/24
!
interface Loopback1
 ip address 10.0.1.251/24
!
</input>

<group name="interfaces">
interface {{ interface }}
 ip address {{ ip | cidr_match("192.168.0.0/16") }}
</group>
"""


test179="""
<template base_path="C:/Users/Denis/YandexDisk/Python/NPG/Text Template Parser/ttp/!USECASES/!GitHub">
<input name="dataset-1" load="yaml" groups="interfaces1">
url: "/Data/Inputs/data-1/"
extensions: ["txt"]
</input>

<input name="dataset-2" load="python" groups="interfaces2">
url = ["/Data/Inputs/data-2/"]
filters = ["sw\-\d.*"]
</input>

<group name="interfaces1">
interface {{ interface }}
 switchport access vlan {{ access_vlan }}
</group>

<group name="interfaces2">
interface {{ interface }}
  ip address {{ ip  }}/{{ mask }}
</group>
</template>
"""


test180="""
<vars name="vars.info**.{{ hostname }}">
# path will be formaed dynamically
hostname='switch-1'
serial='AS4FCVG456'
model='WS-3560-PS'
</vars>

<vars name="vars.ip*">
# variables that will be saved under {'vars': {'ip': []}} path
IP="Undefined"
MASK="255.255.255.255"
</vars>

<vars load="yaml">
# set of vars that will not be included in results
intf_mode: "l3"
</vars>

<input load="text">
interface Vlan777
 description Management
 ip address 192.168.0.1 24
 vrf MGMT
!
</input>

<group name="interfaces">
interface {{ interface }}
 description {{ description }}
 ip address {{ ip | record("IP") }} {{ mask }}
 vrf {{ vrf }}
 {{ mode | set("intf_mode") }}
</group>
"""


test181="""
<input load="text">
interface Loopback0
 description Management
 ip address 192.168.0.113/24
!
</input>

<group name="interfaces">
interface {{ interface }}
 description {{ description | let("description_undefined") }}
 ip address {{ ip | contains("24") | let("netmask", "255.255.255.0") }}
</group>
"""


test182="""
<input load="text">
router bgp 65100
  neighbor 10.145.1.9
    description vic-mel-core1
  !
  neighbor 192.168.101.1
    description qld-bri-core1
</input>

<lookup name="locations" load="ini">
[cities]
-mel- : 7 Name St, Suburb A, Melbourne, Postal Code
-bri- : 8 Name St, Suburb B, Brisbane, Postal Code
</lookup>

<group name="bgp_config">
router bgp {{ bgp_as }}
 <group name="peers">
  neighbor {{ peer }}
    description {{ description | rlookup('locations.cities', add_field='location') }}
 </group>
</group> 
"""

test183="""
<lookup 
name="aux_csv" 
load="csv" 
>
ASN,as_name,as_description,prefix_num
65100,Subs,Private ASN,734
</lookup>

<input load="text">
router bgp 65100
</input>

<group name="bgp_config">
router bgp {{ bgp_as | lookup("aux_csv", add_field="as_details") }}
</group> 
"""

test184="""
<lookup name="yaml_look" load="yaml">
'65100':
  as_description: Private ASN
  as_name: Subs
  prefix_num: '734'
'65101':
  as_description: Cust-1 ASN
  as_name: Cust1
  prefix_num: '156'
</lookup>

<input load="text">
router bgp 65100
</input>

<group name="bgp_config">
router bgp {{ bgp_as | lookup("yaml_look", add_field="as_details") }}
</group> 
"""

test185="""
<input load="text">
interface Vlan163
 description [OOB management]
 ip address 10.0.10.3 255.255.255.0
!
interface GigabitEthernet6/41
 description [uplink to core]
 ip address 192.168.10.3 255.255.255.0
</input>

<group name="interfaces">
interface {{ interface }}
 description {{ description | PHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
"""

test186="""
<input load="text">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
 switchport trunk allowed vlan add 400,401,410
</input>

<vars>
vlans = [
   "unrange(rangechar='-', joinchar=',')",
   "split(',')",
   "join(':')",
   "joinmatches(':')"
]
</vars>

<group name="interfaces">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans | chain('vlans') }}
</group>
"""

test187="""
<input load="text">
interface Vlan163
 description [OOB management]
 ip address 10.0.10.3 255.255.255.0
!
interface GigabitEthernet6/41
 description [uplink to core]
 ip address 192.168.10.3 255.255.255.0
</input>

<input load="text">
interface Vlan164
 description [OOB management]
 ip address 10.0.11.3 255.255.255.0
!
interface GigabitEthernet6/42
 description [uplink to core]
 ip address 192.168.11.3 255.255.255.0
</input>

<group name="interfaces">
interface {{ interface }}
 description {{ description | PHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
"""

test188="""
<input load="text">
interface Vlan163
 description [OOB management]
 ip address 10.0.10.3 255.255.255.0
!
interface GigabitEthernet6/41
 description [uplink to core]
 ip address 192.168.10.3 255.255.255.0
</input>

<input load="text">
interface Vlan164
 description [OOB management]
 ip address 10.0.11.3 255.255.255.0
!
interface GigabitEthernet6/42
 description [uplink to core]
 ip address 192.168.11.3 255.255.255.0
</input>

<group>
interface {{ interface }}
 description {{ description | PHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
"""


test189="""
<template results="per_template">
<input load="text">
interface Vlan163
 description [OOB management]
 ip address 10.0.10.3 255.255.255.0
!
interface GigabitEthernet6/41
 description [uplink to core]
 ip address 192.168.10.3 255.255.255.0
</input>

<input load="text">
interface Vlan164
 description [OOB management]
 ip address 10.0.11.3 255.255.255.0
!
interface GigabitEthernet6/42
 description [uplink to core]
 ip address 192.168.11.3 255.255.255.0
</input>

<group name="interfaces">
interface {{ interface }}
 description {{ description | PHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
</template>
"""

test190="""
<template results="per_template">

<input load="text">
switch1-1#show run interfaces
interface Vlan163
 description [OOB management-1]
 ip address 10.0.10.3 255.255.255.0
!
interface GigabitEthernet6/41
 description [uplink to core-1]
 ip address 192.168.10.3 255.255.255.0
</input>

<input load="text">
switch1-2#show run interfaces
interface Vlan164
 description [OOB management-2]
 ip address 10.0.11.3 255.255.255.0
!
interface GigabitEthernet6/42
 description [uplink to core-2]
 ip address 192.168.11.3 255.255.255.0
</input>

<vars>
hostname="gethostname"
</vars>

<group>
interface {{ interface }}
 description {{ description | PHRASE }}
 ip address {{ ip }} {{ mask }}
 {{ hostname | set("hostname") }}
</group>
</template>
"""


test191="""
<template results="per_template">

<vars>
hostname="gethostname"
</vars>

<group name="interfaces.{{ interface }}**" contains="ip">
interface {{ interface }}
 description {{ description | PHRASE }}
 ip address {{ ip }} {{ mask }}
 {{ hostname | set("hostname") }}
</group>

</template>
"""

test192="""
<template results="per_input">

<vars>
hostname="gethostname"
</vars>

<group name="interfaces.{{ interface }}" contains="ip">
interface {{ interface }}
 description {{ description | PHRASE }}
 ip address {{ ip }} {{ mask }}
 {{ hostname | set("hostname") }}
</group>

</template>
"""


ip_cfg_template_per_tmplt = """
<template results="per_template">

<vars>
hostname = "gethostname"
IfsNormalize = {
    'Lo': ['^Loopback'], 
    'Ge':['^GigabitEthernet'], 
    'Po': ['^port-channel', '^Port-channel', '^Bundle-Ether', '^Eth-Trunk'], 
    'Te':['^TenGigabitEthernet', '^TenGe', '^10GE', '^TenGigE', '^XGigabitEthernet'], 
    'Fa':['^FastEthernet'], 
    'Eth':['^Ethernet'], 
    'Pt':['^Port[^-]'], 
    'Vl':['^Vlan'], 
    '100G':['^HundredGigE']
} 
</vars>

<macro>
def add_network(data):
    # macro to return ip string as data and additional
    # netmask and network fields
    ret = {
        "netmask" : str(data.netmask),
        "network" : str(data.network)    
    }
    return str(data.ip), ret
</macro>

<!--################-=HUAWEI TEMPLATE GROUPS=-################-->
<group name="{{ network }}*" contains="ip" input="./Huawei/">
interface {{ interface | resuball("IfsNormalize") }}
 description {{ port_description }}
 ip binding vpn-instance {{ vrf }}
 ip address {{ ip | PHRASE | strip(" sub") | exclude(':') | to_ip | macro("add_network") }}
 {{ hostname | set("hostname") }}
#{{ _end_ }}
</group>

<group name="{{ network }}*" contains="ip" input="./Huawei/">
interface {{ interface | resuball("IfsNormalize") }}
 description {{ port_description }}
 ip binding vpn-instance {{ vrf }}
 ipv6 address {{ ip | strip("sub") | contains(':') | to_ip | macro("add_network") }}
 {{ hostname | set("hostname") }}
#{{ _end_ }}
</group>

</template>
"""

ip_cfg_template_per_inpt = """
<template results="per_input">

<vars>
hostname = "gethostname"
IfsNormalize = {
    'Lo': ['^Loopback'], 
    'Ge':['^GigabitEthernet'], 
    'Po': ['^port-channel', '^Port-channel', '^Bundle-Ether', '^Eth-Trunk'], 
    'Te':['^TenGigabitEthernet', '^TenGe', '^10GE', '^TenGigE', '^XGigabitEthernet'], 
    'Fa':['^FastEthernet'], 
    'Eth':['^Ethernet'], 
    'Pt':['^Port[^-]'], 
    'Vl':['^Vlan'], 
    '100G':['^HundredGigE']
} 
</vars>

<macro>
def add_network(data):
    # macro to return ip string as data and additional
    # netmask and network fields
    ret = {
        "netmask" : str(data.netmask),
        "network" : str(data.network)    
    }
    return str(data.ip), ret
</macro>

<!--################-=HUAWEI TEMPLATE GROUPS=-################-->
<group name="{{ network }}*" contains="ip" input="./Huawei/">
interface {{ interface | resuball("IfsNormalize") }}
 description {{ port_description }}
 ip binding vpn-instance {{ vrf }}
 ip address {{ ip | PHRASE | strip(" sub") | exclude(':') | to_ip | macro("add_network") }}
 {{ hostname | set("hostname") }}
#{{ _end_ }}
</group>

<group name="{{ network }}*" contains="ip" input="./Huawei/">
interface {{ interface | resuball("IfsNormalize") }}
 description {{ port_description }}
 ip binding vpn-instance {{ vrf }}
 ipv6 address {{ ip | strip("sub") | contains(':') | to_ip | macro("add_network") }}
 {{ hostname | set("hostname") }}
#{{ _end_ }}
</group>

</template>
"""


test193="""
<template
name="template4"
description="template to test csv/tabulate global outputters"
>
<!--test csv and tabulate outputters-->
<input name="test4-1" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/3
 switchport trunk allowed vlan add 138,166-173 
 description some description
!
interface GigabitEthernet3/4
 switchport trunk allowed vlan add 100-105
!
interface GigabitEthernet3/5
 switchport trunk allowed vlan add 459,531,704-707
 ip address 1.1.1.1 255.255.255.255
 vrf forwarding ABC_VRF
!
interface GigabitEthernet3/7
 switchport trunk allowed vlan add 138,166-173 
 description some description
!
interface GigabitEthernet3/8
 switchport trunk allowed vlan add 100-105
!
interface GigabitEthernet3/9
 switchport trunk allowed vlan add 459,531,704-707
 ip address 1.1.1.1 255.255.255.255
 vrf forwarding ABC_VRF
!
</input>


<input name="test4-1.1" load="text">
interface GigabitEthernet3/33
 switchport trunk allowed vlan add 138,166-173 
 description some description
</input>

<group name="interfaces.trunks" input="test4-1.1">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 vrf forwarding {{ vrf }}
 ip address {{ ip }} {{ mask }}
!{{ _end_ }}
</group>


<!--group for global outputs:-->
<group name="interfaces.trunks">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 vrf forwarding {{ vrf }}
 ip address {{ ip }} {{ mask }}
!{{ _end_ }}
</group>

<!--global outputs:-->
<out
name="out_csv"
path="interfaces.trunks"
format="csv"
returner="self"
sep=","
missing="undefined"
load="python"
/>

<out 
name="test4-1"
load="text"
returner="self"
functions="is_equal"
description="test global csv outputter"
>description,interface,ip,mask,trunk_vlans,vrf
some description,GigabitEthernet3/3,undefined,undefined,138,166-173,undefined
undefined,GigabitEthernet3/4,undefined,undefined,100-105,undefined
undefined,GigabitEthernet3/5,1.1.1.1,255.255.255.255,459,531,704-707,ABC_VRF
some description,GigabitEthernet3/7,undefined,undefined,138,166-173,undefined
undefined,GigabitEthernet3/8,undefined,undefined,100-105,undefined
undefined,GigabitEthernet3/9,1.1.1.1,255.255.255.255,459,531,704-707,ABC_VRF</out>

<!--final output to put all results in tabulate table-->
<output 
returner="terminal"
format="tabulate"
format_attributes = "tablefmt='fancy_grid'"
/>
</template>
"""


test194="""
<input name="input_1" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/11
 description input_1_data
 switchport trunk allowed vlan add 111,222
!
</input>

<input name="input_2" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/22
 description input_2_data
 switchport trunk allowed vlan add 222,888
!
</input>

<input name="input_3" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/33
 description input_3_data
 switchport trunk allowed vlan add 333,999
!
</input>

<input name="input_4" load="text">
interface GigabitEthernet3/44
 description input_4_data
 switchport trunk allowed vlan add 444,1010
!
</input>

<input name="input_5" load="text">
interface GigabitEthernet3/55
 description input_5_data
 switchport trunk allowed vlan add 555,2020
!
</input>

<group name="interfaces.trunks" input="input_1">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_1") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks" input="input_2">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_2") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks" input="input_2">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_3") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_4") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks" input="input_5">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_5") }}
!{{ _end_ }}
</group>
"""


test195="""
<input name="input_1" load="text">
interface GigabitEthernet3/11
 description input_1_data
 switchport trunk allowed vlan add 111,222
!
</input>

<input name="input_2" load="text">
interface GigabitEthernet3/22
 description input_2_data
 switchport trunk allowed vlan add 222,888
!
</input>

<group name="interfaces.trunks" input="input_1">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_1") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks" input="input_2">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_2") }}
!{{ _end_ }}
</group>
"""

test196="""
<input load="text">
switch1# show run int
hostname switch12345
!
interface GigabitEthernet3/11
 description input_1_data
 switchport trunk allowed vlan add 111,222
!
</input>

<vars>
hostname_var = "gethostname"
</vars>

<group name="params">
hostname {{ hostname | record("hostname_var") }}
</group>

<group name="interfaces.trunks" input="input_2">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ hostname | set("hostname_var") }}
!{{ _end_ }}
</group>
"""

test197="""
<input load="text">
interface GigabitEthernet3/11
 description bbc.com
 switchport trunk allowed vlan add 111,222
!
</input>

<group name="interfaces_dnsv4_timeout_test">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | dns(record='A', servers='192.168.1.100') }}
!{{ _end_ }}
</group>

<group name="interfaces_dnsv4">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | dns }}
!{{ _end_ }}
</group>

<group name="interfaces_dnsv6">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | dns(record='AAAA') }}
!{{ _end_ }}
</group>

<group name="interfaces_dnsv4_google">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | dns(record='A', servers='8.8.8.8') }}
!{{ _end_ }}
</group>

<group name="interfaces_dnsv6_add_field">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | dns(record='AAAA', add_field='ips') }}
!{{ _end_ }}
</group>
"""

test198="""
<input load="text">
interface GigabitEthernet3/11
 ip address 8.8.8.8 255.255.255.255
!
</input>

<group name="interfaces_rdnsv4">
interface {{ interface }}
 ip address {{ ip | rdns }} {{ mask }}
!{{ _end_ }}
</group>

<group name="interfaces_rdnsv4_google_server">
interface {{ interface }}
 ip address {{ ip | rdns(servers='8.8.8.8') }} {{ mask }}
!{{ _end_ }}
</group>

<group name="interfaces_rdns_add_field">
interface {{ interface }}
 ip address {{ ip | rdns(add_field='FQDN') }} {{ mask }}
!{{ _end_ }}
</group>

<group name="interfaces_rdns_fail">
interface {{ interface }}
 ip address {{ ip | rdns(servers='192.168.1.100') }} {{ mask }}
!{{ _end_ }}
</group>
"""

test199="""
<input load="text">
interface GigabitEthernet3/11
 description wikipedia.org
!
</input>

<group name="interfaces">
interface {{ interface }}
 description {{ description | dns }}
!{{ _end_ }}
</group>

<group name="interfaces_dnsv6">
interface {{ interface }}
 description {{ description | dns(record='AAAA') }}
!{{ _end_ }}
</group>

<group name="interfaces_dnsv4_google_dns">
interface {{ interface }}
 description {{ description | dns(record='A', servers='8.8.8.8') }}
!{{ _end_ }}
</group>

<group name="interfaces_dnsv6_add_field">
interface {{ interface }}
 description {{ description | dns(record='AAAA', add_field='IPs') }}
!{{ _end_ }}
</group>
"""

test200="""
<input load="text">
interface Loopback0
 ip address 192.168.0.113/24
!
interface Vlan778
 ip address 2002::fd37/124
!
</input>

<group name="interfaces">
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
</group>

<output
name="test output 1"
load="json"
description="test results equality"
functions="is_equal"
>
[
    {
        "interfaces": [
            {
                "interface": "Loopback0",
                "ip": "192.168.0.113",
                "mask": "24"
            },
            {
                "interface": "Vlan778",
                "ip": "2002::fd37",
                "mask": "124"
            }
        ]
    }
]
</output>

<output
format="yaml"
returner="file"
url="C:/Users/Denis/YandexDisk/Python/NPG/Text Template Parser/ttp/!USECASES/!GitHub/Output/"
filename="OUT_%Y-%m-%d_%H-%M-%S_results.txt"
/>
"""


test201="""
<input load="text">
interface Loopback0
 ip address 192.168.0.113/24
!
interface Vlan778
 ip address 2002::fd37/124
!
</input>

<input load="text">
interface Loopback10
 ip address 192.168.0.10/24
!
interface Vlan710
 ip address 2002::fd10/124
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
</group>

<output
format="pprint"
returner="terminal"
/>

<output
format="table"
returner="terminal"
/>
"""


test202="""
<input load="text">
interface Loopback10
 ip address 192.168.0.10  subnet mask 24
!
interface Vlan710
 ip address 2002::fd10 subnet mask 124
!
</input>

<group name="interfaces_with_funcs" functions="to_ip('ip', 'mask')">
interface {{ interface }}
 ip address {{ ip }}  subnet mask {{ mask }}
</group>

<group name="interfaces_with_to_ip_args" to_ip = "'ip', 'mask'">
interface {{ interface }}
 ip address {{ ip }}  subnet mask {{ mask }}
</group>

<group name="interfaces_with_to_ip_kwargs" to_ip = "ip_key='ip', mask_key='mask'">
interface {{ interface }}
 ip address {{ ip }}  subnet mask {{ mask }}
</group>
"""

test203="""
<input load="text">
interface Loopback0
 ip address 192.168.0.113/24
!
interface Vlan778
 ip address 2002::fd37/124
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
</group>

<output format="csv" returner="terminal"/>
"""

test204="""
<input load="text">
interface Loopback0
 ip address 192.168.0.113/24
!
interface Vlan778
 ip address 2002::fd37/124
!
</input>

<input load="text">
interface Loopback10
 ip address 192.168.0.10/24
!
interface Vlan710
 ip address 2002::fd10/124
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
</group>

<output format="jinja2" returner="terminal">
{% for input_result in _data_ %}
{% for item in input_result %}
if_cfg id {{ item['interface'] }}
    ip address {{ item['ip'] }} 
    subnet mask {{ item['mask'] }}
#
{% endfor %}
{% endfor %}
</output>
"""

test205="""
<input load="text">
interface Loopback0
 ip address 192.168.0.113/24
!
interface Vlan778
 ip address 2002::fd37/124
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
</group>

<output format="tabulate" returner="terminal"/>
"""

test206="""
<input load="text">
router bgp 65100
  neighbor 10.145.1.9
    description vic-mel-core1
  !
  neighbor 192.168.101.1
    description qld-bri-core1
</input>

<group name="bgp_config">
router bgp {{ bgp_as }}
 <group name="peers">
  neighbor {{ peer }}
    description {{ description  }}
 </group>
</group> 

<output name="out1" format="pprint" returner="terminal"/>

<output name="out2"
path="bgp_config.peers"
format="csv"
returner="terminal"
/>
"""

test207="""
<input load="text">
router bgp 65100
  neighbor 10.145.1.9
    description vic-mel-core1
  !
  neighbor 192.168.101.1
    description qld-bri-core1
</input>

<group name="bgp_config">
router bgp {{ bgp_as }}
 <group name="peers">
  neighbor {{ peer }}
    description {{ description  }}
 </group>
</group> 

<output name="out2"
path="bgp_config.peers"
format="tabulate"
returner="terminal"
format_attributes="tablefmt='fancy_grid'"
/>
"""

test208="""
<input load="text">
interface Loopback0
 description Router-id-loopback
 ip address 192.168.0.113/24
!
interface Vlan778
 description CPE_Acces_Vlan
 ip address 2002::fd37/124
 ip vrf CPE1
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description }}
 ip vrf {{ vrf }}
</group>

<output 
format="tabulate" 
returner="terminal"
headers="interface, description, vrf, ip, mask"
/>
"""

test209="""
<input load="text">
interface Loopback0
 description Router-id-loopback
 ip address 192.168.0.113/24
!
interface Vlan778
 ip address 2002::fd37/124
 ip vrf CPE1
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description }}
 ip vrf {{ vrf }}
</group>

<output 
format="tabulate" 
returner="terminal"
missing="UNDEFINED"
/>
"""

test210="""
<input load="text">
router bgp 65100
  neighbor 10.145.1.9
    description vic-mel-core1
  !
  neighbor 192.168.101.1
    description qld-bri-core1
</input>

<group name="bgp_config">
router bgp {{ bgp_as }}
 <group name="peers">
  neighbor {{ peer }}
    description {{ description  }}
 </group>
</group> 

<output returner="terminal" format="pprint"/>

<output name="out2"
path="bgp_config"
format="tabulate"
returner="terminal"
format_attributes="tablefmt='fancy_grid'"
/>
"""

test211="""
<input load="text">
interface Loopback0
 description Router-id-loopback
 ip address 192.168.0.113/24
!
interface Vlan778
 ip address 2002::fd37/124
 ip vrf CPE1
!
</input>

<group name="{{ interface }}">
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description | contains('-') }}
 ip vrf {{ vrf }}
</group>

<output 
format="tabulate" 
returner="terminal"
key="intf_name"
/>
"""

test212="""
<input name="jun_hierarch" load="text">
## Juniper show configuration interfaces output
some.user@router-fw-host> show configuration interfaces
vlan {
    description "intf descript bla";
    unit 0 {
        family inet {
            address 192.168.1.1/24;
        }
    }
}
lo0 {
    unit 0 {
        description "Routing Loopback";
        family inet {
            address 10.0.0.254/32 {
                primary;
            }
            address 10.11.37.254/32;
        }
    }
}
</input>


<vars name="vars">
hostname = "gethostname"
</vars>

<group name="interfaces" input="jun_hierarch">
{{ interface }} {
    description "{{ intf_description | ORPHRASE }}";
	<group name="units**">
    unit {{ unit }} {
        description "{{ unit_description | ORPHRASE }}";
	    <group name="{{ family }}">
        family {{ family }} {
            address {{ ip | to_list | joinmatches }};
            address {{ ip | to_list | joinmatches }} {
		</group>
    </group>
</group>
"""

test213="""
<input name="in1" load="text">
some.user@router-fw-host> show configuration interfaces | display set 
set interfaces ge-0/0/11 unit 0 description "SomeDescription in1"
set interfaces ge-0/0/11 unit 0 family inet address 10.0.40.121/31
set interfaces ge-5/0/5 unit 0 description "L3VPN: somethere"
set interfaces ge-5/0/5 unit 0 family inet address 10.0.31.48/31
set interfaces lo0 unit 0 description "Routing Loopback"
set interfaces lo0 unit 0 family inet address 10.0.0.254/32 primary
set interfaces lo0 unit 0 family inet address 10.6.4.4/32
</input>

<input load="text">
some.user@router-fw-host> show configuration interfaces | display set 
set interfaces ge-0/0/11 unit 0 description "SomeDescription glob1"
set interfaces ge-0/0/11 unit 0 family inet address 10.0.40.121/31
set interfaces ge-5/0/5 unit 0 description "L3VPN: somethere"
set interfaces ge-5/0/5 unit 0 family inet address 10.0.31.48/31
set interfaces lo0 unit 0 description "Routing Loopback"
set interfaces lo0 unit 0 family inet address 10.0.0.254/32 primary
set interfaces lo0 unit 0 family inet address 10.6.4.4/32
</input>

<input load="text">
some.user@router-fw-host> show configuration interfaces | display set 
set interfaces ge-0/0/11 unit 0 description "SomeDescription glob2"
set interfaces ge-0/0/11 unit 0 family inet address 10.0.40.121/31
set interfaces ge-5/0/5 unit 0 description "L3VPN: somethere"
set interfaces ge-5/0/5 unit 0 family inet address 10.0.31.48/31
set interfaces lo0 unit 0 description "Routing Loopback"
set interfaces lo0 unit 0 family inet address 10.0.0.254/32 primary
set interfaces lo0 unit 0 family inet address 10.6.4.4/32
</input>

<vars name="vars">
hostname = "gethostname"
</vars>

<group name="specific_out_interfaces.{{ interface }}{{ unit }}**" method="table" input="in1" output="out1">
set interfaces {{ interface | append('.') }} unit {{ unit }} family inet address {{ ip }}
set interfaces {{ interface | append('.') }} unit {{ unit }} description "{{ description | ORPHRASE }}"
set interfaces {{ interface | append('.') }} unit {{ unit }} family inet address {{ ip }} primary
{{ hostname | set("hostname") }}
</group>

<output name="out1" dict_to_list="key_name='interface', path='specific_out_interfaces'"/>

<group name="glob_out_interfaces.{{ interface }}{{ unit }}**" method="table">
set interfaces {{ interface | append('.') }} unit {{ unit }} family inet address {{ ip }}
set interfaces {{ interface | append('.') }} unit {{ unit }} description "{{ description | ORPHRASE }}"
set interfaces {{ interface | append('.') }} unit {{ unit }} family inet address {{ ip }} primary
{{ hostname | set("hostname") }}
</group>

<output dict_to_list="key_name='interface', path='glob_out_interfaces'"/>

<output returner="terminal" format="json"/>
"""



test214="""
<input name="input_1" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/11
 description input_1_data
 switchport trunk allowed vlan add 111,222
!
</input>

<input name="input_2" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/22
 description input_2_data
 switchport trunk allowed vlan add 222,888
!
</input>

<input name="input_3" load="text" groups="interfaces.trunks">
interface GigabitEthernet3/33
 description input_3_data
 switchport trunk allowed vlan add 333,999
!
</input>

<input name="input_4" load="text">
interface GigabitEthernet3/44
 description input_4_data
 switchport trunk allowed vlan add 444,1010
!
</input>

<input name="input_5" load="text">
interface GigabitEthernet3/55
 description input_5_data
 switchport trunk allowed vlan add 555,2020
!
</input>

<group name="interfaces.trunks" input="input_1">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_1") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks" input="input_2">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_2") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks" input="input_2">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_3") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_4") }}
!{{ _end_ }}
</group>

<group name="interfaces.trunks" input="input_5">
interface {{ interface }}
 switchport trunk allowed vlan add {{ trunk_vlans }}
 description {{ description | ORPHRASE }}
 {{ group_id | set("group_5") }}
!{{ _end_ }}
</group>
"""

test215="""
<template results="per_template">
<vars>
hostname="gethostname"
</vars>

<input load="text">
user.name@host-site-sw1> show configuration interfaces | display set 
set interfaces vlan unit 17 description "som if descript"
set interfaces vlan unit 17 family inet address 20.17.1.253/23 vrrp-group 25 virtual-address 20.17.1.254
</input>

<input load="text">
user.name@host-site-sw2> show configuration interfaces | display set 
set interfaces vlan unit 17 description "som if descript"
set interfaces vlan unit 17 family inet address 20.17.1.252/23 vrrp-group 25 virtual-address 20.17.1.254
</input>

<group name="juniper.{{ hostname }}.{{ interface }}**.units.{{ unit }}**" method="table">
set interfaces {{ interface }} unit {{ unit }} family inet address {{ ip | to_ip }}
set interfaces {{ interface }} unit {{ unit }} family inet address {{ ip | to_ip }} primary
set interfaces {{ interface }} unit {{ unit }} family inet address {{ ip | to_ip }} vrrp-group {{ vrrp_id }} virtual-address {{ vrrp_vip }}
set interfaces {{ interface }} unit {{ unit }} description "{{ description | ORPHRASE }}"
{{ hostname | set("hostname") }}
</group> 
</template>
"""

test216="""
<vars>
hostname="gethostname"
</vars>

<input load="text" name='in1' preference="merge">
user.name@host-site-sw1> show configuration interfaces | display set 
set interfaces vlan unit 17 description "som if descript"
set interfaces vlan unit 17 family inet address 20.17.1.253/23 vrrp-group 25 virtual-address 20.17.1.254
set interfaces vlan unit 17 family inet address 20.17.1.252/23
</input>


<group name="grp1" method="table" input='in1'>
set interfaces {{ interface }} unit {{ unit }} family inet address {{ ip | to_ip }} vrrp-group {{ vrrp_id }} virtual-address {{ vrrp_vip }}
set interfaces {{ interface }} unit {{ unit }} description "{{ description | ORPHRASE }}"
{{ hostname | set("hostname") }}
{{ group | set("group-0") }}
</group> 

<group name="grp2" method="table">
set interfaces {{ interface }} unit {{ unit }} family inet address {{ ip | to_ip }}
{{ hostname | set("hostname") }}
{{ group | set("group-1") }}
</group> 
"""

test217="""
<input load="text" name='in1' preference="merge">
user.name@host-site-sw1> show configuration interfaces | display set 
set interfaces vlan unit 17 description "som if descript"
set interfaces vlan unit 17 family inet address 20.17.1.253/23 vrrp-group 25 virtual-address 20.17.1.254
set interfaces vlan unit 17 family inet address 20.17.1.252/23
</input>

<group name="bla" output="not exists" func_not_exists="bla">
set interfaces {{ interface }} unit {{ unit }} family inet address {{ ip | to_ip }} vrrp-group {{ vrrp_id }} virtual-address {{ vrrp_vip }}
set interfaces {{ interface }} unit {{ unit }} description "{{ description | ORPHRASE }}"
{{ hostname | set("hostname") }}
{{ group | set("group-0") }}
</group>
"""

test218="""
<input load="text">
interface Loopback0
 description Router-id-loopback
 ip address 192.168.0.113/24
!
interface Vlan778
 ip address 2002::fd37/124
 ip vrf CPE1
!
</input>

<group name="interfaces_1">
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description }}
 ip vrf {{ vrf }}
</group>

<group name="interfaces_2">
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description }}
 ip vrf {{ vrf }}
</group>

<output 
format="excel" 
returner="file"
url="C:/result/"
filename="excel_out_%Y-%m-%d_%H-%M-%S"
load="yaml"
>
table:
  - headers: interface, ip, mask, vrf, description
    path: interfaces_1
    tab_name: tab-1
  - path: interfaces_2
    tab_name: tab-2
</output>
"""

test219="""
<input load="text">
router bgp 12.34
 address-family ipv4 unicast
  router-id 1.1.1.1
 !
 vrf CT2S2
  rd 102:103
  !
  neighbor 10.1.102.102
   remote-as 102.103
   address-family ipv4 unicast
    send-community-ebgp
    route-policy vCE102-link1.102 in
    route-policy vCE102-link1.102 out
   !
  !
  neighbor 10.2.102.102
   remote-as 102.103
   address-family ipv4 unicast
    route-policy vCE102-link2.102 in
    route-policy vCE102-link2.102 out
   !
  !
 vrf AS65000
  rd 102:104
  !
  neighbor 10.1.37.7
   remote-as 65000
   address-family ipv4 labeled-unicast
    route-policy PASS-ALL in
    route-policy PASS-ALL out
</input>

<group name="bgp_cfg">
router bgp {{ ASN }}
 <group name="ipv4_afi">
 address-family ipv4 unicast {{ _start_ }}
  router-id {{ bgp_rid }}
 </group>
 !
 <group name="vrfs">
 vrf {{ vrf }}
  rd {{ rd }}
  !
  <group name="neighbors">
  neighbor {{ neighbor }}
   remote-as {{ neighbor_asn }}
   <group name="ipv4_afi">
   address-family ipv4 unicast {{ _start_ }}
    send-community-ebgp {{ send_community_ebgp | set("Enabled") }}
    route-policy {{ RPL_IN }} in
    route-policy {{ RPL_OUT }} out
   </group>
  </group>
 </group>
</group>
"""

test220="""
<input load="text">
router bgp 12.34
 address-family ipv4 unicast
  router-id 1.1.1.1
 !
 vrf CT2S2
  rd 102:103
  !
  neighbor 10.1.102.102
   remote-as 102.103
   address-family ipv4 unicast
    send-community-ebgp
    route-policy vCE102-link1.102 in
    route-policy vCE102-link1.102 out
   !
  !
  neighbor 10.2.102.102
   remote-as 102.103
   address-family ipv4 unicast
    route-policy vCE102-link2.102 in
    route-policy vCE102-link2.102 out
   !
  !
 vrf AS65000
  rd 102:104
  !
  neighbor 10.1.37.7
   remote-as 65000
   address-family ipv4 labeled-unicast
    route-policy PASS-ALL in
    route-policy PASS-ALL out
</input>

<group name="bgp_cfg">
router bgp {{ ASN }}
 <group name="ipv4_afi">
 address-family ipv4 unicast {{ _start_ }}
  router-id {{ bgp_rid }}
 </group>
 !
 <group name="vrfs.{{ vrf }}">
 vrf {{ vrf }}
  rd {{ rd }}
  !
  <group name="peers.{{ neighbor }}**">
  neighbor {{ neighbor }}
   remote-as {{ neighbor_asn }}
   <group name="ipv4_afi">
   address-family ipv4 unicast {{ _start_ }}
    send-community-ebgp {{ send_community_ebgp | set("Enabled") }}
    route-policy {{ RPL_IN }} in
    route-policy {{ RPL_OUT }} out
   </group>
  </group>
 </group>
</group>
"""

test221="""
<input load="text">
interface Loopback0
 description Router-id-loopback
 ip address 192.168.0.113/24
!
interface Vlan778
 description CPE_Acces_Vlan
 ip address 2002::fd37/124
 ip vrf CPE1
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description }}
 ip vrf {{ vrf }}
</group>
"""

test222="""
<input load="text">
interface Loopback0
 description Router-id-loopback
 ip address 192.168.0.113/24
!
interface Vlan778
 description CPE_Acces_Vlan
 ip address 2002::fd37/124
 ip vrf CPE1
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description }}
 ip vrf {{ vrf }}
</group>

<output format="csv" returner="terminal"/>
"""

test223="""
<input load="text">
interface Loopback0
 description Router-id-loopback
 ip address 192.168.0.113/24
!
interface Gi0/37
 description CPE_Acces
 switchport port-security
 switchport port-security maximum 5
 switchport port-security mac-address sticky
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description }}
 ip vrf {{ vrf }}
 {{ port_security_cfg | _line_ | contains("port-security") | joinmatches }}
! {{ _end_ }}
</group>
"""

test224="""
<input load="text">
FastEthernet0/0 is up, line protocol is up
  Hardware is Gt96k FE, address is c201.1d00.0000 (bia c201.1d00.1234)
  MTU 1500 bytes, BW 100000 Kbit/sec, DLY 1000 usec,
FastEthernet0/1 is up, line protocol is up
  Hardware is Gt96k FE, address is b20a.1e00.8777 (bia c201.1d00.1111)
  MTU 1500 bytes, BW 100000 Kbit/sec, DLY 1000 usec,
</input>

<group>
{{ interface }} is up, line protocol is up
  Hardware is Gt96k FE, address is {{ ignore }} (bia {{MAC}})
  MTU {{ mtu }} bytes, BW 100000 Kbit/sec, DLY 1000 usec,
</group>
"""

test225="""
<vars>
GE_INTF = "GigabitEthernet\S+"
</vars>

<input load="text">
Protocol  Address     Age (min)  Hardware Addr   Type   Interface
Internet  10.12.13.1        98   0950.5785.5cd1  ARPA   FastEthernet2.13
Internet  10.12.13.3       131   0150.7685.14d5  ARPA   GigabitEthernet2.13
Internet  10.12.13.4       198   0950.5C8A.5c41  ARPA   GigabitEthernet2.17
</input>

<group>
Internet  {{ ip | re("IP")}}  {{ age | re("\d+") }}   {{ mac }}  ARPA   {{ interface | re("GE_INTF") }}
</group>
"""

test226="""
<input load="text">
interface Loopback0
 description Router id - OSPF, BGP
 ip address 192.168.0.113/24
!
interface Vlan778
 description CPE_Acces_Vlan
 ip address 2002::fd37/124
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
 description {{ description | ORPHRASE }}
</group>
"""


test227="""
<input load="text">
Pesaro# show ip vrf detail Customer_A
VRF Customer_A; default RD 100:101
  Interfaces:
    Loopback101      Loopback111      Vlan707    
</input>

<group name="vrfs">
VRF {{ vrf }}; default RD {{ rd }}
<group name="interfaces">
  Interfaces: {{ _start_ }}
    {{ intf_list | ROW }} 
</group>
</group>
"""


test228="""
<input load="text">
interface Vlan778
 ip address 2002::fd37::91/124
!
</input>

<group>
interface {{ interface }}
 ip address {{ ip | IPV6 | is_ip }}/{{ mask }}
</group>
"""

test229="""
<input load="text">
interface Vlan778
 ip address 2002::fd37::91/124
!
interface Loopback991
 ip address 192.168.0.1/32
!
</input>

<macro>
def check_svi(data):
    # data is list of lists:
    # [[{'interface': 'Vlan778', 'ip': '2002::fd37::91', 'mask': '124'}, 
    #   {'interface': 'Loopback991', 'ip': '192.168.0.1', 'mask': '32'}]]
    for item in data[0]:
        if "Vlan" in item["interface"]:
            item["is_svi"] = True
        else:
            item["is_svi"] = False
</macro>

<group>
interface {{ interface }}
 ip address {{ ip }}/{{ mask }}
</group>

<output macro="check_svi"/>
"""