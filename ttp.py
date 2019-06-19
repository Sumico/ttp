"""
Module to parse structured text data.

Notes:
    version ttp__v1.2.7.8
    to profile the script:
    python -m cProfile -s tottime ttp_v1.0.py

Todo:
    something
"""

import re
import os
import time
import copy
from xml.etree import cElementTree as ET
from multiprocessing import Process, cpu_count, JoinableQueue, Queue

# Initiate global variables:
ctime = time.ctime().replace(':', '-').replace(' ', '_')

"""
==============================================================================
MAIN TTP CLASS
==============================================================================
"""
class ttp():
    """
    Template Text Parser class used to load data and templates as well as
    dispatch data to parser object, construct final results and run outputs

    Args:
        data : text, file object of python open method or a string with
            OS path to either text file or a directory which contains
            .txt, .log or .conf files
        template : text, file object of python open method or a string which is OS
            path to text file
        DEBUG (bool): if True will print debug data to the terminal
        data_path_prefix (str): Contains path prefix to load data from for template inputs
        self.multiproc_threshold (int): overall data size in ytes beyond which to use
            multiple processes
    """
    def __init__(self, data='', template='', DEBUG=False, data_path_prefix=''):
        """
        Args:
            self.data (list): list of dictionaries, each dict key is file name, value - data/text
            self.templates (list): list of template objects
        """
        self.data_size = 0
        self.multiproc_threshold = 5242880 # 5Mbyte
        self.data = []
        self.templates = []
        self.results = []
        self.DEBUG = DEBUG
        self.data_path_prefix = data_path_prefix
        self.utils = ttp_utils()  # initialise utils class object

        # check if data given, if so - load it:
        if data is not '':
            self.add_data(data=data)

        # check if template given, if so - load it
        if template is not '':
            self.add_template(data=template)


    def add_data(self, data, input_name='Default_Input', groups=['all']):
        """Method to load data
        """
        # form a list of ((type, url|text,), input_name, groups,) tuples
        data_items = self.utils.load_files(path=data, read=False)
        if data_items:
            self.data.append((data_items, input_name, groups,))
        else:
            return
        # get data size
        if self.data_size > self.multiproc_threshold:
            return
        for i in data_items:
            if self.data_size < self.multiproc_threshold:
                self.data_size += os.path.getsize(i[1])
            else:
                break


    def add_template(self, data):
        """Method to load templates
        """
        # get a list of [(type, text,)] tuples or empty list []
        items = self.utils.load_files(path=data, read=True)
        [ self.templates.append(template_class(template_text=i[1],
                                DEBUG=self.DEBUG,
                                data_path_prefix=self.data_path_prefix))
          for i in items ]


    def parse(self, one=False, multi=False):
        """Method to decide how to run parsing.
        - if overall data size is less then 5Mbyte, use single process
        - if more then 5Mbytes use multiprocess
        """
        if one is True and multi is True:
            raise SystemExit("ERROR: choose one or multiprocess parsing.")
        elif one is True:
            self.parse_in_one_process()
        elif multi is True:
            self.parse_in_multiprocess()
        elif self.data_size <= self.multiproc_threshold:
            self.parse_in_one_process()
        else:
            self.parse_in_multiprocess()


    def parse_in_multiprocess(self):
        """Method to parse data in bulk by parsing each data item
        against each template and saving results in results list
        """
        num_processes = cpu_count()

        for template in self.templates:
            num_jobs = 0

            if self.data:
                [template.set_input(data=i[0], input_name=i[1], groups=i[2])
                 for i in self.data]

            tasks = JoinableQueue()
            results = Queue()

            workers = [worker(tasks, results, lookups=template.lookups,
                              vars=template.vars, groups=template.groups)
                       for i in range(num_processes)]
            [w.start() for w in workers]

            for input_name, input_params in template.inputs.items():
                for datum in input_params['data']:
                    task_dict = {
                        'data'            : datum,
                        'groups_to_run'   : input_params['groups']
                    }
                    tasks.put(task_dict)
                    num_jobs += 1

            [tasks.put(None) for i in range(num_processes)]

            # wait fo all taksk to complete
            tasks.join()

            for i in range(num_jobs):
                result = results.get()
                self.form_results(result)


    def parse_in_one_process(self):
        """Method to parse data in bulk by parsing each data item
        against each template and saving results in results list
        """
        for template in self.templates:
            parserObj = parser_class(lookups=template.lookups,
                                     vars=template.vars,
                                     groups=template.groups)
            if self.data:
                [template.set_input(data=i[0], input_name=i[1], groups=i[2])
                 for i in self.data]
            for input_name, input_params in template.inputs.items():
                for datum in input_params['data']:
                    parserObj.set_data(datum)
                    parserObj.parse(input_params['groups'])
                    result = parserObj.RSLTSOBJ.RESULTS
                    self.form_results(result)


    def form_results(self, result):
        """Method to add results into self.results
        """
        if not result:
            return
        elif 'non_hierarch_tmplt' in result:
            if isinstance(result['non_hierarch_tmplt'], list):
                self.results += result['non_hierarch_tmplt']
            else:
                self.results += [result['non_hierarch_tmplt']]
        else:
            self.results.append(result)


    def output(self, **kwargs):
        """Method to run templates' outputters.
        kwargs:
            format : supported ['raw', 'yaml', 'json', 'csv', 'jinja2', 'pprint']
            returner : supported ['file', 'terminal']
            url : path where to save files
            filename : name of the file
        """
        # run templates outputs
        for template in self.templates:
            for output in template.outputs:
                output.run(self.results, ret=False)

        # run on demand output with given returner
        if 'format' in kwargs and 'returner' in kwargs:
            outputter = outputter_class(**kwargs)
            outputter.run(self.results, ret=False)
        # run on demand output and return results
        elif 'format' in kwargs and 'returner' not in kwargs:
            outputter = outputter_class(**kwargs)
            result = outputter.run(self.results, ret=True)
            return result


    def result(self):
        return self.results


"""
==============================================================================
TTP PARSER MULTIPROCESSING WORKER
==============================================================================
"""
class worker(Process):
    """Class used in multiprocessing to parse data
    """

    def __init__(self, task_queue, result_queue, lookups, vars, groups):
        Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.parser_obj = parser_class(lookups, vars, groups)

    def run(self):
        while True:
            next_task = self.task_queue.get()
            # check for dead pill to stop process
            if next_task is None:
                self.task_queue.task_done()
                break
            # set parser object parameters
            self.parser_obj.set_data(next_task['data'])
            # parse and get results
            self.parser_obj.parse(next_task['groups_to_run'])
            result = self.parser_obj.RSLTSOBJ.RESULTS
            # put results in the queue and finish task
            self.task_queue.task_done()
            self.result_queue.put(result)
        return




"""
==============================================================================
TTP RE PATTERNS COLLECTION CLASS
==============================================================================
"""
class ttp_patterns():
    def __init__(self):
        self.patterns={
        'phrase'   : '(\S+ {1})+?\S+',
        'orphrase' : '\S+|(\S+ {1})+?\S+',
        'digit'    : '\d+',
        'ip'       : '(?:[0-9]{1,3}\.){3}[0-9]{1,3}',
        'prefix'   : '(?:[0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}',
        'ipv6'     : '(?:[a-fA-F0-9]{1,4}:|:){1,7}(?:[a-fA-F0-9]{1,4}|:?)',
        'prefixv6' : '(?:[a-fA-F0-9]{1,4}:|:){1,7}(?:[a-fA-F0-9]{1,4}|:?)/[0-9]{1,3}',
        '_line_'   : '.+',
        'word'     : '\S+',
        'mac'      : '(?:[0-9a-fA-F]{2}(:|\.)){5}([0-9a-fA-F]{2})|(?:[0-9a-fA-F]{4}(:|\.)){2}([0-9a-fA-F]{4})'
        }




"""
==============================================================================
TTP FUNCTIONS CLASS
==============================================================================
"""
class ttp_functions():
    """Class to store ttp built in functions used for parsing results
    Notes:
        functions to implement
        # 'variable_wrap'        : add \n at given position to wrap long text
        # 'variable_is_ip'        : to check that data is valid ip address - isip(4) for v4 or isip(6) for v6 or any
        # 'variable_is_mac'       : to check that data is valid  mac-address
        # 'variable_is_word'      : check if no spaces in data - same as notcontains(' ')
        # 'variable_is_phrase'    : check if we have spaces in data - same as contains(' ')
        # 'variable_to_ip'        : convert to IP object to do something with it like prefix matching, e.g. check if 1.1.1.1 is part of 1.1.0.0/16
    """
    def __init__(self, parser_obj=None, results_obj=None):
        self.pobj = parser_obj
        self.robj = results_obj

    def invalid(self, name, scope, skip=True):
        if skip == True:
            print("Error: {} function '{}' not found".format(scope, name))
        else:
            print("Error: {} function '{}' not found, valid functions are: \n{}".format(scope, name, getattr(self, scope).keys() ))

    def group_containsall(self, data, *args):
        # args = ('v4address', 'v4mask',)
        for var in args:
            if var in data:
                if var in self.robj.record['DEFAULTS']:
                    if self.robj.record['DEFAULTS'][var] == data[var]:
                        return data, False
                return data, True
            else:
                return data, False

    def group_containsany(self, data, *args):
        # args = ('v4address', 'v4mask',)
        for var in args:
            if var in data:
                if var in self.robj.record['DEFAULTS']:
                    if self.robj.record['DEFAULTS'][var] != data[var]:
                        return data, None
                else:
                    return data, None
        return data, False

    def match_joinmatches(self, data, *args, **kwargs):
        return data, None

    def match_startswith_re(self, data, pattern):
        if re.search('^{}'.format(pattern), data):
            return data, True
        return data, False

    def match_endswith_re(self, data, pattern):
        if re.search('{}$'.format(pattern), data):
            return data, True
        return data, False

    def match_contains_re(self, data, pattern):
        if re.search(pattern, data):
            return data, True
        return data, False

    def match_contains(self, data, pattern):
        if pattern in data:
            return data, True
        return data, False

    def match_notstartswith_re(self, data, pattern):
        if not re.search('^{}'.format(pattern), data):
            return data, True
        return data, False

    def match_notendswith_re(self, data, pattern):
        if not re.search('{}$'.format(pattern), data):
            return data, True
        return data, False

    def match_exclude_re(self, data, pattern):
        if not re.search(pattern, data):
            return data, True
        return data, False

    def match_exclude(self, data, pattern):
        if not pattern in data:
            return data, True
        return data, False

    def match_equal(self, data, value):
        if data == value:
            return data, True
        return data, False

    def match_notequal(self, data, value):
        if data != value:
            return data, True
        return data, False

    def match_notdigit(self, data):
        if not data.strip().isdigit():
            return data, True
        return data, False

    def match_greaterthan(self, data, value):
        if data.strip().isdigit() and value.strip().isdigit():
            if int(data.strip()) > int(value.strip()):
                return data, True
        return data, False

    def match_lessthan(self, data, value):
        if data.strip().isdigit() and value.strip().isdigit():
            if int(data.strip()) < int(value.strip()):
                return data, True
        return data, False

    def match_resub(self, data, old, new):
        return re.sub(old, new, data, count=1), None

    def match_join(self, data, char):
        if isinstance(data, list):
            return char.join(data), None
        else:
            return data, None

    def match_append(self, data, char):
        if isinstance(data, str):
            return (data + char), None
        else:
            return data, None
            
    def match_print(self, data):
        print(data)
        return data, None

    def match_unrange(self, data, rangechar, joinchar):
        """
        data - string, e.g. '8,10-13,20'
        rangechar - e.g. '-' for above string
        joinchar - e.g.',' for above string
        returns - e.g. '8,10,11,12,13,20 string
        """
        result=[]
        # check if range char actually in data:
        if not rangechar in data: return data, None

        for item in data.split(rangechar):
            # form split list checking that i is not empty
            item_split=[i for i in item.split(joinchar) if i]
            if result:
                start_int=int(result[-1])
                end_int=int(item_split[0])
                list_of_ints_range=[str(i) for i in list(range(start_int,end_int))]
                result += list_of_ints_range[1:] + item_split
            else:
                result=item_split
        data = joinchar.join(result)
        return data, None

    def match_set(self, data, value, match_line):
        if data.rstrip() == match_line:
            return value, None
        else:
            return data, False

    def match_replaceall(self, data, *args):
        vars = self.pobj.vars['globals']['vars']
        args = list(args)
        new = ''
        if len(args) > 1: new = args.pop(0)
        for oldValue in args:
            if oldValue in vars:
                if isinstance(vars[oldValue], list):
                    for oldVal in vars[oldValue]:
                        if isinstance(oldVal, str):
                            data = data.replace(oldVal, new)
                elif isinstance(vars[oldValue], dict):
                    for newVal, oldVal in vars[oldValue].items():
                        if isinstance(oldVal, list):
                            for i in oldVal:
                                if isinstance(i, str):
                                    data = data.replace(i, newVal)
                        elif isinstance(oldVal, str):
                            data = data.replace(oldVal, newVal)
            else:
                data = data.replace(oldValue, new)
        return data, None

    def match_resuball(self, data, *args):
        vars = self.pobj.vars['globals']['vars']
        args = list(args)
        new = ''
        if len(args) > 1: new = args.pop(0)
        for oldValue in args:
            if oldValue in vars:
                if isinstance(vars[oldValue], list):
                    for oldVal in vars[oldValue]:
                        if isinstance(oldVal, str):
                            data = re.sub(oldVal, new, data)
                elif isinstance(vars[oldValue], dict):
                    for newVal, oldVal in vars[oldValue].items():
                        if isinstance(oldVal, list):
                            for i in oldVal:
                                if isinstance(i, str):
                                    data = re.sub(i, newVal, data)
                        elif isinstance(oldVal, str):
                            data = re.sub(oldVal, newVal, data)
            else:
                data = re.sub(oldValue, new, data)
        return data, None

    def match_truncate(self, data, truncate):
        d_split=data.split(' ')
        if len(truncate) == 1:
            t_len=int(truncate[0])
            if len(d_split) >= t_len:
                data = ' '.join(d_split[0:t_len])
        return data, None

    def match_record(self, data, record):
        self.pobj.vars['globals']['vars'].update({record: data})
        self.pobj.update_groups_runs({record: data})
        return data, None

    def match_lookup(self, data, name, add_field=False):
        path = [i.strip() for i in name.split('.')]
        found_value = None
        # get lookup dictionary/data:
        try:
            lookup = self.pobj.lookups
            for i in path:
                lookup = lookup.get(i,{})
        except KeyError:
            return D, None
        # perfrom lookup:
        try:
            found_value = lookup[data]
        except KeyError:
            return data, None
        # decide to replace match result or add new field:
        if add_field is not False:
            return data, {'lookup': {add_field: found_value}}
        else:
            return found_value, None

    def match_rlookup(self, data, name, add_field=False):
        path = [i.strip() for i in name.split('.')]
        found_value = None
        # get lookup dictionary/data:
        try:
            rlookup = self.pobj.lookups
            for i in path:
                rlookup = rlookup.get(i,{})
        except KeyError:
            return data, None
        # perfrom rlookup:
        if isinstance(rlookup, dict) is False:
            return data, None
        for key in rlookup.keys():
            if key in data:
                found_value = rlookup[key]
                break
        # decide to replace match result or add new field:
        if found_value is None:
            return data, None
        elif add_field is not False:
            return data, {'lookup': {add_field: found_value}}
        else:
            return found_value, None

    def variable_gethostname(self, data, name, *args, **kwargs):
        """Description: Method to find hostname in show
        command output, uses symbols '# ', '<', '>' to find hostname
        """
        REs = [ # ios-xr prompt re must go before ios exec prompt re
            {'ios_exec': '^\n(\S+)>.*(?=\n)'},   # e.g. 'hostname>'
            {'ios_xr': '^\n\S+:(\S+)#.*(?=\n)'}, # e.g. 'RP/0/4/CPU0:hostname#'
            {'ios_priv': '^\n(\S+)#.*(?=\n)'},   # e.g. 'hostname#'
            {'huawei': '\n\S*<(\S+)>.*(?=\n)'}   # e.g. '<hostname>'
        ]
        for item in REs:
            name, regex = list(item.items())[0]
            match_iter = re.finditer(regex, data)
            try:
                match = next(match_iter)
                return match.group(1)
            except StopIteration:
                continue
        print('Warning: {}, Hostname not found'.format(data))
        return False

    def variable_getfilename(self, data, name, *args, **kwargs):
        """Return dataname
        """
        return name


"""
==============================================================================
TTP UTILITIES CLASS
==============================================================================
"""
class ttp_utils():
    """Class to store various functions for the use along the code
    """
    def __init__(self):
        pass

    def traverse_dict(self, data, path):
        """Method to traverse dictionary data and return dict element
        at given path
        """
        result = {}
        for i in path:
            result = data.get(i, {})
        return result

    def load_files(self, path, extensions=[], filters=[], read=False):
        """
        Method to load files from path, and filter file names with
        REs filters and extensions.
        Args:
            path (str): string that contains OS path
            extensions (list): list of strings files' extensions like ['txt', 'log', 'conf']
            filters (list): list of strings regexes to filter files
            read (bool): if False will return file names, if true will
        Returns:
            List of (type, text_data) tuples or empty list []  if
            read True, if read False return (type, url,) or []
        """
        files=[]
        # check if path is directory
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if os.path.isfile(path + f)]
            if extensions:
                files=[f for f in files if f.split('.')[-1] in extensions]
            for filter in filters:
                files=[f for f in files if re.search(filter, f)]
            if read:
                return [('text_data', open((path + f), 'r', encoding='utf-8').read(),) for f in files]
            else:
                return [('file_name', path + f,) for f in files]
        # check if path is a path to file
        elif os.path.isfile(path):
            if read:
                return [('text_data', open(path, 'r', encoding='utf-8').read(),)]
            else:
                return [('file_name', path,)]
        # check if path is a string:
        elif isinstance(path, str):
            return [('text_data', path,)]
        # check if path is a file object:
        elif hasattr(path, 'read') and hasattr(path, 'name'):
            if read:
                return [('text_data', path.read(),)]
            else:
                return [('file_name', path.name(),)]
        else:
            return []

    def load_struct(self, element, **kwargs):
        """Method to load structured data from element text
        or from file(s) given in include attribute
        Args:
            element (obj): ETree xml tag object
        Returns:
            empy {} dict if nothing found, or python dictionary of loaded
            data from elemnt.text string or from included text files
        """
        format = element.attrib.get('load', 'python').lower()
        include = element.attrib.get('include', '')
        text_data = element.text
        if text_data is None:
            text_data = ''
        result = {}

        def load_text(text_data, kwargs):
            return text_data

        def load_ini(text_data, kwargs):
            import configparser
            data = configparser.ConfigParser()
            # read from ini files first
            if include:
                files = self.load_files(path=include, extensions=[], filters=[], read=False)
                for datum in files:
                    try:
                        data.read(datum[1])
                    except:
                        ("ERROR: Unable to load ini formatted data\n'{}'".format(text_data))
            # read from lookup tag text to make it more specific
            if text_data:
                try:
                    data.read_string(text_data)
                except:
                    ("ERROR: Unable to load ini formatted data\n'{}'".format(text_data))
            # convert configparser object into dictionary
            return {k: dict(data.items(k)) for k in list(data.keys())}

        def load_python(text_data, kwargs):
            data = {}
            if include:
                files = self.load_files(path=include, extensions=[], filters=[], read=True)
                for datum in files:
                    text_data += "\n" + datum[1]
            try:
                exec(compile(text_data, '<string>', 'exec'), {"__builtins__" : None}, data)
                return data
            except:
                print("ERROR: Unable to load Python formatted data\n'{}'".format(text_data))

        def load_yaml(text_data, kwargs):
            from yaml import load
            data = {}
            if include:
                files = self.load_files(path=include, extensions=[], filters=[], read=True)
                for datum in files:
                    text_data += "\n" + datum[1]
            try:
                data = load(text_data)
                return data
            except:
                raise SystemExit("ERROR: Unable to load YAML formatted data\n'{}'".format(text_data))

        def load_json(text_data, kwargs):
            from json import loads
            data = {}
            if include:
                files = self.load_files(path=include, extensions=[], filters=[], read=True)
                for datum in files:
                    text_data += "\n" + datum[1]
            try:
                data = loads(text_data)
                return data
            except:
                raise SystemExit("ERROR: Unable to load YAML formatted data\n'{}'".format(text_data))

        def load_csv(text_data, kwargs):
            from csv import reader
            key = element.attrib.get('key', None)
            data = {}
            headers = []
            for row in reader(iter(text_data.splitlines())):
                if not row:
                    continue
                if not headers:
                    headers = row
                    if not key:
                        key = headers[0]
                    elif key and key not in headers:
                        return data
                    continue
                temp = {headers[index]: i for index, i in enumerate(row)}
                data[temp.pop(key)] = temp
            return data
        # dispatcher:
        funcs = {
            'ini'   : load_ini,
            'python': load_python,
            'yaml'  : load_yaml,
            'json'  : load_json,
            'csv'   : load_csv,
            'text'  : load_text
        }
        # run function to load structured data
        result = funcs[format](text_data, kwargs)
        return result


"""
==============================================================================
TTP TEMPLATE CLASS
==============================================================================
"""
class template_class():
    """Template class to hold template data
    """
    def __init__(self, template_text, DEBUG=False, data_path_prefix=''):
        self.DEBUG=DEBUG
        self.PATHCHAR='.'          # character to separate path items, like ntp.clock.time, '.' is pathChar here
        self.GROUPSTARTED = False
        self.outputs = []
        self.vars = {}
        self.groups = []
        self.inputs = {}
        self.lookups = {}
        self.data_path_prefix = data_path_prefix
        self.utils = ttp_utils()

        # load template from string:
        self.load_template_xml(template_text)

        # update inputs with the groups it has to be run against:
        self.update_inputs_with_groups()

        if self.DEBUG == True:
            from yaml import dump
            print("self.outputs: \n", dump(self.outputs))
            print("self.vars: \n",   dump(self.vars))
            print('self.groups: \n', dump(self.groups))
            print("self.inputs: \n", self.inputs)
            print('self.lookups: \n', self.lookups)


    def set_input(self, data, input_name='Default_Input', groups=['all']):
        """
        Method to set data for default input
        Args:
            data (list): list of (data_name, data_path,) tuples
            input_name (str): name of the input
            groups (list): list of groups to use for that input
        """
        if isinstance(groups, str):
            groups = [groups]
        if input_name not in self.inputs:
            self.inputs[input_name]={'data': data, 'groups': groups}
        else:
            self.inputs[input_name]['data'] += data
            # do not add 'all' to input groups if input was defined already
            # that is needed to allow groups to match based on input attribute
            if groups is not ['all']:
                self.inputs[input_name]['groups'] += groups


    def update_inputs_with_groups(self):
        """
        Method to update self.inputs dictionaries with groups' names
        that will parse this input data
        """
        for G in self.groups:
            # input_name - os path to files to parse
            for input_name in G.inputs:
                if input_name in self.inputs:
                    self.inputs[input_name]['groups'].append(G.name)
                else:
                    input_name = self.data_path_prefix + input_name.lstrip('.')
                    data_items = self.utils.load_files(path=input_name, extensions=[],
                                                       filters=[], read=False)
                    # skip 'text_data' from data as it does not make sense here
                    data = [i for i in data_items if 'text_data' not in i[0]]
                    self.inputs[input_name]={
                        'data'   : data,
                        'groups' : [G.name]
                    }


    def load_template_xml(self, template_text):

        def parse_vars(element):
            # method to parse vars data
           vars = self.utils.load_struct(element)
           if vars:
               self.vars.update(vars)

        def parse_output(element):
            self.outputs.append(outputter_class(element))

        def parse_input(element):
            input_data={}
            file_names=[]

            # load input parameters from text:
            input_data = self.utils.load_struct(element)

            # get parameters:
            name = element.attrib['name']
            extensions = input_data.get('extensions', [])
            filters = input_data.get('filters', [])
            urls = input_data.get('url', [])
            groups = input_data.get('groups', [])

            # run checks:
            if not urls:
                raise SystemExit("ERROR: Input '{}', no 'url' parametr given".format(name))
            if isinstance(extensions, str): extensions=[extensions]
            if isinstance(filters, str): filters=[filters]
            if isinstance(urls, str): urls=[urls]
            if isinstance(groups, str): groups=[groups]

            # load data:
            for url in urls:
                url=self.data_path_prefix + url.lstrip('.')
                file_names += self.utils.load_files(url, extensions, filters, read=False)

            self.inputs[name]={
                'data'   : file_names,
                'groups' : groups
            }

        def parse_group(element):
            self.groups.append(
                group_class(
                    element,
                    top=True,
                    pathchar=self.PATHCHAR,
                    debug=self.DEBUG,
                    vars=self.vars
                )
            )

        def parse_lookup(element):
            try:
                name = element.attrib['name']
            except KeyError:
                print("Error: Lookup 'name' attribute not found but required")
                return
            data = self.utils.load_struct(element)
            if data is None:
                return
            self.lookups[name] = data

        def parse_non_hierarch_tmplt(element):
            elem = ET.XML('<g name="non_hierarch_tmplt">\n{}\n</g>'.format(element.text))
            parse_group(elem)

        def invalid(C):
            print("Warning: Invalid tag '{}'".format(C.tag))

        def parse_hierarch_tmplt(element):
            # dict to store all top tags sorted parsing as need to
            # parse variablse fist after that all the rest
            tags = {
                'vars': [], 'groups': [],
                'inputs': [], 'outputs': [],
                'lookups': []
            }

            # functions to append tag elements to tags dictionary:
            tags_funcs = { # C - child
            'v'         : lambda C: tags['vars'].append(C),
            'vars'      : lambda C: tags['vars'].append(C),
            'variables' : lambda C: tags['vars'].append(C),
            'g'         : lambda C: tags['groups'].append(C),
            'grp'       : lambda C: tags['groups'].append(C),
            'group'     : lambda C: tags['groups'].append(C),
            'o'         : lambda C: tags['outputs'].append(C),
            'out'       : lambda C: tags['outputs'].append(C),
            'output'    : lambda C: tags['outputs'].append(C),
            'i'         : lambda C: tags['inputs'].append(C),
            'in'        : lambda C: tags['inputs'].append(C),
            'input'     : lambda C: tags['inputs'].append(C),
            'lookup'    : lambda C: tags['lookups'].append(C)
            }

            # fill in tags dictionary:
            [tags_funcs.get(child.tag.lower(), invalid)(child)
             for child in list(element)]

            # perform tags parsing:
            [parse_vars(v) for v in tags['vars']]
            [parse_output(o) for o in tags['outputs']]
            [parse_input(i) for i in tags['inputs']]
            [parse_lookup(L) for L in tags['lookups']]
            [parse_group(g) for g in tags['groups']]

        def parse_template_XML(template_text):
            template_ET=ET.XML("<template>\n{}\n</template>".format(template_text))
            if not list(template_ET):
                parse_non_hierarch_tmplt(template_ET)
            else:
                parse_hierarch_tmplt(template_ET)

        parse_template_XML(template_text)



"""
==============================================================================
GROUP CLASS
==============================================================================
"""
class group_class():
    """group class to store template group objects data
    """

    def __init__(self, element, top=False, path=[], pathchar=".",
                 debug=False, vars={}):
        """Init method
        Attributes:
            element : xml ETree element to parse
            top (bool): to indicate that group is a top xml ETree group
            path (list): list containing results tree path, have to copy it otherwise
                it got overriden by recursion
            defaults (dict): contains group variables' default values
            runs (dict): to sotre modified defaults during parsing run
            default (str): group all variables' default value if no more specific default value given
            inputs (list): list of inputs names this group should be used for
            outputs (list): list of outputs, feature not implemnted yet
            funcs (list):vlist of functions to run agaist group results
            method (str): indicate type of the group - [group | table]
            start_re (list): contains list of group start regular epressions
            end_re (list): contains list of group end regular expressions
            children (list): contains child group objects
            vars (dict): variables dictionary from template class
        """
        self.pathchar = pathchar
        self.top      = top
        self.path     = path.copy()
        self.defaults = {}
        self.runs     = {}
        self.default  = "_Not_Given_"
        self.inputs   = []
        self.outputs  = []
        self.funcs    = []
        self.method   = 'group'
        self.start_re = []
        self.end_re   = []
        self.re       = []
        self.children = []
        self.debug    = debug
        self.name     = ''
        self.vars     = vars
        # extract data:
        self.get_attributes(element.attrib)
        self.get_regexes(element.text)
        self.get_children(list(element))

    def get_attributes(self, data):

        def extract_default(O):
            if len(O.strip()) == 0: self.default='None'
            else: self.default=O.strip()

        def extract_method(O):
            self.method=O.lower().strip()

        def extract_input(O):
            if self.top: self.inputs += [(i.strip()) for i in O.split(',')]

        def extract_output(O):
            if self.top: self.outputs += [(i.strip()) for i in O.split(',')]

        def extract_name(O):
            self.path=self.path + O.split(self.pathchar)
            self.name='.'.join(self.path)

        def extract_containsany(O):
            self.funcs.append({
                'name': 'containsany',
                'args': [i.strip() for i in O.split(',')]
            })

        def extract_containsall(O):
            self.funcs.append({
                'name': 'containsall',
                'args': [i.strip() for i in O.split(',')]
            })

        # group attributes extract functions dictionary:
        opt_funcs={
        'containsany' : extract_containsany,
        'containsall' : extract_containsall,
        'method'      : extract_method,
        'input'       : extract_input,
        'output'      : extract_output,
        'name'        : extract_name,
        'default'     : extract_default
        }

        for name, options in data.items():
            if name.lower() in opt_funcs: opt_funcs[name.lower()](options)
            else: print('ERROR: Uncknown group attribute: {}="{}"'.format(name, options))


    def get_regexes(self, data, tail=False):
        varaibles_matches=[] # list of dictionaries
        regexes=[]

        for line in data.splitlines():
            # skip empty lines and comments:
            if not line.strip(): continue
            elif line.startswith('##'): continue
            # parse line against variable regexes
            match=re.findall('{{([\S\s]+?)}}', line)
            if not match:
                print("Warning: Variable not found in line: '{}'".format(line))
                continue
            varaibles_matches.append({'variables': match, 'line': line})

        for i in varaibles_matches:
            regex=''
            variables={}
            action='ADD'
            is_line=False
            skip_regex = False
            for variable in i['variables']:
                variableObj=variable_class(variable, i['line'], DEBUG=self.debug, group=self)

                # check if need to skip appending regex dict to regexes list
                # have to skip it for 'let' function
                if variableObj.skip_regex_dict == True:
                    skip_regex = True
                    break

                # creade variable dict:
                if variableObj.skip_variable_dict is False:
                    variables[variableObj.var_name]=variableObj

                # form regex:
                regex=variableObj.form_regex(regex)

                # check if IS_LINE:
                if is_line == False:
                    is_line=variableObj.IS_LINE

                # modify save action only if it is not START or STARTEMPTY already:
                if "START" not in action:
                    action=variableObj.SAVEACTION

            if skip_regex is True:
                continue

            regexes.append({
                'REGEX'    : re.compile(regex),  # re element
                'VARIABLES': variables,          # Dict of variables objects
                'ACTION'   : action,             # to indicate the save action
                'GROUP'    : self,               # string contains current group object reference
                'IS_LINE'  : is_line             # boolean to indicate _line_ regex
            })

        # form re, start re and end re lists:
        for index, re_dict in enumerate(regexes):
            if tail == True:
                self.re.append(re_dict)
            elif index == 0:
                if not 'START' in re_dict['ACTION']:
                    re_dict['ACTION'] ='START'
                self.start_re.append(re_dict)
            elif self.method == 'table':
                if not 'START' in re_dict['ACTION']:
                    re_dict['ACTION'] = 'START'
                self.start_re.append(re_dict)
            elif "START" in re_dict['ACTION']:
                self.start_re.append(re_dict)
            elif "END" in re_dict['ACTION']:
                self.end_re.append(re_dict)
            else:
                self.re.append(re_dict)


    def get_children(self, child_groups):
        """Method to create child groups objects
        by iterating over all children.
        """
        for g in child_groups:
            self.children.append(group_class(
                element=g,
                top=False,
                path=self.path,
                pathchar=self.pathchar,
                debug=self.debug,
                vars=self.vars))
            # get regexes from tail
            if g.tail.strip():
                self.get_regexes(data=g.tail, tail=True)


    def set_runs(self):
        """runs - default variable values during group
        parsing run, have to preserve original defaults
        as values in defaults dictionried can change for 'let'
        function
        """
        self.runs = self.defaults.copy()
        # run reursion for children:
        [child.set_runs() for child in self.children]


    def update_runs(self, data):
        # func to update runs of the groups using data dictionary
        for k, v in data.items():
            for dk, dv in self.runs.items():
                if dv == k: self.runs[dk]=v
        # run recursion for children:
        [child.update_runs(data) for child in self.children]



"""
==============================================================================
TTP MATCH VARIABLE CLASS
==============================================================================
"""
class variable_class():
    """
    variable class - to define variables and associated actions, conditions, regexes.
    """
    def __init__(self, variable, line, DEBUG=False, group=''):
        """
        Args:
            variable (str): contains variable content
            line(str): original line, need it here to form "set" actions
        """

        # initiate variableClass object variables:
        self.variable = variable
        self.LINE = line                             # original line from template
        self.indent = len(line) - len(line.lstrip()) # variable to store line indentation
        self.functions = []                          # actions and conditions list
        self.DEBUG = DEBUG                           # to control debug behaviuor

        self.SAVEACTION = 'ADD'                      # to store actioan to do with results during saving
        self.group = group                           # template object current group to save some vars
        self.IS_LINE = False                         # to indicate that variable is _line_ regex
        self.skip_variable_dict = False              # will be set to true for 'ignore'
        self.skip_regex_dict = False                 # will be set to true for 'let'
        self.var_res = []                            # list of variable regexes

        # add formatters:
        self.REs = ttp_patterns()

        # form attributes - list of dictionaries:
        self.attributes = self.get_attributes(variable)
        self.var_dict = self.attributes.pop(0)
        self.var_name = self.var_dict['name']

        # add defaults
        # list of variables names that should not have dafaults:
        self.skip_defaults = ["_end_", "_line_", "ignore", "_start_"]
        if self.group.default is not "_Not_Given_":
            if self.var_name not in self.group.defaults:
                if self.var_name not in self.skip_defaults:
                    self.group.defaults.update({self.var_name: self.group.default})

        # perform extractions:
        self.extract_functions()

    def get_args_kwargs(self, *args, **kwargs):
        return {'args': args, 'kwargs': kwargs}

    def get_attributes(self, line):
        """Extract attributes from variable line string.
        Example:
            'peer | orphrase | exclude(-VM-)' -> [{'peer': []}, {'orphrase': []}, {'exclude': ['-VM-']}]
        Args:
            line (str): string that contains variable attributes
        Returns:
            List of dictionaries containing extracted attributes
        """
        RESULT=[]
        ATTRIBUTES=[i.strip() for i in line.split('|')]
        for item in ATTRIBUTES:
            opts = {'args': (), 'kwargs': {}, 'name': ''}
            if not item.strip(): # skip empty items like {{ bla | | bla2 }}
                continue
            # re search attributes like set(), upper, joinchar(',','-')
            itemDict = re.search('^(?P<name>\S+?)\s?(\((?P<options>.*)\))?$', item).groupdict()
            opts['name'] = itemDict['name']
            options = itemDict['options']
            # create options list from options string using eval:
            if options:
                args_kwargs = eval("self.get_args_kwargs({})".format(options))
                opts.update(args_kwargs)
            else:
                options = []
            RESULT.append(opts)
        return RESULT

    def extract_functions(self):
        """Method to extract variable actions and conditions.
        """
        #
        # Helper functions:
        #
        def extract__start_(data):
            self.SAVEACTION='START'
            if self.var_name == '_start_':
                self.SAVEACTION='STARTEMPTY'

        def extract__end_(data):
            self.SAVEACTION='END'

        def extract_set(data):
            match_line=re.sub('{{([\S\s]+?)}}', '', self.LINE).rstrip()
            data['kwargs']['match_line'] = '\n' + match_line
            self.functions.append(data)

        def extract_default(data):
            if self.var_name in self.skip_defaults:
                return
            if len(data['args']) == 1:
                self.group.defaults.update({self.var_name: data['args'][0]})
            else:
                self.group.defaults.update({self.var_name: "None"})

        def extract_joinmatches(data):
            self.functions.append(data)
            self.SAVEACTION='JOIN'

        def extract__line_(data):
            self.functions.append(data)
            self.SAVEACTION='JOIN'
            self.IS_LINE=True

        def extract_let(data):
            self.group.defaults.update({self.var_name: data['args'][0]})
            self.skip_regex_dict = True

        def extract_ignore(data):
            self.skip_variable_dict = True

        def extract_chain(data):
            """add items from chain to variable attributes and functions
            """
            variable_value = self.group.vars.get(data['args'][0], '')
            attributes =  self.get_attributes(variable_value)
            for i in attributes:
                name = i['name']
                if name in extract_funcs:
                    extract_funcs[name](i)
                else:
                    self.functions.append(i)

        extract_funcs = {
        'let'           : extract_let,
        'ignore'        : extract_ignore,
        '_start_'       : extract__start_,
        '_end_'         : extract__end_,
        '_line_'        : extract__line_,
        'chain'         : extract_chain,
        'set'           : extract_set,
        'default'       : extract_default,
        'joinmatches'   : extract_joinmatches,
        # regex formatters:
        're'       : lambda data: self.var_res.append(data['args'][0]),
        'phrase'   : lambda data: self.var_res.append(self.REs.patterns['phrase']),
        'orphrase' : lambda data: self.var_res.append(self.REs.patterns['orphrase']),
        'digit'    : lambda data: self.var_res.append(self.REs.patterns['digit']),
        'ip'       : lambda data: self.var_res.append(self.REs.patterns['ip']),
        'prefix'   : lambda data: self.var_res.append(self.REs.patterns['prefix']),
        'ipv6'     : lambda data: self.var_res.append(self.REs.patterns['ipv6']),
        'prefixv6' : lambda data: self.var_res.append(self.REs.patterns['prefixv6']),
        'mac'      : lambda data: self.var_res.append(self.REs.patterns['mac']),
        'word'     : lambda data: self.var_res.append(self.REs.patterns['word']),
        '_line_'   : lambda data: self.var_res.append(self.REs.patterns['_line_']),
        }

        if self.var_name in extract_funcs:
            extract_funcs[self.var_name](self.var_dict)
        # go over attribute extract function:
        [ extract_funcs[i['name']](i) if i['name'] in extract_funcs
          else self.functions.append(i) for i in self.attributes ]


    def form_regex(self, regex):
        """Method to form regular expression for template line.
        """
        # form escapedVariable:
        esc_var='\\{\\{' + re.escape(self.variable) + '\\}\\}' # escape all special chars in variable like (){}[].* etc.
        if not 'EXACT' in  esc_var.upper():
            esc_var=re.sub('\d+', r'\\d+', esc_var)  # replace all numbers with \d+ in regex in variable, skip it if EXACT in variable
        esc_var=re.sub(r'(\\ )+', r'\\ +', esc_var)  # replace all spaces with  + in regex in variable

        # form escaped line:
        esc_line=re.escape(self.LINE.lstrip())         # escape all special chars in line like (){} [].* etc. and strip leading spaces to preserve indent
        if not 'EXACT' in  esc_line.upper():
            esc_line=re.sub('\d+',r'\\d+', esc_line)   # to replace all numbers with \d+ in regex
        esc_line=re.sub(r'(\\ )+',r'\\ +', esc_line)   # to replace all spaces with  + in regex

        # check if regex empty, if so, make it equal to escaped line, reconstruct indent and add start/end of line:
        if regex == '':
            regex=esc_line
            regex=self.indent * ' ' + regex       # reconstruct indent
            regex='\\n' + regex + ' *(?=\\n)'     # use lookahead assertion for end of line and match any number of leading spaces

        def regex_ignore(data):
            nonlocal regex
            if len(data['args']) == 0:
                regex = regex.replace(esc_var, '\S+', 1)
            elif len(data['args']) == 1:
                regex = regex.replace(esc_var, data['args'][0], 1)

        def regex_deleteVar(data):
            nonlocal regex
            result = None
            if esc_var in regex:
                index = regex.find(esc_var)
                # slice regex string before esc_var start:
                result = regex[:index] 
                # delete "\ +" from end of line and add " *(?=\\n)":
                result = re.sub('(\\\\ \+)$', '', result) + ' *(?=\\n)'
            if result:
                regex = result

        # for variables like {{ _line_ }} or {{ ignore() }}
        regexFuncsVar={
        'ignore'   : regex_ignore,
        '_start_'  : regex_deleteVar,
        '_end_'    : regex_deleteVar
        }
        # for the rest of functions:
        regexFuncs={
        'set'      : regex_deleteVar
        }

        if self.var_name in regexFuncsVar:
            regexFuncsVar[self.var_name](self.var_dict)

        # go over all keywords to form regex:
        [regexFuncs[i['name']](i)
         for i in self.functions if i['name'] in regexFuncs]

        # assign default re if variable without regex formatters:
        if self.var_res == []: self.var_res.append(self.REs.patterns['word'])

        # form variable regex by replacing escaped variable, if it is still in regex:
        regex = regex.replace(esc_var,
            '(?P<{}>(?:{}))'.format(self.var_name, ')|(?:'.join(self.var_res),1)
        )

        # after regexes formed we can delete unneccesary variables:
        if self.DEBUG == False:
            del self.attributes, esc_var, esc_line, self.DEBUG
            del self.LINE, self.skip_defaults, self.indent
            del self.var_dict, self.REs, self.var_res

        return regex



"""
==============================================================================
TTP PARSER OBJECT
==============================================================================
"""
class parser_class():
    """Parser Object to run parsing of data and constructong resulted dictionary/list
    """
    def __init__(self, lookups, vars, groups):
        self.lookups = lookups
        self.original_vars = vars
        self.groups = groups
        self.functions = ttp_functions(parser_obj=self)


    def set_data(self, D):
        """Method to load data and recreate results object
        Args:
            D (tuple): dict of (dataname, data_path,)
        """
        self.raw_results = []            # initiate raw results dictionary
        self.RSLTSOBJ = results_class()  # create results object
        self.DATANAME, self.DATATEXT = self.read_data(D)
        # set vars to original vars and update them based on DATATEXT:
        self.set_vars()


    def read_data(self, D):
        """Method to read data from datafile
        """
        name = ''
        datatext = '\n\n'

        def load_file(D):
            nonlocal name, datatext
            try:
                f = open(D[1], 'r', encoding='utf-8')
                name = f.name
                datatext = '\n' + f.read() + '\n'
            except UnicodeDecodeError:
                print('Warning: Unicode read error, file {}'.format(name))
            finally:
                f.close()

        def load_text(D):
            nonlocal name, datatext
            datatext = '\n' + D[1] + '\n'
            name = 'text_data'

        read_funcs = {
            'file_name': load_file,
            'text_data': load_text
        }
        read_funcs[D[0]](D)
        return (name, datatext,)


    def set_vars(self):
        """Method to load template
        Args:
            vars (dict): template variables dictionary
        """
        self.vars={
            'globals': {
                # need to copy as additional var can be recorded,
                # that can lead to change of original vars dictionary
                'vars' : self.original_vars.copy()
            }
        }
        # run macro functions to update vars with functions results:
        self.run_functions()
        # update groups' runs dictionaries to hold defaults updated with var values
        [G.set_runs() for G in self.groups]
        self.update_groups_runs(self.vars['globals']['vars'])


    def update_groups_runs(self, D):
        """Method to update groups runs dictionaries with new values deirved
        during parsing, can be called from 'record' variable functions
        """
        [G.update_runs(D) for G in self.groups]

    def run_functions(self):
        """Method to run variables functions before parsing data
        """
        for VARname, VARvalue in self.vars['globals']['vars'].items():
            if isinstance(VARvalue, str):
                try:
                    result = getattr(self.functions, 'variable_' + VARvalue)(self.DATATEXT, self.DATANAME)
                    self.vars['globals']['vars'].update({VARname: result})
                except AttributeError:
                    continue


    def parse(self, groups_names):
        # groups_names - list of groups' names to run
        unsort_rslts=[] # list of dictionaries - one item per top group, each dictionary
                        # contains unsorted match results for all res within group

        def check_matches(regex, matches, results, start):
            for match in matches:
                result = {} # dict to store result
                temp = {}

                # check if groupdict present - means regex with no set variables been matchesd
                if match.groupdict():
                    temp = match.groupdict()
                # we have match but no variables - set regex, need to check it as well:
                else:
                    temp = {key: match.group() for key in regex['VARIABLES'].keys()}

                # process matched values
                for var_name, data in temp.items():
                    flags = {}
                    for item in regex['VARIABLES'][var_name].functions:
                        func_name = item['name']
                        args = item['args']
                        kwargs = item['kwargs']
                        try: # try variable function
                            data, flag = getattr(self.functions, 'match_' + func_name)(data, *args, **kwargs)
                        except AttributeError:
                            try: # try data bilt-in finction. e.g. if data is string, can run data.upper()
                                data = getattr(data, func_name)(*args, **kwargs)
                                flag = True
                            except AttributeError as e:
                                flag = False
                                self.functions.invalid(func_name, scope='variable', skip=True)

                        if flag is False:
                            result = False # if flag False - checks produced negative result
                            break
                        elif flag is True:
                            continue    # if checks was successful
                        elif flag:
                            flags.update(flag)

                    if result is False:
                        break

                    result.update({var_name: data})

                    if 'lookup' in flags:
                        result.update(flags['lookup'])

                # skip not start regexes that evaluated to False
                if result is False and not regex['ACTION'].startswith('START'):
                    continue

                # form result dictionary of dictionaries:
                span_start = start + match.span()[0]
                if span_start not in results:
                    results[span_start] = [(regex, result,)]
                else:
                    results[span_start].append((regex, result,))


        def run_re(group, results, start=0, end=-1):
            """Recursive function to run REs
            """
            # results - dict of {span_start: [(re1, match1), (re2, match2)]}
            matched = False  # to indicate if at least one of start res been matched
            s = 0            # int to get the lowest start re span value
            e = -1           # int to get the biggest end re span value

            # run start REs:
            for R in group.start_re:
                matches = list(R['REGEX'].finditer(self.DATATEXT[start:end]))
                if matches:
                    matched = True
                    check_matches(R, matches, results, start)
                    # if s is bigger, make it smaller:
                    if s > matches[0].span()[0] or s == 0:
                        s = matches[0].span()[0]
            start = start + s
            # if no matches found for any start REs of this group - skip the rest of REs
            if not matched:
                # if empty group - tag only, no REs - run children:
                if not group.start_re:
                    # run recursion:
                    [run_re(child_group, results, start, end) for child_group in group.children]
                return {}

            # run end REs:
            for R in group.end_re:
                matches = list(R['REGEX'].finditer(self.DATATEXT[start:end]))
                if matches:
                    check_matches(R, matches, results, start)
                    # if e is smaller, make it bigger
                    if e < matches[-1].span()[1]:
                        e = matches[-1].span()[1]
            if e is not -1:
                end = start + e

            # run normal REs:
            [check_matches(R, list(R['REGEX'].finditer(self.DATATEXT[start:end])),
                results, start) for R in group.re]

            # run recursion:
            [run_re(child_group, results, start, end) for child_group in group.children]

            return results

        [unsort_rslts.append(run_re(group, results={})) for group in self.groups
         if group.name in groups_names or 'all' in groups_names]

        # sort results:
        [ self.raw_results.append(
          [group_result[key] for key in sorted(list(group_result.keys()))]
          )
          for group_result in unsort_rslts if group_result ]

        # import yaml
        # print(yaml.dump(self.raw_results, default_flow_style=False))
        # import pprint
        # pprint.pprint(self.raw_results)

        # save results:
        self.RSLTSOBJ.form_results(self.vars['globals']['vars'], self.raw_results)


"""
==============================================================================
TTP RESULTS FORMATTER OBJECT
==============================================================================
"""
class results_class():
    """
    Class to save results and do actions with them.
    Args:
        self.dyn_path (dict): used to store dynamic path variables
    """
    def __init__(self):
        self.RESULTS = {}
        self.GRPLOCK = {'LOCK': False, 'GROUP': ()} # GROUP - path tuple of locked group
        self.record={
            'RESULT'     : {},
            'PATH'       : [],
            'CONDITIONS' : []
        }
        self.dyn_path={}
        self.functions = ttp_functions(results_obj=self)

    def form_results(self, vars, results):

        self.vars=vars

        saveFuncs={
            'START'      : self.START,       # START - to start new group;
            'ADD'        : self.ADD,         # ADD - to add data to group, defaul-normal action;
            'STARTEMPTY' : self.STARTEMPTY,  # STARTEMPTY - to start new empty group in case if _start_ found;
            'END'        : self.END,         # END - to explicitly signal the end of group to LOCK it;
            'JOIN'       : self.JOIN         # JOIN - to join results for given variable, e.g. joinmatches; 'joinchar' value also must be passed in that case;
        }

        if results: self.RESULTS.update({'vars': vars})

        for group_results in results:
            # clear LOCK between groups as LOCK has intra group significanse only:
            self.GRPLOCK['LOCK'] = False
            self.GRPLOCK['GROUP'] = ()

            for result in group_results:
                # if result been matched by one regex only
                if len(result) == 1:
                    re=result[0][0]
                    result_data=result[0][1]
                # if same results captured by multiple regexes, need to do further descision checks:
                else:
                    for item in result:
                        re=item[0]
                        if re['IS_LINE'] == False:
                            result_data=item[1]
                            break

                group = re['GROUP']

                # check if result is false, lock the group if so:
                if result_data == False:
                    self.GRPLOCK['LOCK']=True
                    self.GRPLOCK['GROUP']=group.path

                # skip results for locked group:
                if self.GRPLOCK['LOCK'] is True:
                    locked_group_path=self.GRPLOCK['GROUP']
                    # skip children of locked group only based on group.path - if group.path starts with locked group group.path
                    # it means that this is a children and we need to skip it except for the case when RSULTHPATH is the same:
                    if group.path[:len(locked_group_path)] == locked_group_path and group.path != locked_group_path:
                        continue
                    # evaluate same level or parents - RSULTHPATH is the same
                    elif re['ACTION'].startswith('START') and result_data is not False:
                        self.GRPLOCK['LOCK'] = False
                        self.GRPLOCK['GROUP'] = ()
                    else:
                        continue

                # Save results:
                saveFuncs[re['ACTION']](
                    RESULT     = result_data,
                    PATH       = group.path.copy(),
                    DEFAULTS   = group.runs,
                    CONDITIONS = group.funcs,
                    REDICT     = re
                )

        # check the last group:
        if self.record['RESULT'] and self.PROCESSGRP() is not False:
            self.SAVE_CURELEMENTS()


    def value_to_list(self, DATA, PATH, RESULT):
        """recursive function to get value at given PATH and transform it into the list
        Example:
            DATA={1:{2:{3:{4:5, 6:7}}}} and PATH=(1,2,3)
            running this function will transform DATA to {1:{2:{3:[{4:5, 6:7}]}}}
        Args:
            DATA (dict): data to add to the DATA
            PATH (list): list of path keys
            RESULT : dict or list that contains results
        Returns:
            transformed DATA with list at given PATH and appended RESULTS to it
        """
        if PATH:
            name=str(PATH[0]).rstrip('*')
            if isinstance(DATA, dict):
                if name in DATA:
                    DATA[name]=self.value_to_list(DATA[name], PATH[1:], RESULT)
                    return DATA
            elif isinstance(DATA, list):
                if name in DATA[-1]:
                    DATA[-1][name]=self.value_to_list(DATA[-1][name], PATH[1:], RESULT)
                    return DATA
        else:
            return [DATA, RESULT] # for resulting list - value at given PATH transformed into list with RESULT appended to it


    def list_to_dict_fwd(self, KEYS):
        """recursive function to build nested dict starting from first element in list - forward order
        Args:
            KEYS (list): list that contains keys
        Returns:
            Nested dictionary
        Example:
            if KEYS=[1,2,3,4], returns {1:{2:{3:{4:{}}}}}, or
            if KEYS=[1,2,3,4*], returns {1:{2:{3:{4:[]}}}}, or
            if KEYS=[1,2,3*,4], returns {1:{2:{3:[{4:{}}]}}}
        """
        if KEYS:                                                  # check if list is not empty:
            name=str(KEYS[0]).rstrip('*')                         # get the name of first item in PATH keys
            if len(KEYS[0]) - len(name) == 1:                     # if one * at the end - make a list
                if len(KEYS) == 1:                                # if KEYS=[1,2,3,4*], returns {1:{2:{3:{4:[{}]}}}}
                    return {name: []}                             # if last item in PATH - return emplty list
                else:                                             # if KEYS=[1,2,3*,4], returns {1:{2:{3:[{4:{}}]}}}
                    return {name: [self.list_to_dict_fwd(KEYS[1:])]}  # run recursion if PATH has more than one element
            else:                                                 # if KEYS=[1,2,3,4], returns {1:{2:{3:{4:{}}}}}
                return {name: self.list_to_dict_fwd(KEYS[1:])}
        return {}                                                 # return empty dict if KEYS list empty


    def dict_by_path(self, PATH, ELEMENT):
        """recursive function to iterate over PATH list and merge it into ELEMENT dict as new keys
        Args:
            PATH (list): list of keys in absolute path format
            ELEMENT: nested list, list of dictionaries or dictionary to get element from
        Returns:
            last element at given PATH of transformed ELEMENT dict
        """
        if PATH == []: return ELEMENT                                # check if PATH is empty, if so - stop and return ELEMENT

        elif isinstance(ELEMENT, dict):
            name = str(PATH[0]).rstrip('*')
            if name in ELEMENT:                                      # check if first element of the list is in ELEMENT
                return self.dict_by_path(PATH[1:], ELEMENT[name])    # run recursion with moving forward in both - PATH and ELEMENT
            else:                                                    # if first element not in dict - we found new key, update it into the dict
                ELEMENT.update(self.list_to_dict_fwd(PATH))          # update new key into the nested dict with value equal to new nested dict branch
                return self.dict_by_path(PATH[1:], ELEMENT[name])    # run recursion to reach element in the PATH

        elif isinstance(ELEMENT, list):
            if ELEMENT == []:
                ELEMENT.append(self.list_to_dict_fwd(PATH))   # check if element list is empty, if so - append empty dict to it
            return self.dict_by_path(PATH, ELEMENT[-1])                     # run recursion with last item in the list


    def SAVE_CURELEMENTS(self):
        """Method to save current group results in self.RESULTS
        """
        RSLT = self.record['RESULT']
        PATH = self.record['PATH']
        # get ELEMENT from self.RESULTS by PATH
        E=self.dict_by_path(PATH=PATH, ELEMENT=self.RESULTS)
        if isinstance(E, list):
            E.append(RSLT)
        elif isinstance(E, dict):
            # check if PATH endswith "**" - update result's ELMENET without converting it into list:
            if len(PATH[-1]) - len(str(PATH[-1]).rstrip('*')) == 2:
                E.update(RSLT)
            # to match all the other cases, like templates without "**" in path:
            elif E != {}:
                # transform ELEMENT dict to list and append data to it:
                self.RESULTS = self.value_to_list(DATA=self.RESULTS, PATH=PATH, RESULT=RSLT)
            else:
                E.update(RSLT)


    def START(self, RESULT, PATH, DEFAULTS={}, CONDITIONS=[], REDICT=''):
        if self.record['RESULT'] and self.PROCESSGRP() != False:
            self.SAVE_CURELEMENTS()
        self.record = {
            'RESULT'     : DEFAULTS.copy(),
            'DEFAULTS'   : DEFAULTS,
            'PATH'       : PATH,
            'CONDITIONS' : copy.deepcopy(CONDITIONS)
        }
        self.record['RESULT'].update(RESULT)


    def STARTEMPTY(self, RESULT, PATH, DEFAULTS={}, CONDITIONS=[], REDICT=''):
        if self.record['RESULT'] and self.PROCESSGRP() != False:
            self.SAVE_CURELEMENTS()
        self.record = {
            'RESULT'     : DEFAULTS.copy(),
            'DEFAULTS'   : DEFAULTS,
            'PATH'       : PATH,
            'CONDITIONS' : copy.deepcopy(CONDITIONS)
        }


    def ADD(self, RESULT, PATH, DEFAULTS={}, CONDITIONS=[], REDICT=''):
        if self.GRPLOCK['LOCK'] == True: return

        if self.record['PATH'] == PATH: # if same path - save into self.record
            self.record['RESULT'].update(RESULT)
        # if different path - that can happen if we have
        # group ended and RESULT actually belong to another group, hence have
        # save directly into RESULTS
        else:
            processed_path = self.form_path(PATH)
            if processed_path is False:
                return
            ELEMENT = self.dict_by_path(PATH=processed_path, ELEMENT=self.RESULTS)
            if isinstance(ELEMENT, dict):
                ELEMENT.update(RESULT)
            elif isinstance(ELEMENT, list):
                ELEMENT[-1].update(RESULT)


    def JOIN(self, RESULT, PATH, DEFAULTS={}, CONDITIONS=[], REDICT=''):
        joinchar = '\n'
        for varname, varvalue in RESULT.items():
            for item in REDICT['VARIABLES'][varname].functions:
                if item['name'] == 'joinmatches':
                    if item['args']:
                        joinchar = item['args'][0]
                        break
        # join results:
        for k in RESULT.keys():
            if k in self.record['RESULT']:                           # if we already have results
                if k in DEFAULTS:
                    if self.record['RESULT'][k] == DEFAULTS[k]:      # check if we have default value
                        self.record['RESULT'][k] = RESULT[k]         # replace default value with new value
                        continue
                if isinstance(self.record['RESULT'][k], str):
                    self.record['RESULT'][k] += joinchar + RESULT[k] # join strings
                elif isinstance(self.record['RESULT'][k], list):
                    self.record['RESULT'][k] += RESULT[k]            # join lists
            else:
                self.record['RESULT'][k] = RESULT[k]                 # if first result


    def END(self, RESULT, PATH, DEFAULTS={}, CONDITIONS=[], REDICT=''):
        # action to end current group by locking it
        self.GRPLOCK['LOCK'] = True
        self.GRPLOCK['GROUP'] = PATH.copy()


    def form_path(self, path):
        """Method to form dynamic path
        """
        for index, item in enumerate(path):
            match=re.findall('{{\s*(\S+)\s*}}', item)
            if not match:
                continue
            for m in match:
                pattern='{{\s*' + m + '\s*}}'
                if m in self.record['RESULT']:
                    self.dyn_path[m] = self.record['RESULT'][m]
                    repl = self.record['RESULT'].pop(m)
                    path[index] = re.sub(pattern, repl, item)
                elif m in self.dyn_path:
                    path[index] = re.sub(pattern, self.dyn_path[m], item)
                elif m in self.vars:
                    path[index] = re.sub(pattern, self.vars[m], item)
                else:
                    return False
        return path


    def PROCESSGRP(self):
        """Method to process group results
        """
        for item in self.record['CONDITIONS']:
            func_name = item['name']
            args = item['args']
            try: # try group function
                self.record['RESULT'], flags = getattr(self.functions, 'group_' + func_name)(self.record['RESULT'], *args)
            except AttributeError:
                flags = False
            # if conditions check been false, return False:
            if flags == False:
                return False

        # check if dynamic path and form it
        processed_path = self.form_path(self.record['PATH'])
        if processed_path:
            self.record['PATH'] = processed_path
        else:
            return False



"""
==============================================================================
TTP OUTPUTTER CLASS
==============================================================================
"""
class outputter_class():
    """Class to serve excel, yaml, json, xml etc. dumping functions
    Args:
        destination (str): if 'file' will save data to file,
            if 'terminal' will print data to terinal
        format (str): output format indicator on how to format data
        url (str): path to where to save data to e.g. OS path
        filename (str): name of hte file
    """
    def __init__(self, element=None, **kwargs):
        self.utils = ttp_utils()
        self.attributes = {
            'returner'    : 'file',
            'format'      : 'json',
            'url'         : './Output/',
            'filename'    : 'output_{}.txt'.format(ctime)
        }
        self.supported_formats = ['raw', 'yaml', 'json',
                                'csv', 'jinja2', 'pprint']
        self.supported_returners = ['file', 'terminal']
        if element is not None:
            self.element = element
            self.attributes.update(element.attrib)
        else:
            self.element = None
            self.attributes.update(kwargs)
        self.name = self.attributes.get('name', None)
        if self.name:
            self.attributes['filename'] = self.name+'_'+self.attributes['filename']

    def run(self, data, ret):
        result = []
        format = self.attributes['format']
        returner = self.attributes['returner']
        if format not in self.supported_formats:
            raise SystemExit("Error: Unsupported output format '{}', Supported: {}. Exiting".format(
                              format, str(self.supported_formats)))
        # construct results on a per-file basis:
        [result.append(getattr(self, 'formatter_' + format)(datum)) for datum in data]
        # decide what to do with results:
        if ret:
            return result
        elif returner in self.supported_returners:
            getattr(self, 'returner_' + returner)(result)
        else:
            raise SystemExit("Error: Unsupported output returner '{}'. Supported: {}. Exiting".format(
                             returner, self.supported_returners))

    def returner_file(self, D):
        url = self.attributes['url']
        filename = self.attributes['filename']
        if not os.path.exists(url):
            os.mkdir(url)
        with open(url + filename, 'a') as f:
            for datum in D:
                f.write(datum)

    def returner_terminal(self, D):
        [print(datum) for datum in D]

    def formatter_raw(self, data):
        """Method returns parsing results as python list or dictionary.
        """
        return data

    def formatter_pprint(self, data):
        """Method to pprint format results
        """
        from pprint import pformat
        return pformat(data, indent=4)

    def formatter_yaml(self, data):
        """Method returns parsing results in yaml format.
        """
        from yaml import dump
        return dump(data, default_flow_style=False)

    def formatter_json(self, data):
        """Method returns parsing result in json format.
        """
        from json import dumps
        return dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

    def formatter_csv(self, data):
        """
        Method to dump list of dictionaries to csv spreadsheet.
        Args:
            dataToDump : List of data to dump
            output_data : Dictionary of {'attributes' : element.attrib, 'data' :
                element.text} extracted from template "outputs" element
        Example:
            <outputs name="IPAM" format="csv" text="python">
            group=["interfaces"]
            headers=["hostname", "Interface", "vrf", "ip", "mask", "description"]
            </outputs>
        """
        import csv
        pass

    def formatter_jinja2(self, data):
        """Method to render output template using results data.
        """
        # load Jinja2:
        try:
            from jinja2 import Environment
        except ImportError:
            raise SystemExit("Jinja2 not installed, install: 'python -m pip install jinja2', exiting")
        # load template:
        template_obj = Environment(loader='BaseLoader', trim_blocks=True,
                                   lstrip_blocks=True).from_string(self.element.text)
        # render data - first argiment is data as is, second argument data assigned to _data,
        # so that _data can be referenced in templates, need it because data can be a dictionary
        # without predefined keys:
        result = template_obj.render(data, _data=data)
        return result



"""
==============================================================================
TTP CLI PROGRAMM
==============================================================================
"""
if __name__ == '__main__':
    import argparse
    try:
        import templates as ts
        templates_exist = True
    except ModuleNotFoundError:
        templates_exist = False

    # form arg parser menu:
    argparser = argparse.ArgumentParser(description="Template Text Parser.",
                               formatter_class=argparse.RawDescriptionHelpFormatter)
    argparser.add_argument('-T', '--Timing', action='store_true', dest='TIMING', default=False, help='Print timing')
    argparser.add_argument('-debug', action='store_true', dest='DEBUG', default=False, help='Print debug information')
    argparser.add_argument('--one', action='store_true', dest='ONE', default=False, help='Parse all in single process')
    argparser.add_argument('--multi', action='store_true', dest='MULTI', default=False, help='Parse multiprocess')
    run_options=argparser.add_argument_group(
        title='run options',
        description='''-d, --data      url        Data files location
-dp, --data-prefix         Prefix to add to template inputs' urls
-t, --template  template   Name of the template in "templates.py"
-o, --outputer  output     Specify output format'''
    )
    run_options.add_argument('-d', '--data', action='store', dest='DATA', default='', type=str, help=argparse.SUPPRESS)
    run_options.add_argument('-dp', '--data-prefix', action='store', dest='data_prefix', default='', type=str, help=argparse.SUPPRESS)
    run_options.add_argument('-t', '--template', action='store', dest='TEMPLATE', default='', type=str, help=argparse.SUPPRESS)
    run_options.add_argument('-o', '--outputter', action='store', dest='output', default='', type=str, help=argparse.SUPPRESS)

    # extract argparser arguments:
    args = argparser.parse_args()
    DATA = args.DATA             # string, OS path to data files to parse
    TEMPLATE = args.TEMPLATE     # string, Template name
    DEBUG = args.DEBUG           # boolean, set debug to true/false
    output = args.output         # string, set output format
    TIMING = args.TIMING         # boolean, enabled timing
    DP = args.data_prefix        # string, to add to templates' inputs' urls
    ONE = args.ONE               # boolean to indicate if run in single process
    MULTI = args.MULTI           # boolean to indicate if run in multi process

    def timing(message):
        if TIMING:
            print(round(time.perf_counter() - t0, 5), message)

    if TIMING:
        t0 = time.perf_counter()
    else:
        t0 = 0

    if templates_exist:
        parser_Obj = ttp(data=DATA, template=vars(ts)[TEMPLATE], DEBUG=DEBUG, data_path_prefix=DP)
    else:
        parser_Obj = ttp(data=DATA, template=TEMPLATE, DEBUG=DEBUG, data_path_prefix=DP)
    timing("Template and data descriptors loaded")

    parser_Obj.parse(one=ONE, multi=MULTI)
    timing("Data parsing finished")

    parser_Obj.output()
    timing("Data output done")

    if output.lower() == 'yaml':
        parser_Obj.output(format='yaml', returner='terminal')
        timing("YAML dumped")
    elif output.lower() == 'raw':
        parser_Obj.output(format='raw', returner='terminal')
        timing("RAW dumped")
    elif output.lower() == 'json':
        parser_Obj.output(format='json', returner='terminal')
        timing("JSON dumped")
    elif output.lower() == 'pprint':
        parser_Obj.output(format='pprint', returner='terminal')
        timing("RAW pprint dumped")
    elif output:
        print("Error: Unsuported output format '{}', supported [yaml, json, raw, pprint]".format(output.lower()))

    timing("Done")