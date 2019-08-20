Variables
=========
   
ttp supports definition of custom variables using dedicated xml tags <v>, <vars> or <variables>. Withing this tags variables can be defined in various formats and loaded using one of supported loaders. Variables can also be defined in external text files using *include* attribute. 

Custom variables can be used in a number of places within the templates, primarily in match variable functions, to store data off the groups definitions.

Data can also be recorded in variables during parsing and referenced later to construct dynamic path or within variables functions.

Variable tag attributes
-----------------------

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Attribute
     - Description
   * - `name`_   
     - String of dot-separated path items
   * - `load`_   
     - Indicates which loader to use to read tag data, default is *python*
   * - `include`_   
     - Specifies location of the file with variables data to load`_
	

load
------------------------------------------------------------------------------
``load="loader_name"``	

* loader_name (optional) - name of the loader to use to render supplied variables data

Supported loaders:

* python - default, uses python *exec* method to load data structured in native Python formats
* yaml - relies on PyYAML to load YAML structured data
* json - used to load json formatted variables data
* ini - *configparser* Python standart module used to read variables from ini structured file
* csv - csv formatted data loaded with Python *csv* standart library module

**Example**

Template
::
    <input load="text">
    interface GigabitEthernet1/1
     ip address 192.168.123.1 255.255.255.0
    !
    </input>
    
    <!--Python formatted variables data-->
    <vars name="vars">
    python_domains = ['.lab.local', '.static.on.net', '.abc']
    </vars>
    
    <!--YAML formatted variables data-->
    <vars load="yaml" name="vars">
    yaml_domains:
      - '.lab.local'
      - '.static.on.net'
      - '.abc'
    </vars>
    
    <!--Json formatted variables data-->
    <vars load="json" name="vars">
    {
        "json_domains": [
            ".lab.local",
            ".static.on.net",
            ".abc"
        ]
    }
    </vars>
    
    <!--INI formatted variables data-->
    <variables load="ini" name="vars">
    [ini_domains]
    1: '.lab.local'
    2: '.static.on.net'
    3: '.abc'
    </variables>
    
    <!--CSV formatted variables data-->
    <variables load="csv" name="vars.csv">
    id, domain
    1,  .lab.local
    2,  .static.on.net
    3,  .abc
    </variables>
    
    <group name="interfaces">
    interface {{ interface }}
     ip address {{ ip }} {{ mask }}	
    </group>
	
Result as displayed by Python pprint outputter
::
    [   {   'interfaces': {   'interface': 'GigabitEthernet1/1',
                              'ip': '192.168.123.1',
                              'mask': '255.255.255.0'},
            'vars': {   'csv_data': {   '1': {' domain': '  .lab.local'},
                                        '2': {' domain': '  .static.on.net'},
                                        '3': {' domain': '  .abc'}},
                        'ini_data': {   '1': "'.lab.local'",
                                        '2': "'.static.on.net'",
                                        '3': "'.abc'"},
                        'json_data': ['.lab.local', '.static.on.net', '.abc'],
                        'python_data': ['.lab.local', '.static.on.net', '.abc'],
                        'yaml_data': ['.lab.local', '.static.on.net', '.abc']}}]
						
YAML, JSON and Python formats are suitalble for encoding any arbitrary data and loaded as is.

INI structured data loaded into python nested dictionary, where top level keys represent ini section names each havin nested dictionary of variables. 

CSV data also transformed into dictionary using first column values to fill in dictionary keys, unless specified otherwise using *key* attribute