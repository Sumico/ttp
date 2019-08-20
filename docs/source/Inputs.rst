Inputs
======
.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
Input attributes
----------------

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

* string (optional) - name of the input to reference in group *input* attribute. Default value is "Default_Input" and used internaly to store set of data that should be parsed by all groups.

groups
------------------------------------------------------------------------------
``groups="group1, group2, ... , groupN"``

* groupN (optional) - Default value is "all", comma separated string of group names that should be used to parse given input data. If value is "all" - input data will be parsed by each group.

load
------------------------------------------------------------------------------
``load="loader_name"``

* loader_name - name of the loader that should be used to load input tag text data, supported values are ``python, yaml, json or text``, if text used as a loader, text data within input tag itself used as an input data and parsed by a set of given groups or by all groups.

**Example**

Below template contains data that should be parsed within input itself, that is useful for testing purposes.

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
    
Input parameters
----------------

Apart from input attributes specified in <input> tag, text payload of <input> tag can be used to pass additional parameters. These parameters is a key value pairs and serve to provide information that should be used during input data loading. Input tag `load`_ attribute can be used to specify which loader to use to parse data in tag's text, e.g. if data structured in yaml format, yaml loader can be used to convert it in Python data structure.

.. list-table:: input parameters
   :widths: 10 90
   :header-rows: 1

   * - Parametr
     - Description
   * - `url`_   
     - Single url string or list of urls of input data location 
   * - `extensions`_   
     - Extensions of files to load input data from, e.g. "txt" or "log" or "conf"
   * - `filters`_   
     - Regular expression or list of regexes to use to filter input data files based on their names
     
url
------------------------------------------------------------------------------
``url="url-1"`` or ``url=["url-1", "url-2", ... , "url-N"]``

* url-N - string or list of strings that contains absolute or relative (if base path provided) OS path to file or to directory of file(s) that needs to be parsed.
     
extensions
------------------------------------------------------------------------------
``extensions="extension-1"`` or ``extensions=["extension-1", "extension-2", ... , "extension-N"]``

* extension-N - string or list of strings that contains file extensions that needs to be parsed e.g. txt, log, conf etc. In case if `url`_ is OS path to directory and not single file, ttp will use this strings to check if file names ends with one of given extensions, if so, file will be loaded and skipped otherwise.

filters
------------------------------------------------------------------------------
``filters="regex-1"`` or ``filters=["regex-1", "regex-2", ... , "regex-N"]``

* regex-N - string or list of strings that contains regular expressions. If `url`_ is OS path to directory and not single file, ttp will use this strings to run re search against file names to load only files with names that matched by at least one regex.

**Example**

For instance we have this folders structure to store data that needs to be parsed:
my
|-- base
    |-- path
        |-- Data
            |-- Inputs
                |-- data-1/
                   |-- sw-1.conf
                   |-- sw-1.txt
                |-- data-2/
                   |-- sw-2.txt
                   |-- sw3.txt                       

Where content:

.. code-block::

    [sw-1.conf]
    interface GigabitEthernet3/7
     switchport access vlan 700
    !
    interface GigabitEthernet3/8
     switchport access vlan 800
    !

    [sw-1.txt]
    interface GigabitEthernet3/2
     switchport access vlan 500
    !
    interface GigabitEthernet3/3
     switchport access vlan 600
    !
    
    [sw-2.txt]
    interface Vlan221
      ip address 10.8.14.130/25
    
    interface Vlan223
      ip address 10.10.15.130/25
    
    [sw3.txt]
    interface Vlan220
      ip address 10.9.14.130/24
    
    interface Vlan230
      ip address 10.11.15.130/25

Below template inputs structured in such a way that for "data-1" folder only files that have ".txt" extension will be parsed by group "interfaces1", for input named "dataset-2" only files with names matching given regular expression will be parsed by "interfaces2" group. Alos, base path provided that will be appended to *url* parametres within inputs, moreover, input parameters for "dataset-1" input structured using YAML representation, while "dataset-2" uses python language definition.

As a result of filtering within inputs, only "sw-1.txt" will be matched by "dataset-1" input because it is only file that has ".txt" extension, only  "sw-2.txt" will be matched by input "dataset-2" because "sw3.txt" not matched by "sw\-\d.*" regular expression.

Template

.. code-block:: html

    <template base="/my/base/path/">
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
    
Result

    [
        {
            "interfaces1": [
                {
                    "access_vlan": "500",
                    "interface": "GigabitEthernet3/2"
                },
                {
                    "access_vlan": "600",
                    "interface": "GigabitEthernet3/3"
                }
            ]
        },
        {
            "interfaces2": [
                {
                    "interface": "Vlan221",
                    "ip": "10.8.14.130",
                    "mask": "25"
                },
                {
                    "interface": "Vlan223",
                    "ip": "10.10.15.130",
                    "mask": "25"
                }
            ]
        }
    ]