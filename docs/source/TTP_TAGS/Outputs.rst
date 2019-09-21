Outputs
=======

Outputs system allows to process parsing results, format them in certain way and return results to various destination. For instance, using yaml formatter results can take a form of YAML syntax and using file returner these results can be saved into file.

Outputs can be chained, say results after passing through first outputter will serve as an input for next outputter. That allows to implement complex processing logic of results produced by ttp.

The opposite way would be that each output defined in template will work with parsing results, transform them in different way and return to different destinations. An example of such a behavior might be the case when first outputter form csv table and saves it onto the file, while second outputter will render results with Jinja2 template and print them to the screen.

In addition two types of outputter exists - template specific and group specific. Template specific outputs will process template overall results, while group-specific will work with results of this particular group only.

There is a set of function available in outputs to process/modify results further.

.. note:: If several outputs provided - they run sequentially in the order defined in template. Within single output, processing order is - functions run first, after that formatters, followed by returners. 

There are a number of attributes that outputs system can use. Some attribute can be specific to output itself (name, description), others can be used by formatters or returners. 

Output attributes
-----------------

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Name
     - Description
   * - `name`_ 
     - name of the output, can be referenced in group *output* attribute
   * - `description`_ 
     - attribute to contain description of outputter
   * - `load`_ 
     - name of the loader to use to load output tag text
   * - `returner`_ 
     - returner to use to return data e.g. self, file, terminal
   * - `format`_ 
     - formatter to use to format results
   * - `functions`_ 
     - pipe separated list of functions to run results through         

name
******************************************************************************
``name="output_name"``

Name of the output, optional attribute, can be used to reference it in groups :ref:`Groups/Attributes:output` attribute, in that case that output will become group specific and will only process results for this group. 

description
******************************************************************************
``name="descrition_string"``

descrition_string, optional string that contains output description or notes, can serve documentation purposes.

load
******************************************************************************
``load="loader_name"``    

Name of the loader to use to render supplied output tag text data, default is python.

Supported loaders:

* python - uses python `exec <https://docs.python.org/3/library/functions.html#exec>`_ method to load data structured in native Python formats
* yaml - relies on `PyYAML <https://pyyaml.org/>`_ to load YAML structured data
* json - used to load JSON formatted variables data
* ini - `configparser <https://docs.python.org/3/library/configparser.html>`_ Python standard module used to read variables from ini structured file
* csv - csv formatted data loaded with Python *csv* standard library module

If load is csv, first column by default will be used to create lookup dictionary, it is possible to supply `key`_ with column name that should be used as a keys for row data. If any other type of load provided e.g. python or yaml, that data must have a dictionary structure, there keys will be compared against match result and on success data associated with given key will be included in results.
     
returner
******************************************************************************
``returner=returner_name"``    

Name of the returner to use to return results.

format
******************************************************************************
``format=formatter_name"``    

Name of the formatter to use to format results.

functions
******************************************************************************
``functions="function1('attributes') | function2('attributes') | ... | functionN('attributes')"``

* functionN - name of the output function together with it's attributes

String, that contains pipe separated list of output functions with functions' attributes

Output Functions
------------------------------------------------------------------------------

Output system provide support for a number of functions. Functions process output results first with intention to modify or check overall data in certain way.

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Name
     - Description
   * - `is_equal`_ 
     - checks if results equal to structure loaded from the output tag text 
   * - `set_data`_
     - insert arbitrary data to results at given path, replacing any existing results
   * - `dict_to_list`_
     - transforms dictionary to list of dictionaries at given path     
     
is_equal
******************************************************************************
``functions="is_equal"``

Function is_equal load output tag text data into python structure (list, dictionary etc.) using given loader and performs comparison with parsing results. is equal returns a dictionary of three elements::

    {
        "is_equal": true|false,
        "output_description": "output description as set in description attribute",
        "output_name": "name of the output"
    } 
    
This function use-cases are various tests or compliance checks, one can construct a set of template groups to produce results, these results can be compared with predefined structures to check if they are matching, based on comparison a conclusion can be made such as whether or not source data satisfies certain criteria.

**Example**

Template::

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
    
Results::

    {
        "is_equal": true,
        "output_description": "test results equality",
        "output_name": "test output 1"
    }
  
set_data
******************************************************************************

TBD
  
dict_to_list
******************************************************************************

TBD

Output Returners
------------------------------------------------------------------------------
     
TTP has `file`_, `terminal`_ and `self`_ returners. The purpose of returner is to return data to certain destination in a certain way.
  
self
******************************************************************************

Default returner, data processed by output returned back to ttp for further processing, that way outputs can be chained to produce required results. Another use case is when ttp used as a module, results can be formatted retrieved out of ttp object.

file
******************************************************************************

Results will be saved to text file on local file system. One file will be produced per template to contain all the results for all the inputs and groups of this template.

terminal
******************************************************************************

Results will be printed to terminal window.

Returner attributes
******************************************************************************

.. list-table::
   :widths: 10 10 80
   :header-rows: 1
   
   * - Returner
     - Attribute
     - Description   
     
   * - file
     - `url`_
     - OS path to folder there to save results
   * - file
     - `filename`_ 
     - name of the file to save data in  
     
url
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If returner is file - url attribute helps to specify full OS path to folder where file should be stored.

filename
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If returner is file - filename specifies the name of the file to save data in. Filename attribute support a number of formatters.

Time filename formatters::

   * ``%m``  Month as a decimal number [01,12].
   * ``%d``  Day of the month as a decimal number [01,31].
   * ``%H``  Hour (24-hour clock) as a decimal number [00,23].
   * ``%M``  Minute as a decimal number [00,59].
   * ``%S``  Second as a decimal number [00,61].
   * ``%z``  Time zone offset from UTC.
   * ``%a``  Locale's abbreviated weekday name.
   * ``%A``  Locale's full weekday name.
   * ``%b``  Locale's abbreviated month name.
   * ``%B``  Locale's full month name.
   * ``%c``  Locale's appropriate date and time representation.
   * ``%I``  Hour (12-hour clock) as a decimal number [01,12].
   * ``%p``  Locale's equivalent of either AM or PM. 
   
For instance, filename="OUT_%Y-%m-%d_%H-%M-%S_results.txt" will be rendered to "OUT_2019-09-09_18-19-58_results.txt" filename. By default filename is set to "output_<ctime>.txt", where "ctime" is a string produced after rendering "%Y-%m-%d_%H-%M-%S" by python `time.strftime() <https://docs.python.org/3/library/time.html#time.strftime>`_ function.
     
Output Formatters
------------------------------------------------------------------------------

TTP supports `raw`_, `yaml`_, `json`_, `csv`_, `jinja2`_, `pprint`_, `tabulate`_, `table`_, `excel`_ formatters. Formatters have a number of attributes that can be used to supply additional information or modify behavior. 

In general case formatters take python structured data - dictionary, list, list of dictionaries etc. - as an input, format that data in certain way and return string representation of results, except for `raw`_ output formatter, which just returns input data without modifying it.

raw
******************************************************************************

If format is raw, no formatting will be applied and native python structure will be returned, results will not be converted to string.

yaml
******************************************************************************

**Prerequisites**: Python PyYAML library needs to be installed

This formatter will run results through PyYAML module to produce YAML structured results.

JSON
******************************************************************************

This formatter will run results through Python built-in JSON module ``dumps`` method to produce `JSON (JavaScript Object Notation) <http://json.org>` structured results. 

.. note:: json.dumps() will have these additional attributes set ``sort_keys=True, indent=4, separators=(',', ': ')``

pprint
******************************************************************************

As the name implies, python built-in pprint module will be used to structure python data in a more readable.

table
******************************************************************************

This formatter will transform results into a list of lists, where first list item will represent table headers, all the rest of items will represent table rows. 

For table formatter to work correctly, results data should have certain structure, namely:

* list of flat dictionaries 
* single flat dictionary
* dictionary of flat dictionaries if `key`_ attribute provided

Flat dictionary - such a dictionary where all values are strings. It is not a limitation and in fact dictionary values can be of any structure, but they will be placed in table as is.

**Example**

Template::

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
    
    <output format="pprint" returner="terminal"/>
    
    <output format="table" returner="terminal"/>

Results::

    First output will print to terminal, after passing results through pprint function:
    [   [   {'interface': 'Loopback0', 'ip': '192.168.0.113', 'mask': '24'},
            {'interface': 'Vlan778', 'ip': '2002::fd37', 'mask': '124'}],
        [   {'interface': 'Loopback10', 'ip': '192.168.0.10', 'mask': '24'},
            {'interface': 'Vlan710', 'ip': '2002::fd10', 'mask': '124'}]]
            
    Above data will serve as an input to second outputter, that outputter 
    will format data in table list of lists:
    [['interface', 'ip', 'mask'], 
    ['Loopback0', '192.168.0.113', '24'], 
    ['Vlan778', '2002::fd37', '124'], 
    ['Loopback10', '192.168.0.10', '24'], 
    ['Vlan710', '2002::fd10', '124']]

.. note:: csv and tabulate outputters use table outputter to construct a list of lists, after that they use it to represent data in certain format. Meaning all the attributes supported by table outputter, inherently supported by csv and tabulate outputters.

csv
******************************************************************************

This outputter takes parsing result as an input, transforms it in list of lists using table outputter and emits csv structured table.

**Example**

Template::

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
    
Results::

    interface,ip,mask
    Loopback0,192.168.0.113,24
    Vlan778,2002::fd37,124

tabulate
******************************************************************************

**Prerequisites:** `tabulate <https://pypi.org/project/tabulate/>`_ module needs to be installed on the system.

Tabulate outputter uses python tabulate module to transform and emit results in a plain-text table.

**Example**

Template::

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
    
Results::

    interface    ip               mask
    -----------  -------------  ------
    Loopback0    192.168.0.113      24
    Vlan778      2002::fd37        124

jinja2
******************************************************************************

**Prerequisites:** `Jinja2 <https://palletsprojects.com/p/jinja/>`_ module needs to be installed on the system

This outputters allow to render parsing results with jinja2 template. Jinja2 template can be enclosed in output tag text data. Jinja2 templates can help to produce any text output out of parsing results. There are lots of use cases for it, to name a few:

* vendor configuration translator - parse vendor A configuration, emit configuration for vendor B
* markdown - use Jinja2 template to produce markdown report etc.

Within jinja2, the whole parsing results data passed into the renderer within `_data_` variable, that variable can be referenced in template accordingly.

**Example**

Template::

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
    
Results::

    if_cfg id Loopback0
        ip address 192.168.0.113
        subnet mask 24
    #
    if_cfg id Vlan778
        ip address 2002::fd37
        subnet mask 124
    #
    if_cfg id Loopback10
        ip address 192.168.0.10
        subnet mask 24
    #
    if_cfg id Vlan710
        ip address 2002::fd10
        subnet mask 124
    #
    
excel
******************************************************************************

**Prerequisites:** `openpyxl <https://openpyxl.readthedocs.io/en/stable/#>`_ module needs to be installed on the system

This formatter takes table structure defined in output tag text and transforms parsing results into table on a per tab basis using `table`_ formatter, as a results all attributes supported by table formatter can be used in excel formatter as well. 

**Example**

Template::

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
    filename="excel_out_%Y-%m-%d_%H-%M-%S"
    url="C:/result/"
    load="yaml"
    >
    table:
      - headers: interface, ip, mask, vrf, description
        path: interfaces_1
        tab_name: tab-1
      - path: interfaces_2
        tab_name: tab-2
    </output>
    
TTP will produce excel table with two tabs using results from different groups. Table will be saved under *C:/result/* path in *excel_out_%Y-%m-%d_%H-%M-%S.xslx* file.
    
Formatter attributes
******************************************************************************

.. list-table::
   :widths: 30 10 60
   :header-rows: 1
   
   * - Formatter
     - Attribute
     - Description  
   * - table, csv, tabulate, excel 
     - `path`_ 
     - dot separated string that denotes path to data within results tree
   * - tabulate
     - `format_attributes`_ 
     - string of `*args`, `**kwargs` to pass to formatter
   * - table, csv, tabulate, excel
     - `headers`_    
     - comma separated string of table headers    
   * - csv
     - `sep`_ 
     - character to separate items, by default it is comma
   * - table, csv, tabulate, excel
     - `missing`_ 
     - string to replace missing items based on provided headers
   * - table, csv, tabulate, excel
     - `key`_ 
     - string to use while flattening dictionary of data results


path
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``path="path_to_data"``  

* path_to_data - dot separated string of path items within results tree, used to specify location of data to work with.

In the case when results data is a nested structure and we want to output only part of it in a certain format, path attribute can be used to identify the portion of results to work with.

**Supported by:** table, csv, tabulate output formatters

**Example**

In this example we want to emit BGP peers in a table format, however, list of peer dictionaries is nested within results tree behind *bgp_config* and *peers* sections. We can set `path` to `bgp_config.peers` value to reference required data and pass it through output formatter, in this case csv. 

Template::

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
    
    <output name="out2" path="bgp_config.peers" format="csv" returner="terminal"/>
    
Results::

    [   {   'bgp_config': {   'bgp_as': '65100',
                              'peers': [   {   'description': 'vic-mel-core1',
                                               'peer': '10.145.1.9'},
                                           {   'description': 'qld-bri-core1',
                                               'peer': '192.168.101.1'}]}}]
    description,peer
    vic-mel-core1,10.145.1.9
    qld-bri-core1,192.168.101.1
    
Outputter *out1* will emit data in native python format but structured by pprint for ease of read, while outputter `out2` will format peers data in a table using tabulate formatter. Returner *terminal* will print results to command line screen.

format_attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``format_attributes="**args, **kwargs"``

* args - list of attribute values e.g. `value1, value2, value3`, to pass to formatter
* kwargs - list of attribute name-value pairs e.g. `key1=value1, key2-value2`, to pass to formatter

**Supported by**: tabulate output formatter

Some outputters can be invoked with a number of additional arguments to modify their behavior, this arguments can be passed to them using *format_attributes* attribute.

**Example**

Tabulate outputter supports a number of table formates that can be specified using `tablefmt` argument, in below template data will be formatted using tabulate formatter with tabulate table format set to `fancy_grid` and results will be printer to terminal screen.

Template::

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
        
    <output name="out2" path="bgp_config.peers" format="csv" 
    returner="terminal" format_attributes="tablefmt='fancy_grid'"/>
    
Results::

    ╒═══════════════╤═══════════════╕
    │ description   │ peer          │
    ╞═══════════════╪═══════════════╡
    │ vic-mel-core1 │ 10.145.1.9    │
    ├───────────────┼───────────────┤
    │ qld-bri-core1 │ 192.168.101.1 │
    ╘═══════════════╧═══════════════╛
    
headers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``headers="header1, header2, ... headerN"``  

* headers - comma separated string of table headers

Table formatter will identify the list of headers automatically, however, their order will be undefined and can change. To solve that problem, predefined list of headers can be supplied to formatter. Headers have to match key names of the results dictionaries and they are case sensitive.

**Supported by:** table, csv, tabulate output formatters

**Example**

Template::

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

Results::

    interface    description         vrf    ip               mask
    -----------  ------------------  -----  -------------  ------
    Loopback0    Router-id-loopback         192.168.0.113      24
    Vlan778      CPE_Acces_Vlan      CPE1   2002::fd37        124
    
sep
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``sep="char"``  

* char - separator character to use for csv formatter, default value is comma ","

**Supported by:** csv output formatter

missing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``missing="value"``  

* value - string to use to substitute empty cells in table, default is empty - ""

**Supported by:** table, csv, tabulate output formatters

**Example**

Template::

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
    
Results::

    description         interface    ip               mask  vrf
    ------------------  -----------  -------------  ------  ---------
    Router-id-loopback  Loopback0    192.168.0.113      24  UNDEFINED
    UNDEFINED           Vlan778      2002::fd37        124  CPE1
    
key
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``key="name"``

* name - name of the key to use in a dictionary to associate data value

This attribute helps to solve specific problem when results data is a dictionary of dictionaries similar to this::

    {
        "Loopback0": {
            "description": "Router-id-loopback",
            "ip": "192.168.0.113",
            "mask": "24"
        },
        "Vlan778": {
            "ip": "2002::fd37",
            "mask": "124",
            "vrf": "CPE1"
        }
    }
    
If ``key`` will be set to "intf_name", above data will be transformed into list of dictionaries such as::

    [
        {
            "intf_name": "Loopback0",
            "description": "Router-id-loopback",
            "ip": "192.168.0.113",
            "mask": "24"
        },
        {
            "intf_name": "Vlan778",
            "ip": "2002::fd37",
            "mask": "124",
            "vrf": "CPE1"
        }
    ]

With that list of lists table formatter will be able to create below list of lists and emit it in desirable format (csv, tabulate)::
    
    [
    ['description', 'intf_name', 'ip', 'mask', 'vrf'], 
    ['Router-id-loopback', 'Loopback0', '192.168.0.113', '24', ''], 
    ['', 'Vlan778', '2002::fd37', '124', 'CPE1']
    ]
    
**Example**

Template::

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
     description {{ description }}
     ip vrf {{ vrf }}
    </group>
    
    <output 
    format="tabulate" 
    returner="terminal"
    key="intf_name"
    />
    
Results::

    description         intf_name    ip               mask  vrf
    ------------------  -----------  -------------  ------  -----
    Router-id-loopback  Loopback0    192.168.0.113      24
                        Vlan778      2002::fd37        124  CPE1