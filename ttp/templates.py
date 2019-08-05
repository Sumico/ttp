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
 description {{description | ORPHRASE | upper}}
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
 description {{description | ORPHRASE }}
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
 description {{description | ORPHRASE | upper}}
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
Platform: {{ CDP_peer_platform | ORPHRASE | upper }},  Capabilities: {{ CDP_peer_capabilities | ORPHRASE }} 
Interface: {{ Interface | resuball(IfsNormalize) | _key_ }},  Port ID (outgoing port): {{ CDP_peer_interface | ORPHRASE | resuball(IfsNormalize) }}

{% endgroup interfaces** %}

{% group interfaces** %}
interface {{ Interface | resuball(IfsNormalize) | _key_ }}
 description {{description | ORPHRASE }}
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
Platform: {{ CDP_peer_platform | ORPHRASE | upper }},  Capabilities: {{ CDP_peer_capabilities | ORPHRASE }} 
Interface: {{ Interface | resuball(IfsNormalize) | _key_ }},  Port ID (outgoing port): {{ CDP_peer_interface | ORPHRASE | resuball(IfsNormalize) }}
{% endgroup CDP_IOS* %}

{% group interfaces* %}
interface {{ Interface | resuball(IfsNormalize) }}
{{ sysname | record(hostname) }}
 description {{description | ORPHRASE }}
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
For address family: {{ AFI | ORPHRASE }}

{% group PEERS | default(None) %}
BGP neighbor is {{ peer_ip }},  vrf {{ source_vrf }},  remote AS {{ peer_as }}, {{ type }} link
 Description: {{ source_description | ORPHRASE }}
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
 description {{ description | ORPHRASE | title }}
 vrf forwarding  {{ vrf | default(Default) }} 
 ip address {{ v4address  }} {{ v4mask  }}
 no ip redirects {{ipRedir | set(Disabled) }}
 
## Cisco NX-OS:
  description {{ description | ORPHRASE }}
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
Platform: {{ CDP_peer_platform | ORPHRASE | upper }},  Capabilities: {{ CDP_peer_capabilities | ORPHRASE }} 
Interface: {{ Interface | resuball('IfsNormalize') }},  Port ID (outgoing port): {{ CDP_peer_interface | ORPHRASE | resuball('IfsNormalize') }}
</g>

<g name="{{ Interface }}**">
interface {{ Interface | resuball('IfsNormalize') }}
 description {{description | ORPHRASE }}
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
{% for key, value in _data_.items() %}
{{ value.sysname }},{{ key }},{{ value.description }}
{% endfor %}
</out>
"""


Intfs_ips_XML = """
<vars>
hostname = "gethostname"
</vars>

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

<g name="{{ hostname }}.interfaces.{{ Interface }}" containsall="ip" default="None" input="Cisco_IOS">
##====================CISCO IOS====================
interface {{ Interface | resuball('IfsNormalize') }}
 description {{description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
 vrf forwarding {{ vrf | default('Default') }}
 {{ hostname | let('hostname') }}
 {{ bgp_as | let('bgpAS') }}
!{{_end_}}
</g>

<g name="{{ hostname }}.interfaces.{{ Interface }}" containsall="ip" default="None" input="Cisco_IOS-XR">
##====================CISCO IOS-XR==================
interface {{ Interface | resuball('IfsNormalize') }}
 description {{description | ORPHRASE }}
 ipv4 address {{ ip }} {{ mask }}
 vrf {{ vrf | default('Default') }}
 {{ hostname | let('hostname') }}
 {{ bgp_as | let('bgpAS') }}
!{{_end_}}
</g>

<g name="{{ hostname }}.interfaces.{{ Interface }}" containsall="ip" default="None" input="./NX-OS/">
##====================CISCO NX-OS==================
interface {{ Interface | resuball('IfsNormalize') }}
  description {{description | ORPHRASE }}
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
format="json"
returner="terminal"
/>
"""

Intfs_ios_XML_simple = """
##====================CISCO IOS====================
interface {{ Interface | _key_ }}
 description {{description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
 vrf forwarding {{ vrf | default(GRT) }}
 {{ config | _line_ | strip }}
!{{_end_}}
"""

ip_intf_only = """
<g name="interfaces_config">
##====================CISCO IOS====================
interface {{ Interface }}
 description {{description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
 vrf forwarding {{ vrf | default('GRT') }}
!{{_end_}}
</g>

<o 
name="ip_intf_only"
returner="file" 
url="./Output/" 
format="yaml"
method="join"
/>
"""


bgp_peers_configured_and_state = """
<vars name="vars.info">
hostname='gethostname' 
</vars>

<vars>
caps = "ORPHRASE | upper"
</vars>

<lookup 
name="aux_ini" 
load="ini" 
include="C:/Users/Denis/YandexDisk/Python/TPG/Text Template Parser/ttp/!USECASES/BGP MAP/aux_data.txt"
/>

<lookup 
name="aux_csv" 
load="csv" 
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
router bgp {{ bgp_as | record('loca_as') | lookup(name="aux_csv", add_field='asn_details') }}
  router-id {{ rid }}
  <group name="vrfs*.{{ VRF }}">
  vrf {{ VRF }}
    {{ hostname | let('hostname') }}
    {{ local_as | let('loca_as') }}
    <group name="afi**">
      <group name="Unicast**.{{ AFI }}">
    address-family {{ AFI }} unicast
      network {{ network | joinmatches() }}
      redistribute direct route-map {{ redistr_direct_rpl }}
      </group>
    </group>
    <group name="peers**.{{ PEER }}">    
    neighbor {{ PEER }}
      remote-as {{ remote_as | lookup('aux_csv') }}
      description {{ description | chain('caps') }}
      <group name="afi**.{{ AFI }}">
       <group name="Unicast**">
      address-family {{ AFI }} unicast
        shutdown {{ shutdown | set('True') }}
        allowas-in {{ allow_as_in | set('True') }}
        route-map {{ rpl_in }} in
        route-map {{ rpl_out }} out
       </group>
      </group>
    </group>
  </group>
</group>


<!--NXOS "show bgp vrf all all neighbors" parse template-->
<g name = "peers_state.{{ PEER }}">
BGP neighbor is {{ PEER }},  remote AS {{ remote_as | lookup('aux_csv', 'asn_details') }}, {{ type }} link, Peer index 2
  Description: {{ description | chain('caps') }}
  BGP version 4, remote router ID {{ peer_rid }}
  BGP state = {{ state }}, up for {{ time }}
  BGP state = {{ state }}, down for {{ time }}, retry in {{ ignore }}
  BGP state = {{ state }} (Admin), down for {{ time }}
  Last read {{ ignore }}, hold time = {{ holddown }}, keepalive interval is {{ keepalive }} seconds
  
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
format="json"
returner="file"
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
<group name="interfaces">
interface {{ interface | upper }}
 description {{ description | split('-') }}
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
VRF TPGMPLS (VRF Id = 4); default RD 7545:24;
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
    RT:7545:24              
  Import VPN route-target communities
    RT:7545:24               RT:7545:7544             RT:9942:17
    RT:9942:31546            RT:7545:89900            RT:7545:650
    RT:7545:89564            RT:7545:89611           
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