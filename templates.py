nxos_show_run_interface = """
interface {{ Interface|contains("Eth|mgm") }}
  description {{cfg_description|startswith(5311)|phrase|upper | replace('L','@')}}
  description {{  cfg_description  | default}}
  switchport vlan mapping {{mappings| re('\d+\s\d+') | joinmatches(',')}} 
  switchport {{L2_intf| set('True') }}
  no switchport {{L3_intf | set('True') | default(L2)}}
  switchport mode trunk {{cfg_trunk | set  ('True') }}
  switchport trunk allowed vlan {{trunked_vlans |  joinmatches(',')}}
  switchport trunk allowed vlan add {{trunked_vlans  |  joinmatches(',') |  unrange(',','-')}}
  channel-group {{cfg_lag_id}} mode active
  vrf forwarding {{vrf}}
  vrf member {{vrf}}
  ip address {{ip}} {{mask}}
  ip address {{ip}}
  ip helper-address {{dhcp_helper_ip}} 
  switch virtual link {{vsl_link_id}}
 """
 
nxos_show_run_interface2 = """
{% group interfaces %}
interface {{ Interface}}
  description {{cfg_description|phrase|upper | replace('L','@')}}
  description {{  cfg_description  }}
{% group vlanMappings %}
  switchport vlan mapping {{ mapping | re('\d+\s\d+') }} 
{% endgroup vlanMappings %}
  switchport {{L2_intf| set('True') }}
  no switchport {{L3_intf | set('True') }}
  switchport mode trunk {{cfg_trunk | set  ('True') }}
  switchport trunk allowed vlan {{trunked_vlans |  joinmatches(',')}}
  switchport trunk allowed vlan add {{trunked_vlans  |  joinmatches(',') |  unrange(',','-')}}
  channel-group {{cfg_lag_id}} mode active
  vrf forwarding {{vrf}}
  vrf member {{vrf}}
  ip address {{ip}} {{mask}}
  ip address {{ip}}
  ip helper-address {{dhcp_helper_ip | default }} 
  switch virtual link {{vsl_link_id}}
{% endgroup interfaces %}
 """

huawei_lldp = """
{% var local_name='gethostname' %}
{% var domainsToStrip = ['.tpg.com.sg', '.tpgi.com.au'] %}
{% var IfsNormalize = {'Ge':['GigabitEthernet'], 'Po': 'Eth-Trunk', 'Te':['TenGigabitEthernet', 'TenGe'], 'Fe':['FastEthernet'], 'Eth':['Ethernet'], 'Pt':['Port']} %}

{% group LLDP_PEERS | table %}
{{ local_if | resuball(IfsNormalize) }}     98  {{ peer_if | resuball(IfsNormalize) }}     {{ peer_name | resuball(domainsToStrip) }}
{% endgroup LLDP_PEERS %}

{% definition IF_Descript_Hua %}
##yaml definition of Jinja2 template:
Type: jinja2
outFolder: './Output/'
Templates:
  - name: IF_Descript_Hua
    template: |
              ======================================================================
              {{ vars.local_name }}:
              ======================================================================
              {% for peer in LLDP_PEERS %}
              interface {{ peer.local_if }}
               description LK:{{ peer.peer_name }}:{{ peer.peer_if }}
              {% endfor %}
{% enddefinition IF_Descript_Hua %}
    """
    
IOS_Intfs = """
interface {{ Interface | _key_ }}
 description {{description | orphrase | upper}}
 switchport access vlan {{ accessVlan }}
 switchport mode access {{ mode | set(access) }}
 switchport trunk allowed vlan {{ trunkVlans | joinmatches() }}
 switchport voice vlan {{voiceVlan }}
 switchport port-security maximum {{ maxMAC }}
 switchport port-security aging time {{ agingTimer }}
 ip address {{ ip }} {{ mask }}
 ip helper-address {{ helper }}
! {{ _end_ }}
    """
    
IPs = """
{% var hostname = 'gethostname' %}

{% group IPs** %}
interface {{ Interface }}
 description {{description | orphrase }}
 {{ hostname | record(hostname) }}
 ip address {{ ipv4 | _key_  }} {{ mask }}
 ipv4 address {{ ipv4 | _key_  }} {{ mask }}
 vrf forwarding {{ vrf | default(GRT) }}
 vrf {{ vrf | default(GRT) }}
{% endgroup IPs** %}
"""

IOS_Intfs2 = """
{% group interfaces**._key_.descript %}
interface {{ Interface | _key_ }}
 description {{description | orphrase | upper}}
! {{ _end_ }}
{% endgroup interfaces**._key_.descript %}

{% group interfaces**._key_.cfg.l2 %}
interface {{ Interface | _key_ }}
 switchport access vlan {{ accessVlan }}
 switchport mode access {{ mode | set(access) }}
 switchport trunk allowed vlan {{ trunkVlans | joinmatches() }}
 switchport voice vlan {{voiceVlan }}
 switchport port-security maximum {{ maxMAC }}
 switchport port-security aging time {{ agingTimer }}
 ip address {{ ip }} {{ mask }}
 ip helper-address {{ helper }}
! {{ _end_ }}
{% endgroup interfaces**._key_.cfg.l2 %}
    """
    
iosXRsampleBGP = """
{% group bgpProcess %}
router bgp {{BGP_AS}}

{% group IPv4UnicastAFI %}
 address-family ipv4 unicast {{ v4AFI | set(True) | exact }}
  additional-paths receive {{addPathRCV|set(True)}}
  allocate-label all {{allocLblbALL|set(True)}}
{% group networkStatements | table %}
  network {{netowrkStatemenetIP}} route-policy {{netowrkStatemenetRPL}}
{% endgroup networkStatements %}
{% endgroup IPv4UnicastAFI %}

{% group neighbourGroups %}
 neighbor-group {{name}}
  remote-as {{peerAS}}
  keychain {{keychain}}
  update-source {{updateSource}}
{% group v4AFI %}
  address-family ipv4 unicast {{ v4AFI | set(True) | exact }}
   next-hop-self {{NHS|set(True)}}
   remove-private-AS {{ remove_priv_as | set(True) }}
{% endgroup v4AFI %}
{% group VPNv4AFI %}
  address-family vpnv4 unicast {{ VPNv4AFI | set(True) | exact }}
   route-policy {{rplOut}} out
{% endgroup VPNv4AFI %}
{% endgroup neighbourGroups %}

{% group Neighbours %}
 neighbor {{peeIP | ip | word }}
  use neighbor-group {{peerNbrGrp}}
  remote-as {{peerAS}}
  description {{peerDescription}}
  update-source {{updateSrc}}
{% group v4AFI %}
  address-family ipv4 unicast {{ v4AFI | set(True) | exact }}
   next-hop-self {{NHS|set(True)}}
{% endgroup v4AFI %}
{% group VPNv4AFI %}
  address-family vpnv4 unicast {{VPNv4AFI | set(True) | exact }}
{% endgroup VPNv4AFI %}
{% endgroup Neighbours %}

{% group VRFs %}
 vrf {{VRF}}
  rd {{rd}}
{% group v4AFI %}
  address-family ipv4 unicast {{ v4AFI | set(True) }}
{% endgroup v4AFI %}
{% group neighbours %}
  neighbor {{peerIP }}
   remote-as {{peerAS}}
{% group v4AFI %}
   address-family ipv4 unicast {{ _start_ | exact }}
    send-community-ebgp {{sendCommunity|set(True)}}
    route-policy {{rplIN}} in
    route-policy {{rplOut}} out
{% endgroup v4AFI %}
{% endgroup neighbours %}
{% endgroup VRFs %}

!{{ _end_ }}
{% endgroup bgpProcess %}
    """
        
cdpmap = """
{% var hostname = gethostname %}

{% group CDP_IOS %}
Device ID: {{ peer_hostname | replace('.tpg.local', '') }}
  IP address: {{ ip }}
Platform: {{ platform | phrase | upper }},  Capabilities: {{ capabilities | phrase }} 
Interface: {{ interface | replace('GigabitEthernet', 'Ge') }},  Port ID (outgoing port): {{ peer_interface | phrase | replace('Port', 'Pt') }}
Interface: {{ interface | replace('GigabitEthernet', 'Ge') }},  Port ID (outgoing port): {{ peer_interface | replace('GigabitEthernet', 'Ge')}}

{% group peerVersion %}
Version :{{ _start_ }}
{{ _line_ | contains(Version) }}
{{ _end_ }}
{% endgroup peerVersion %}

{% endgroup CDP_IOS %}

{% definition pythonDictTransform %}
##yaml definition of graphml dict to draw the map:
Type: pydict
Stuctures:
  - 'name': 'graphmlDictFromCDP'
    'nodes': 
      - 'node_name': 'hostname'
        'pic_name': 'router'
        'label': 'hostname'
        'bottom_label': 'platform'
        'top_label': 'ip' 
    'edges':
      - 'src_node': 'hostname'
        'src_label': 'interface'
        'label': ''
        'trgt_node': 'peer_hostname'
        'trgt_label': 'peer_interface'
        'description': "'vlans_trunked: {}\nstate: {}'.format(vlans_trunked, state)"
{% enddefinition pythonDictTransform %}
    """
    
sampleTwmplate = """
    {% group grp-1 %}
    grp1Version :{{ grp1Var1 }}
    {% group grp-2 %}
    grp2Version :{{ grp2Var1 }}
    {% group grp-3 %}
    grp3Version :{{ grp3Var1 }}
    {% group grp-4 %}
    grp4Version :{{ grp4Var1 }}
    {% endgroup grp-4 %}
    {% endgroup grp-3 %}
    outGrp3Version :{{ grp5Var1 }}
    {% endgroup grp-2 %}
    {% endgroup grp-1 %}
    {% group grp-4 %}
    grp4Version :{{ grp4Var1 }}
    {% endgroup grp-4 %}
    """
    
cdpmapNexus = """
{% var hostname = gethostname %}

{% group NexusInterfaces | default(NULL) %}
interface {{ Inerface }}
  description {{ description | phrase | default(empty) }}
  mtu {{ mtu | default }}
  vrf member {{ vrf | default(GRT) }}
  ip address {{ v4address }}/{{ v4mask | default(32) }}
  ipv6 address {{ v6address | default }}/{{ v6mask | default }}
{% endgroup NexusInterfaces %}
    """
    
ios_arp = """
{% group arp | table %}
Internet  {{ip}} {{age}}   {{mac}}  ARPA  {{Interface}}
Internet  {{ip}} {{age}}   {{mac}}  arpa  {{Interface}}
{% endgroup arp %}
    """
    
IOS_Intfs_with_CDP2 = """
{% var filename='getfilename' %}    
{% var hostname='gethostname' %}

{% var domainsToStrip = ['.tpg.local', '.iinet.net.au', '.win2k', 'idn.au.tcnz.net'] %}
{% var IfsNormalize = {'Ge':['^GigabitEthernet'], 'Pt':['^Port'], 'Po': '^Eth-Trunk', 'Te':['^TenGe', '^TenGigabitEthernet', '^TenGigE'], 'Fe':['^FastEthernet']} %}

{% group interfaces** %}
-------------------------{{_start_}}
Device ID: {{ CDP_peer_Hostname | replaceall(domainsToStrip) | exclude(SEP) | title }}
  IP address: {{ CDP_peer_ip }}
Platform: {{ CDP_peer_platform | orphrase | upper }},  Capabilities: {{ CDP_peer_capabilities | orphrase }} 
Interface: {{ Interface | resuball(IfsNormalize) | _key_ }},  Port ID (outgoing port): {{ CDP_peer_interface | orphrase | resuball(IfsNormalize) }}

{% endgroup interfaces** %}

{% group interfaces** %}
interface {{ Interface | resuball(IfsNormalize) | _key_ }}
 description {{description | orphrase }}
 no snmp trap link-status
 spanning-tree portfast {{ portfast | set(True) }}
 spanning-tree bpduguard enable {{ bpduguard | set(True) }}
 ip address {{ ip | default }} {{ mask | default(128)}}
 ip helper-address {{ helper }}
 no ip redirects
 no ip unreachables
 no ip proxy-arp
 {{ sysname | record(hostname) }}
 {{ local_bgp_as | record(bgpAS) }}
!{{_end_}}
{% endgroup interfaces** %}

{% group bgp %}
router bgp {{ bgp_as | var(bgpAS) }}
!{{ _end_ }}
{% endgroup bgp %}
    """
    
IOS_Intfs_with_CDP = """
{% var filename='getfilename' %}    
{% var hostname='gethostname' %}

{% var domainsToStrip = ['.tpg.local', '.iinet.net.au', '.win2k', 'idn.au.tcnz.net'] %}
{% var IfsNormalize = {'Ge':['^GigabitEthernet'], 'Pt':['^Port'], 'Po': '^Eth-Trunk', 'Te':['^TenGe', '^TenGigabitEthernet', '^TenGigE'], 'Fe':['^FastEthernet']} %}

{% group CDP_IOS* %}
-------------------------{{_start_}}
Device ID: {{ CDP_peer_Hostname | replaceall(domainsToStrip) | exclude(SEP) | title }}
  IP address: {{ CDP_peer_ip }}
Platform: {{ CDP_peer_platform | orphrase | upper }},  Capabilities: {{ CDP_peer_capabilities | orphrase }} 
Interface: {{ Interface | resuball(IfsNormalize) | _key_ }},  Port ID (outgoing port): {{ CDP_peer_interface | orphrase | resuball(IfsNormalize) }}
{% endgroup CDP_IOS* %}

{% group interfaces* %}
interface {{ Interface | resuball(IfsNormalize) }}
{{ sysname | record(hostname) }}
 description {{description | orphrase }}
{% group Settings.L2.switchport | default(None)%}
 switchport access vlan {{ AccessVlan }}
 switchport mode access {{ mode | set(access) }}
 switchport voice vlan {{voiceVlan }}
 switchport trunk allowed vlan {{ trunkVlans | joinmatches() | unrange('-',',') }}
 switchport trunk allowed vlan add {{ trunkVlans | joinmatches() | unrange('-',',') }}
 switchport mode trunk {{ mode | set(trunk) }}  {{ Vlans | set(all) }}
{% endgroup Settings.L2.switchport %}
{% group Settings.L2.portSecurity %}
 switchport port-security maximum {{ MaxMAC }}
 switchport port-security aging time {{ agingTimeout }}
 switchport port-security aging type {{ agingType }}
{% endgroup Settings.L2.portSecurity %}
 spanning-tree portfast {{ portfast | set(True) }}
 spanning-tree bpduguard enable {{ bpduguard | set(True) }}
 ip address {{ ip | default }} {{ mask | default(128)}}
 ip helper-address {{ helper }}
{{ local_bgp_as | record(bgpAS) }}
{% endgroup interfaces* %}

{% group bgp %}
router bgp {{ bgp_as | var(bgpAS) }}
!{{ _end_ }}
{% endgroup bgp %}
    """
    
IOS_or_Nexus_CDP = """
{% var local_hostname = 'getfilename' %}

{% var domainsToStrip = ['.tpgi.com.au', '.tpgtelecom.com.', '.comindico.com.au', '.tpg.local', '.on.ii.net', '.win2k.iinet.net.au'] %}
{% var IfsNormalize = {'Ge':['GigabitEthernet'], 'Po': 'Eth-Trunk', 'Te':['TenGigabitEthernet', 'TenGe'], 'Fe':['FastEthernet'], 'Eth':['Ethernet'], 'Pt':['Port']} %}

##resub(\(\S+\), "") } - replaces/wipe endings like (FDS04DFVC678)
{% group peers %}
## Cisco IOS:
Device ID: {{ peer_hostname | replaceall(domainsToStrip) | resub(\(\S+\), "") }}
Device ID:{{ peer_hostname | _start_ | replaceall(domainsToStrip) | resub(\(\S+\), "") }}
  IP address: {{ peer_ip }}    
Platform: {{ peer_platform | phrase }},  Capabilities: {{ peer_capabilities | phrase }}
Platform: {{ peer_platform }},  Capabilities: {{ peer_capabilities | phrase }}
Platform: {{ peer_platform }},  Capabilities: {{ peer_capabilities }}
Platform: {{ peer_platform | phrase }},  Capabilities: {{ peer_capabilities }}
Interface: {{ local_interface | replaceall(IfsNormalize) }},  Port ID (outgoing port): {{ peer_interface | replaceall(IfsNormalize) }}
Interface: {{ local_interface | replaceall(IfsNormalize) }},  Port ID (outgoing port): {{ peer_interface | phrase | replaceall(IfsNormalize) }}

##Cisco Nexus:
Device ID:{{ peer_hostname | _start_ | replaceall(domainsToStrip) | resub(\(\S+\), "") }}
    IPv4 Address: {{ peer_ip }}
{{ peer_platform }}, Capabilities: {{ peer_capabilities }}
{{ peer_platform | phrase }}, Capabilities: {{ peer_capabilities }}
{{ peer_platform }}, Capabilities: {{ peer_capabilities | phrase }}
{{ peer_platform | phrase }}, Capabilities: {{ peer_capabilities | phrase }}
{{ local_interface | replaceall(IfsNormalize) }}, Port ID (outgoing port): {{ peer_interface | replaceall(IfsNormalize) }}
{{ local_interface | replaceall(IfsNormalize) }}, Port ID (outgoing port): {{ peer_interface | replaceall(IfsNormalize) | phrase }}

{% endgroup peers %}
"""

Cisco_IOS_BGP_Peers = """
##based on show bgp * all neighbours output
{% var deviceName='gethostname' %}
{% var vendor='Cisco' %}

{% group BGP_PEERS %}
For address family: {{ AFI | orphrase }}

{% group PEERS | default(None) %}
BGP neighbor is {{ peer_ip }},  vrf {{ source_vrf }},  remote AS {{ peer_as }}, {{ type }} link
 Description: {{ source_description | orphrase }}
  BGP version 4, remote router ID {{ peer_rid }}
  BGP state = {{ source_state }}, up for {{ ignore() }}
Local host: {{ source_ip }}, Local port: 15736
{{ source_hostname | record(deviceName) }}
{{ source_make | record(vendor) }}
{{ source_as | record(bgp_as) }}
{{ source_rid | record(bgp_rid) }}

{% endgroup PEERS %}
{% endgroup BGP_PEERS %}

{% group BGP_Config %}
router bgp {{ AS | var(bgp_as) }}
 bgp router-id {{ RID | var(bgp_rid) }}
{% endgroup BGP_Config %}

##
{% group Interfaces_L3 | default(None) | containsall(v4address, v4mask) %}
interface {{ Inerface | replace(Vlan, SVI)}}
##Cisco IOS:
 description {{ description | orphrase | title }}
 vrf forwarding  {{ vrf | default(Default) }} 
 ip address {{ v4address  }} {{ v4mask  }}
 no ip redirects {{ipRedir | set(Disabled) }}
 
## Cisco NX-OS:
  description {{ description | orphrase }}
  vrf member {{ vrf | default(Default)}} 
  ip address {{ v4address  }}/{{ v4mask  }}
  
!{{ _end_ }}
{% endgroup Interfaces_L3 %}
    """
    
ips = """
{% var IfsNormalize = {'Vl':['Vlan', 'Vlanif'], 'Ge':['GigabitEthernet'], 'Po': 'Eth-Trunk', 'Te':['TenGigabitEthernet', 'TenGe'], 'Fe':['FastEthernet'], 'Eth':['Ethernet'], 'Pt':['Port']} %}

##{% group interfaces | containsall(ip) %}
##interface {{ Interface | resuball(IfsNormalize) }}
## ip address {{ ip }} {{ mask }}
##{% endgroup interfaces %}

{% group interfaces %}
interface {{ Interface }}
 ip address {{ ip }} {{ mask }}
{% endgroup interfaces %}
"""

IOS_Intfs_with_CDP2_XML = """
<v>
filename='getfilename'
hostname='gethostname' 
domainsToStrip = ['.tpg.local', '.iinet.net.au', '.win2k', 'idn.au.tcnz.net']
IfsNormalize = {
     'Ge':['^GigabitEthernet'], 
     'Pt':['^Port'], 
     'Po':['^Eth-Trunk'], 
     'Te':['^TenGe', '^TenGigabitEthernet', '^TenGigE'], 
     'Fe':['^FastEthernet']
     }
</v>

<lookup name='locations' format='ini'>
[SITES]
-qv1              : Perth WA, 250 St Georges Terrace, WA 6000
-osb              : Perth WA, 24 Sangiorgio Crt, Osborne Park WA 6017
-mil              : Perth WA, 4 Millrose Drive, Malaga WA 6090 (NextDC)
-sub              : Perth WA, 502 Hay St, Subiaco WA
-per-apt-stg      : Perth WA, 44 St Georges, WA
-per-pow-stg      : Perth WA, 12 St Georges, WA
-cam              : Melbourne VIC, 293 Camberwell Rd, VIC
-gex              : Geelong VIC, Thompson Road, Victoria
-rex              : Cape Town Africa, 263 Victoria Road, Salt River, South Africa
-mas              : Sydney NSW, 639 Gardners Road, Mascot NSW 2020
-syd-gls-har      : Sydney NSW, 400 Harris Street, ULTIMO NSW 2007
-ult              : Sydney NSW, 400 Harris Street, ULTIMO NSW 2007
-syd-apt-ros      : Sydney NSW, 30 Ross St, Glebe NSW 2037
-akl-iin-cit      : Auckland NZ, 7 City Road, New Zealand
-isa-city         : Auckland NZ, 7 City Road, New Zealand
-anx              : Canberra ACT, 470 Northbourne Avenue, DICKSON 2602
-creek            : Brisbane QLD, 127 Creek St, QLD 4000
-mql              : Mildura VIC, Cnr 10th Street and Orange Avenue, 3500
-lon              : Adelaide SA, 19-31 London road, Mile End South, SA, 5031
-fra              : Adelaide SA, 262-280 Franklin Street, SA 5000
-117kws           : Adelaide SA, 117 King William St
-150g             : Adelaide SA, 150 Grenfell
-90kws            : Adelaide SA, 90 King William Street, 5000
-blt              : Ballarat VIC, Neerim Crescent, Victoria
gle30             : Glebe, 30 Ross Street, NSW
syd-sot-ken       : SYD, 201KentStL14
</lookup>

<g name="{{ Interface }}**.CDP" default="" containsall="Interface">
-------------------------{{_start_}}
-----------------------{{_start_}}
Device ID: {{ CDP_peer_Hostname | replaceall('domainsToStrip') | exclude('SEP') | title | rlookup('locations.SITES', 'site') }}
  IP address: {{ CDP_peer_ip }}
Platform: {{ CDP_peer_platform | orphrase | upper }},  Capabilities: {{ CDP_peer_capabilities | orphrase }} 
Interface: {{ Interface | resuball('IfsNormalize') }},  Port ID (outgoing port): {{ CDP_peer_interface | orphrase | resuball('IfsNormalize') }}
</g>

<g name="{{ Interface }}**">
interface {{ Interface | resuball('IfsNormalize') }}
 description {{description | orphrase }}
 spanning-tree portfast {{ portfast | set(True) }}
 spanning-tree bpduguard enable {{ bpduguard | set(True) }}
 switchport access vlan {{ AccessVlan }}
 switchport mode access {{ mode | set('access') }}
 switchport voice vlan {{voiceVlan }}
 switchport trunk allowed vlan {{ trunkVlans | joinmatches(char = ',') | unrange(rangechar = '-' , joinchar=',')}}
 switchport trunk allowed vlan add {{ trunkVlans | joinmatches(',') | unrange('-',',') }}
 switchport mode trunk {{ mode | set('trunk') }}  {{ Vlans | set('all') }}
 <g name="cfg.l3">
 ip address {{ ip | default }} {{ mask | default(128)}}
 ipv4 address {{ ip | default }} {{ mask | default(128) | _start_ }}
 ip helper-address {{ helper }}
 </g>
 {{ sysname | let('hostname') }}
 {{ local_bgp_as | let('bgpAS') }}
!{{_end_}}
</g>

<g name="bgp">
router bgp {{ bgp_as | record('bgpAS') }}
</g>

<out
name="Intfs_ips_XML"
format="jinja2"
returner="terminal"
>
hostname,interface,description
{% for key, value in _data.items() %}
{{ value.sysname }},{{ key }},{{ value.description }}
{% endfor %}
</out>
"""


Intfs_ips_XML = """
<vars include="./vars/vars.txt" load="python"/>

<input name="Cisco_IOS" load="python">
url = "./IOS/"
extensions = ['txt', 'log']
filters = [".*"]
</input>

<input name="Cisco_IOS-XR" load="yaml">
url: ["./IOS-XR/"]
extensions: 'txt'
filters: "running_config_IOSXR"
</input>

<input name="Cisco_NX-OS">
url = "./NX-OS/"
filters = ["cns11-gc", "intfs"]
</input>

<g name = "BGP">
router bgp {{ bgp_as | record('bgpAS') | default('ABC') }}
</g>

<g name="{{ hostname }}.interfaces.{{ Interface }}" containsall="ip" default="None" input="Cisco_IOS" output="IPAM">
##====================CISCO IOS====================
interface {{ Interface | resuball('IfsNormalize') }}
 description {{description | orphrase }}
 ip address {{ ip }} {{ mask }}
 vrf forwarding {{ vrf | default('Default') }}
 {{ hostname | let('hostname') }}
 {{ bgp_as | let('bgpAS') }}
!{{_end_}}
</g>

<g name="{{ hostname }}.interfaces.{{ Interface }}" containsall="ip" default="None" output="IPAM" input="Cisco_IOS-XR">
##====================CISCO IOS-XR==================
interface {{ Interface | resuball('IfsNormalize') }}
 description {{description | orphrase }}
 ipv4 address {{ ip }} {{ mask }}
 vrf {{ vrf | default('Default') }}
 {{ hostname | let('hostname') }}
 {{ bgp_as | let('bgpAS') }}
!{{_end_}}
</g>

<g name="{{ hostname }}.interfaces.{{ Interface }}" containsall="ip" default="None" output="IPAM" input="./NX-OS/">
##====================CISCO NX-OS==================
interface {{ Interface | resuball('IfsNormalize') }}
  description {{description | orphrase }}
  ip address {{ ip }}/{{ mask }}
  vrf member {{ vrf | default('Default') }}
{{ hostname | let('hostname') }}
{{ bgp_as | let('bgpAS') }}
{{ _end_ }}
</g>

<g name="{{ hostname }}.interfaces.{{ Interface }}.config" input="Cisco_IOS">
##====================All interfaces Config====================
interface {{ Interface | resuball('IfsNormalize') }}
 {{ config | _line_  }}
!{{ _end_ }}
{{_end_}}
</g>

<out
name="Intfs_ips_XML"
type="json"
destination="file"
/>
"""

Intfs_ios_XML_simple = """
##====================CISCO IOS====================
interface {{ Interface | _key_ }}
 description {{description | orphrase }}
 ip address {{ ip }} {{ mask }}
 vrf forwarding {{ vrf | default(GRT) }}
 {{ config | _line_ | strip }}
!{{_end_}}
"""

ip_intf_only = """
<g name="interfaces_config" containsall="ip">
##====================CISCO IOS====================
interface {{ Interface }}
 description {{description | orphrase }}
 ip address {{ ip }} {{ mask }}
 vrf forwarding {{ vrf | default(GRT) }}
!{{_end_}}
</g>
"""


bgp_peers_configured_and_state = """
<vars>
hostname='gethostname' 
caps = "orphrase | upper"
</vars>

<lookup 
name="aux_ini" 
format="ini" 
include="C:/Users/Denis/YandexDisk/Python/TPG/Text Template Parser/ttp/!USECASES/BGP MAP/aux_data.txt"
/>

<lookup 
name="aux_csv" 
format="csv" 
key='ASN'
>
ASN,as_name,as_description,as_number
9942,SOUL,Public ASN,9942
7545,TPG,Public ASN,7545
2764,AAPT,Public ASN,2764
4174,AAPT,Public ASN,4174
4739,INTERNODE,Public ASN,4739
4817,TPG SG,Public ASN,4817
</lookup>

<!--NXOS "show run | sec bgp" parse template-->
<group name="{{ hostname }}.bgp_config.AS_{{ loca_as }}">
router bgp {{ bgp_as | record(loca_as) | lookup(name="aux_csv", add_field='asn_details') }}
  router-id {{ rid }}
  <group name="vrfs*.{{ VRF }}">
  vrf {{ VRF }}
    {{ hostname | let(hostname) }}
    {{ local_as | let(loca_as) }}
    <group name="afi**">
      <group name="Unicast**.{{ AFI }}">
    address-family {{ AFI }} unicast
      network {{ network | joinmathes() }}
      redistribute direct route-map {{ redistr_direct_rpl }}
      </group>
    </group>
    <group name="peers**.{{ PEER }}">    
    neighbor {{ PEER }}
      remote-as {{ remote_as | lookup(aux_csv) }}
      description {{ description | chain(caps) }}
      <group name="afi**.{{ AFI }}">
       <group name="Unicast**">
      address-family {{ AFI }} unicast
        shutdown {{ shutdown | set(True) }}
        allowas-in {{ allow_as_in | set(True) }}
        route-map {{ rpl_in }} in
        route-map {{ rpl_out }} out
       </group>
      </group>
    </group>
  </group>
</group>


<!--NXOS "show bgp vrf all all neighbors" parse template-->
<g name = "peers_state.{{ PEER }}">
BGP neighbor is {{ PEER }},  remote AS {{ remote_as | lookup(aux_csv, asn_details) }}, {{ type }} link, Peer index 2
  Description: {{ description | chain(caps) }}
  BGP version 4, remote router ID {{ peer_rid }}
  BGP state = {{ state }}, up for {{ time }}
  BGP state = {{ state }}, down for {{ time }}, retry in {{ ignore }}
  BGP state = {{ state }} (Admin), down for {{ time }}
  Last read 00:00:06, hold time = {{ holddown }}, keepalive interval is {{ keepalive }} seconds
  
  <g name = "afi**">  
   <g name="Unicast**.{{ AFI }}">
  For address family: {{ AFI }} Unicast
  {{ received_count }} accepted paths consume {{ used_bytes }} bytes of memory
  {{ advertised_count }} sent paths
  Allow my ASN {{ allow_as_in_count }} times
  Inbound route-map configured is {{ rpl_in }}, handle obtained
  Outbound route-map configured is {{ rpl_out }}, handle obtained
   </g>
  </g>  
  
  Local host: {{ source_ip }}, Local port: {{ source_port }}
</g>

<out
name="bgp_peers_configured_and_state"
type="json"
destination="file"
/>
"""

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