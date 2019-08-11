# -*- coding: utf-8 -*-
"""
Template Text Parser

Module to parse semi-structured text data.
"""
# compatibility with python2.6:
# from __future__ import print_function

__version__ = '0.0.0'

import re
import os
import time
from xml.etree import cElementTree as ET
from multiprocessing import Process, cpu_count, JoinableQueue, Queue
from sys import version_info

# get version of python running the script:
python_major_version = version_info.major

# Initiate global variables:
ctime = time.ctime().replace(':', '-').replace(' ', '_')

"""
==============================================================================
MAIN TTP CLASS
==============================================================================
"""
class ttp():
    """
    Template Text Parser main class to load data, templates and
    dispatch data to parser object, parse the data, construct final results
    and run outputs.

    Args:
        data : text, file object or string - OS path to either text file or
            directory which contains .txt, .log or .conf files
        template : text, file object of python open method or a string which is OS
            path to text file
        DEBUG (bool): if True will print debug data to the terminal
        data_path_prefix (str): Contains path prefix to load data from for template inputs
        self.multiproc_threshold (int): overall data size in bytes beyond which to use
            multiple processes
    """
    def __init__(self, data='', template='', DEBUG=False, data_path_prefix='', vars={}):
        """
        Args:
            self.__data (list): list of dictionaries, each dict key is file name, value - data/text
            self.__templates (list): list of template objects
        """
        self.__data_size = 0
        self.__data = []
        self.__templates = []
        self.__utils = _ttp_utils()
        self.DEBUG = DEBUG
        self.data_path_prefix = data_path_prefix
        self.multiproc_threshold = 5242880 # 5Mbyte
        self.vars = vars # dictionary of variables to add to each template vars
        self.lookups = {}

        # check if data given, if so - load it:
        if data is not '':
            self.add_data(data=data)

        # check if template given, if so - load it
        if template is not '':
            self.add_template(data=template)
            
    def add_lookup(self, name, text_data, include=None, load="python", key=None):
        """Method to load lookup table data
        Args::
            name(str): name of lookup table to reference in templates
            text_data(str): text to load lookup table from
            include(str): os/path/to/lookup/table/text
            load(str): name of loader to use to load table data
            key(str): used for csv loader to specify key collumn
        """
        lookup_data = self.__utils.load_struct(text_data=text_data,
            include=include, load=load, key=key)
        self.lookups.update({name: lookup_data})
        [template.add_lookup({name: lookup_data}) for template in self.__templates]

    def add_vars(self, data):
        """Method to add vars to ttp and its templates
        """
        if isinstance(data, dict):
            self.vars.update(data)
            [template.add_vars(data) for template in self.__templates]
            

    def add_data(self, data, input_name='Default_Input', groups=['all']):
        """Method to load data
        """
        # form a list of ((type, url|text,), input_name, groups,) tuples
        data_items = self.__utils.load_files(path=data, read=False)
        if data_items:
            self.__data.append((data_items, input_name, groups,))
        else:
            return
        # get data size
        if self.__data_size > self.multiproc_threshold:
            return
        for i in data_items:
            if self.__data_size < self.multiproc_threshold:
                if i[0] == "file_name":
                    self.__data_size += os.path.getsize(i[1])
            else:
                break


    def add_template(self, data):
        """Method to load templates
        """
        # get a list of [(type, text,)] tuples or empty list []
        items = self.__utils.load_files(path=data, read=True)
        for i in items:
            template_obj = _template_class(
                template_text=i[1],
                DEBUG=self.DEBUG,
                data_path_prefix=self.data_path_prefix, 
                ttp_vars=self.vars)
            # if templates are empty - no 'template' tags in template:
            if template_obj.templates == []:
                self.__templates.append(template_obj)
            else:
                self.__templates += template_obj.templates


    def parse(self, one=False, multi=False):
        """Method to decide how to run parsing following below rules:
        1. if one or multi set to True run in one- or multiprocess
        2. if overall data size is less then 5Mbyte, use single process
        3. if overall data size is more then 5Mbytes use multiprocess
        Args:
            one (bool): if set to true will run parsing in single process
            multi (bool): if set to true will run parsing in multiprocess
        """
        if one is True and multi is True:
            raise SystemExit("ERROR: choose one or multiprocess parsing.")
        elif one is True:
            self.__parse_in_one_process()
        elif multi is True:
            self.__parse_in_multiprocess()
        elif self.__data_size <= self.multiproc_threshold:
            self.__parse_in_one_process()
        else:
            self.__parse_in_multiprocess()
        # run outputters defined in templates
        self.__run_outputs()


    def __parse_in_multiprocess(self):
        """Method to parse data in bulk by parsing each data item
        against each template and saving results in results list
        """
        num_processes = cpu_count()

        for template in self.__templates:
            num_jobs = 0

            if self.__data:
                [template.set_input(data=i[0], input_name=i[1], groups=i[2])
                 for i in self.__data]

            tasks = JoinableQueue()
            results_queue = Queue()

            workers = [_worker(tasks, results_queue, lookups=template.lookups,
                              vars=template.vars, groups=template.groups, 
                              macro=template.macro)
                       for i in range(num_processes)]
            [w.start() for w in workers]

            for input_name, input_params in template.inputs.items():
                for datum in input_params['data']:
                    task_dict = {
                        'data'          : datum,
                        'groups_to_run' : input_params['groups']
                    }
                    tasks.put(task_dict)
                    num_jobs += 1

            [tasks.put(None) for i in range(num_processes)]

            # wait fo all taksk to complete
            tasks.join()

            for i in range(num_jobs):
                result = results_queue.get()
                template.form_results(result)


    def __parse_in_one_process(self):
        """Method to parse data in bulk by parsing each data item
        against each template and saving results in results list
        """
        for template in self.__templates:
            parserObj = _parser_class(lookups=template.lookups,
                                     vars=template.vars,
                                     groups=template.groups,
                                     macro=template.macro)
            if self.__data:
                [template.set_input(data=i[0], input_name=i[1], groups=i[2])
                 for i in self.__data]
            for input_name, input_params in template.inputs.items():
                for datum in input_params['data']:
                    parserObj.set_data(datum)
                    parserObj.parse(groups_names=input_params['groups'])
                    result = parserObj.results
                    template.form_results(result)


    def __run_outputs(self):
        """Method to run templates' outputters.
        """
        [template.run_outputs() for template in self.__templates]


    def result(self, templates=[], returner='self', **kwargs):
        """
        Args:
            templates (list|str): names of the templates to return results for
            returner (str): if 'self', results will be returned, else given returner will
                be used to return results to
        kwargs:
            returner : supported ['file', 'terminal']
        """
        # filter templates to run outputs for:
        templates_obj = self.__templates
        if isinstance(templates, str):
            templates = [templates]
        if templates:
            templates_obj = [template for template in self.__templates
                             if template.name in templates]

        # return results:
        results = []
        if kwargs:
            kwargs['returner'] = returner
            outputter = _outputter_class(**kwargs)
            return [outputter.run(template.results) for template in templates_obj]
        else:
            return [template.results for template in templates_obj]


"""
==============================================================================
TTP PARSER MULTIPROCESSING WORKER
==============================================================================
"""
class _worker(Process):
    """Class used in multiprocessing to parse data
    """

    def __init__(self, task_queue, results_queue, lookups, vars, groups, macro):
        Process.__init__(self)
        self.task_queue = task_queue
        self.results_queue = results_queue
        self.parser_obj = _parser_class(lookups, vars, groups, macro)

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
            self.parser_obj.parse(groups_names=next_task['groups_to_run'])
            result = self.parser_obj.results
            # put results in the queue and finish task
            self.task_queue.task_done()
            self.results_queue.put(result)
        return



"""
==============================================================================
TTP RE PATTERNS COLLECTION CLASS
==============================================================================
"""
class _ttp_patterns():
    def __init__(self):
        self.patterns={
        'PHRASE'   : '(\S+ {1})+?\S+',
        'ROW'      : '(\S+ +)+?\S+',
        'ORPHRASE' : '\S+|(\S+ {1})+?\S+',
        'DIGIT'    : '\d+',
        'IP'       : '(?:[0-9]{1,3}\.){3}[0-9]{1,3}',
        'PREFIX'   : '(?:[0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}',
        'IPV6'     : '(?:[a-fA-F0-9]{1,4}:|:){1,7}(?:[a-fA-F0-9]{1,4}|:?)',
        'PREFIXV6' : '(?:[a-fA-F0-9]{1,4}:|:){1,7}(?:[a-fA-F0-9]{1,4}|:?)/[0-9]{1,3}',
        '_line_'   : '.+',
        'WORD'     : '\S+',
        'MAC'      : '(?:[0-9a-fA-F]{2}(:|\.)){5}([0-9a-fA-F]{2})|(?:[0-9a-fA-F]{4}(:|\.)){2}([0-9a-fA-F]{4})'
        }



"""
==============================================================================
TTP FUNCTIONS CLASS
==============================================================================
"""
class _ttp_functions():
    """Class to store ttp built in functions used for parsing results
    Notes:
        functions to implement
        # 'variable_wrap'         : add \n at given position to wrap long text
        # 'variable_is_ip'        : to check that data is valid ip address - isip(4) for v4 or isip(6) for v6 or any
        # 'variable_is_mac'       : to check that data is valid  mac-address
        # 'variable_is_word'      : check if no spaces in data - same as notcontains(' ')
        # 'variable_to_ip'        : convert to IP object to do something with it like prefix matching, e.g. check if 1.1.1.1 is part of 1.1.0.0/16
        # 'variable_to_list/to_digit/to_string' : convert variable to list, difit or string
        # 'group_exclude_all/exclude_any'  : to exclude group if group contains certain values
        # 'index(int)' : index to get from string converted into list with split
    """
    def __init__(self, parser_obj=None, results_obj=None, out_obj=None, macro=None):
        self.pobj = parser_obj
        self.robj = results_obj
        self.out_obj = out_obj
        self.macro = macro

    def invalid(self, data, name, scope, skip=True):
        if skip == True:
            print("Error: data - {}, {} function '{}' not found".format(data, scope, name))
        else:
            print("Error: data - {}, {} function '{}' not found, valid functions are: \n{}".format(
                data, scope, name, getattr(self, scope).keys() ))

    def output_is_equal(self, data, *args, **kwargs):
        data_to_compare_with = self.out_obj.attributes['load']
        is_equal = False
        if "_anonymous_" in data:
            if data["_anonymous_"] == data_to_compare_with:
                is_equal = True               
        elif data == data_to_compare_with:
            is_equal = True
        return {
            'output_name'        : self.out_obj.name,
            'output_description' : self.out_obj.attributes.get('description', 'None'),
            'is_equal'           : is_equal
        }

    def group_containsall(self, data, *args):
        # args = ('v4address', 'v4mask',)
        for var in args:
            if var in data:
                if var in self.robj.record['DEFAULTS']:
                    if self.robj.record['DEFAULTS'][var] == data[var]:
                        return data, False
            else:
                return data, False
        return data, None

    def group_contains(self, data, *args):
        # args = ('v4address', 'v4mask',)
        for var in args:
            if var in data:
                if var in self.robj.record['DEFAULTS']:
                    if self.robj.record['DEFAULTS'][var] == data[var]:
                        return data, False
                return data, None
        return data, False
        
    def group_macro(self, data, macro_name):
        result = None
        if macro_name in self.macro:
            result = self.macro[macro_name](data)
        # process macro result
        if result is True:
            return data, True
        elif result is False:
            return data, False
        elif result is None:
            return data, None
        return result, None

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

    def match_isdigit(self, data):
        if data.strip().isdigit():
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

    def match_resub(self, data, old, new, count=1):
        return re.sub(old, new, data, count=count), None

    def match_join(self, data, char):
        if isinstance(data, list):
            return char.join(data), None
        else:
            return data, None

    def match_append(self, data, char):
        if isinstance(data, str):
            return (data + char), None
        elif isinstance(data, list):
            data.append(char)
            return data, None
        else:
            return data, None
    
    def match_prepend(self, data, char):
        if isinstance(data, str):
            return (char + data), None
        elif isinstance(data, list):
            data.insert(0, char)
            return data, None
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
        vars = self.pobj.vars['globals']['vars']
        if data.rstrip() == match_line:
            if isinstance(value, str):
                if value in vars:
                    return vars[value], None
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
            return data, {'new_field': {add_field: found_value}}
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
            return data, {'new_field': {add_field: found_value}}
        else:
            return found_value, None
            
    def match_item(self, data, item_index):
        """Method to return item of iterable at given index
        """
        item_index = int(item_index)
        # item_index not out of range
        if 0 <= item_index and item_index <= len(data) - 1:
            return data[item_index], None
        # item_index out of right range - return last item
        elif 0 <= item_index and item_index >= len(data) - 1:
            return data[-1], None
        # negative item_index not out of range 
        elif 0 >= item_index and abs(item_index) <= len(data) - 1: 
            return data[item_index], None    
        # negative item_index out of range - return first item
        elif 0 >= item_index and abs(item_index) >= len(data): 
            return data[0], None    
            
    def match_macro(self, data, macro_name):
        result = None
        if macro_name in self.macro:
            result = self.macro[macro_name](data)
        # process macro result
        if result is True:
            return data, True
        elif result is False:
            return data, False
        elif result is None:
            return data, None
        elif isinstance(result, tuple):
            if len(result) == 2:
                if isinstance(result[1], dict):
                    return result[0], {"new_field": result[1]}
        return result, None

    def match_to_str(self, data):
        return str(data), None
        
    def match_to_list(self, data):
        return [data], None
        
    def match_to_int(self, data):
        try:
            return int(data), None
        except ValueError:
            return data, None

    def match_is_ip(self, data, *args):
        try:
            self.match_to_ip(data, *args)
            return data, True
        except:
            return data, False
            
    def match_to_ip(self, data, *args):
        # for py2 support need to convert data to unicode:
        if python_major_version is 2:
            ipaddr_data = unicode(data)
        elif python_major_version is 3:
            ipaddr_data = data
        if "ipv4" in args:
            if "/" in ipaddr_data or " " in ipaddr_data:
                return ipaddress.IPv4Interface(ipaddr_data.replace(" ", "/")), None
            else:
                return ipaddress.IPv4Address(ipaddr_data), None
        elif "ipv6" in args:
            if "/" in ipaddr_data:
                return ipaddress.IPv6Interface(ipaddr_data), None
            else:
                return ipaddress.IPv6Address(ipaddr_data), None
        elif "/" in ipaddr_data or " " in ipaddr_data:
            return ipaddress.ip_interface(ipaddr_data.replace(" ", "/")), None
        else:
            return ipaddress.ip_address(ipaddr_data), None
                
    def match_to_net(self, data, *args):
        # for py2 support need to convert data to unicode:
        if python_major_version is 2:
            ipaddr_data = unicode(data)
        elif python_major_version is 3:
            ipaddr_data = data
        if "ipv4" in args:
            return ipaddress.IPv4Network(ipaddr_data), None
        elif "ipv6" in args:
            return ipaddress.IPv6Network(ipaddr_data), None
        else:
            return ipaddress.ip_network(ipaddr_data), None
        
    def match_to_cidr(self, data):
        """Method to convet 255.255.255.0 like mask to CIDR prefix len 
        such as 24
        """
        try:
            ret = sum([bin(int(x)).count('1') for x in data.split('.')])
            return ret, None
        except:
            print("ERROR: '{}' is not a valid netmask".format(data))
            return data, None   
            
    def match_ip_info(self, data, *args):
        if isinstance(data, str):
            ip_obj = self.match_to_ip(data, *args)[0]
        else:
            ip_obj = data
        if isinstance(ip_obj, ipaddress.IPv4Interface) or isinstance(ip_obj, ipaddress.IPv6Interface):
            ret = {
                'compressed': ip_obj.compressed, 
                'exploded': ip_obj.exploded, 
                'hostmask': str(ip_obj.hostmask), 
                'ip': str(ip_obj.ip), 
                'is_link_local': ip_obj.is_link_local, 
                'is_loopback': ip_obj.is_loopback, 
                'is_multicast': ip_obj.is_multicast, 
                'is_private': ip_obj.is_private, 
                'is_reserved': ip_obj.is_reserved, 
                'is_unspecified': ip_obj.is_unspecified, 
                'max_prefixlen': ip_obj.max_prefixlen, 
                'netmask': str(ip_obj.netmask), 
                'network': str(ip_obj.network), 
                'version': ip_obj.version, 
                'with_hostmask': ip_obj.with_hostmask, 
                'with_netmask': ip_obj.with_netmask, 
                'with_prefixlen': ip_obj.with_prefixlen,  
                'broadcast_address': str(ip_obj.network.broadcast_address), 
                'network_address': str(ip_obj.network.network_address), 
                'num_addresses': ip_obj.network.num_addresses, 
                'hosts': ip_obj.network.num_addresses - 2,
                'prefixlen': ip_obj.network.prefixlen        
            }
        elif isinstance(ip_obj, ipaddress.IPv4Address) or isinstance(ip_obj, ipaddress.IPv6Address):
            ret = {
                'ip' : str(ip_obj),
                'compressed': ip_obj.compressed, 
                'exploded': ip_obj.exploded , 
                'is_link_local': ip_obj.is_link_local, 
                'is_loopback': ip_obj.is_loopback, 
                'is_multicast': ip_obj.is_multicast, 
                'is_private': ip_obj.is_private, 
                'is_reserved': ip_obj.is_reserved, 
                'is_unspecified': ip_obj.is_unspecified, 
                'max_prefixlen': ip_obj.max_prefixlen, 
                'version': ip_obj.version                
            }
        else:
            ret = data
        return ret, None
        
    def match_cidr_match(self, data, prefix):
        if isinstance(data, str):
            ip_obj = self.match_to_ip(data)[0]
        else:
            ip_obj = data 
        ip_net = self.match_to_net(prefix)[0]         
        if isinstance(ip_obj, ipaddress.IPv4Interface) or isinstance(ip_obj, ipaddress.IPv6Interface):
            check = ip_obj.network.overlaps(ip_net)
        elif isinstance(ip_obj, ipaddress.IPv4Address) or isinstance(ip_obj, ipaddress.IPv6Address):
            if ip_obj.version is 4:
                # for py2 support need to convert data to unicode:
                if python_major_version is 2:
                    ipaddr_data = unicode("{}/32".format(str(ip_obj)))
                elif python_major_version is 3:
                    ipaddr_data = "{}/32".format(str(ip_obj))
                ip_obj = ipaddress.IPv4Interface(ipaddr_data)
            elif ip_obj.version is 6:
                # for py2 support need to convert data to unicode:
                if python_major_version is 2:
                    ipaddr_data = unicode("{}/128".format(str(ip_obj)))
                elif python_major_version is 3:
                    ipaddr_data = "{}/128".format(str(ip_obj))
                ip_obj = ipaddress.IPv6Interface(ipaddr_data)
            check = ip_obj.network.overlaps(ip_net)
        else:
            check = None
        return data, check

    def variable_gethostname(self, data, data_name, *args, **kwargs):
        """Description: Method to find hostname in show
        command output, uses symbols '# ', '<', '>' to find hostname
        """
        REs = [ # ios-xr prompt re must go before ios privilege prompt re
            {'ios_exec': '\n(\S+)>.*(?=\n)'},   # e.g. 'hostname>'
            {'ios_xr': '\n\S+:(\S+)#.*(?=\n)'}, # e.g. 'RP/0/4/CPU0:hostname#'
            {'ios_priv': '\n(\S+)#.*(?=\n)'},   # e.g. 'hostname#'
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
        print('ERROR: "{}" file, Hostname not found'.format(data_name))
        return False

    def variable_getfilename(self, data, data_name, *args, **kwargs):
        """Return dataname
        """
        return data_name


"""
==============================================================================
TTP UTILITIES CLASS
==============================================================================
"""
class _ttp_utils():
    """Class to store various functions for the use along the code
    """
    def __init__(self):
        pass

    def traverse_dict(self, data, path):
        """Method to traverse dictionary data and return element
        at given path.
        """
        if not isinstance(data, dict):
            print("ERROR: ttp_utils.traverse_dict - data is not a dictionary, data: \n{}\n\n".format(data))
            return data
        result = data
        for i in path:
            result = result.get(i, {})
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
        # check if path is a path to file:
        if os.path.isfile(path):
            if read:
                try:
                    if python_major_version is 2:
                        return [('text_data', open(path, 'r').read(),)]
                    return [('text_data', open(path, 'r', encoding='utf-8').read(),)]
                except UnicodeDecodeError:
                    print('Warning: Unicode read error, file "{}"'.format(path))
            else:
                return [('file_name', path,)]
        # check if path is a directory:
        elif os.path.isdir(path):
            files = [f for f in os.listdir(path) if os.path.isfile(path + f)]
            if extensions:
                files=[f for f in files if f.split('.')[-1] in extensions]
            for filter in filters:
                files=[f for f in files if re.search(filter, f)]
            if read:
                if python_major_version is 2:
                    return [('text_data', open((path + f), 'r').read(),) for f in files]
                return [('text_data', open((path + f), 'r', encoding='utf-8').read(),) for f in files]
            else:
                return [('file_name', path + f,) for f in files]
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

        
    def load_struct(self, text_data="", **kwargs):
        """Method to load structured data from text
        or from file(s) given in include attribute
        Args:
            element (obj): ETree xml tag object
        Returns:
            empy {} dict if nothing found, or python dictionary of loaded
            data from elemnt.text string or from included text files
        """
        result = {}
        loader = kwargs.get('load', 'python').lower()
        include = kwargs.get('include', None)
        if not text_data and include is None:
            return None        

        def load_text(text_data, **kwargs):
            return text_data

        def load_ini(text_data, **kwargs):
            if python_major_version is 3:
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
                # read from tag text next to make it more specific:
                if text_data:
                    try:
                        data.read_string(text_data)
                    except:
                        ("ERROR: Unable to load ini formatted data\n'{}'".format(text_data))
                # convert configparser object into dictionary
                result = {k: dict(data.items(k)) for k in list(data.keys())}
            elif python_major_version is 2:
                result = {"DEFAULT": {}}
            if not result["DEFAULT"]: # delete empty DEFAULT section
                result.pop("DEFAULT")
            return result

        def load_python(text_data, **kwargs):
            data = {}
            if include:
                files = self.load_files(path=include, extensions=[], filters=[], read=True)
                for datum in files:
                    text_data += "\n" + datum[1]
            try:
                if python_major_version is 2:
                    # if running ttp.py deirectly
                    if __name__ == "__main__":
                        from ttp_load_py2 import load_python_exec
                    # if running ttp as a module
                    else:
                        from .ttp_load_py2 import load_python_exec
                elif python_major_version is 3:
                    if __name__ == "__main__":
                        from ttp_load_py3 import load_python_exec
                    else:
                        from .ttp_load_py3 import load_python_exec
                data = load_python_exec(text_data)
                return data
            except:
              print("ERROR: Unable to load Python formatted data\n'{}'".format(text_data))

        def load_yaml(text_data, **kwargs):
            from yaml import safe_load
            data = {}
            if include:
                files = self.load_files(path=include, extensions=[], filters=[], read=True)
                for datum in files:
                    text_data += "\n" + datum[1]
            try:
                data = safe_load(text_data)
                return data
            except:
                raise SystemExit("ERROR: Unable to load YAML formatted data\n'{}'".format(text_data))

        def load_json(text_data, **kwargs):
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
                raise SystemExit("ERROR: Unable to load JSON formatted data\n'{}'".format(text_data))

        def load_csv(text_data, **kwargs):
            """Method to load csv data and convert it to dictionary
            using given key-header-column as keys or first column as keys
            """
            from csv import reader
            key = kwargs.get('key', None)
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
        loaders = {
            'ini'   : load_ini,
            'python': load_python,
            'yaml'  : load_yaml,
            'json'  : load_json,
            'csv'   : load_csv,
            'text'  : load_text
        }
        # run function to load structured data
        result = loaders[loader](text_data, **kwargs)
        return result

    def get_attributes(self, line):
        """Extract attributes from variable line string.
        Example:
            'peer | orphrase | exclude(-VM-)' -> [{'peer': []}, {'orphrase': []}, {'exclude': ['-VM-']}]
        Args:
            line (str): string that contains variable attributes i.e. "contains('vlan') | upper | split('.')"
      s  Returns:
            List of opts dictionaries containing extracted attributes
        """
        def get_args_kwargs(*args, **kwargs):
            return {'args': args, 'kwargs': kwargs}

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
                try:
                    args_kwargs = eval("get_args_kwargs({})".format(options))
                except NameError:
                    raise SystemExit("""ERROR: Failed to load arg/kwargs from line '{}' for options '{}' - possibly wrong syntaxis, 
make sure that all string arguments are within quotes, e.g. split(',') not split(,)""".format(line, options))
                opts.update(args_kwargs)
            else:
                options = []
            RESULT.append(opts)
        return RESULT

"""
==============================================================================
TTP TEMPLATE CLASS
==============================================================================
"""
class _template_class():
    """Template class to hold template data
    """
    def __init__(self, template_text, DEBUG=False, data_path_prefix='', ttp_vars={}):
        self.DEBUG = DEBUG
        self.PATHCHAR = '.'          # character to separate path items, like ntp.clock.time, '.' is pathChar here
        self.outputs = []            # list htat contains global outputs
        self.groups_outputs = []     # list that contains groups specific outputs
        # _vars_to_results_ is a dict of {pathN:[var_key1, var_keyN]} data
        # to indicate variables and patch where they should be saved in results
        self.vars = {"_vars_to_results_":{}}
        # add vars from ttp class that supplied during ttp object instantiation
        self.ttp_vars = ttp_vars
        self.vars.update(ttp_vars)
        self.groups = []
        self.inputs = {}
        self.lookups = {}
        self.templates = []
        self.data_path_prefix = data_path_prefix
        self.utils = _ttp_utils()
        self.results = []
        self.name = None
        self.attributes = {}
        self.macro = {} # dictionary of macro name and macro function

        # load template from string:
        self.load_template_xml(template_text)

        # update inputs with the groups it has to be run against:
        self.update_inputs_with_groups()

        # update groups with output references:
        self.update_groups_with_outputs()

        if self.DEBUG == True:
            from yaml import dump
            print("self.attributes: \n", self.attributes)
            print("self.outputs: \n", dump(self.outputs))
            print("self.groups_outputs: \n", dump(self.groups_outputs))
            print("self.vars: \n",   dump(self.vars))
            print('self.groups: \n', dump(self.groups))
            print("self.inputs: \n", self.inputs)
            print('self.lookups: \n', self.lookups)
            print('self.templates: \n', self.templates)

    def add_lookup(self, data):
        """Method to load lookup data
        """
        self.lookups.update(data)
        [template.add_lookup(data) for template in self.templates]
            
    def add_vars(self, data):
        """Method to update vars with given data
        """
        if isinstance(data, dict):
            self.vars.update(data)
            [template.add_vars(data) for template in self.templates]

    def run_outputs(self):
        """Method to run template outputs with template results
        """
        # [output.run(self.results) for output in self.outputs]
        for output in self.outputs:
            self.results = output.run(self.results)

    def form_results(self, result):
        """Method to add results to self.results
        """
        if not result:
            return
        elif '_anonymous_' in result:
            if isinstance(result['_anonymous_'], list):
                self.results += result['_anonymous_']
            else:
                self.results += [result['_anonymous_']]
        else:
            if isinstance(result, list):
                self.results += result
            else:
                self.results.append(result)

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
                    # remove 'all' from this input as it is group specific:
                    if self.inputs[input_name]['groups'][0].lower() == 'all':
                        self.inputs[input_name]['groups'].pop(0)
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

    def update_groups_with_outputs(self):
        """Method to replace output names in group with
        output index from self.groups_outputs, also move
        output from self.outputs to group specific
        self.groups_outputs
        """
        for G in self.groups:
            for grp_index, grp_output in enumerate(G.outputs):
                group_output_found = False
                # search through global outputs:
                for glob_index, glob_output in enumerate(self.outputs):
                    if glob_output.name == grp_output:
                        self.groups_outputs.append(self.outputs.pop(glob_index))
                        G.outputs[grp_index] = self.groups_outputs[-1]
                        group_output_found = True
                # go to next output if this output found:
                if group_output_found:
                    continue
                # try to find output in group specific outputs:
                for index, output in enumerate(self.groups_outputs):
                    if output.name == grp_output:
                        G.outputs[grp_index] = output
                        group_output_found = True
                # print error message if no output found:
                if not group_output_found:
                    G.outputs.pop(grp_index)
                    print("Error: group output '{}' not found.".format(grp_output))


    def get_template_attributes(self, element):

        def extract_name(O):
            self.name = O

        opt_funcs = {
        'name'    : extract_name
        # data_path_prefix
        # pathchar
        # debug
        }

        [opt_funcs[name](options) for name, options in element.attrib.items()
         if name in opt_funcs]

    def load_template_xml(self, template_text):

        def parse_vars(element):
            # method to parse vars data
            vars = self.utils.load_struct(element.text, **element.attrib)
            if vars:
                self.vars.update(vars)
            #check if var has name attribute:
            if "name" in element.attrib:
                path = element.attrib['name']
                if not path in self.vars['_vars_to_results_']:
                    self.vars['_vars_to_results_'][path] = []
                [self.vars['_vars_to_results_'][path].append(key) for key in vars.keys()]

        def parse_output(element):
            self.outputs.append(_outputter_class(element))

        def parse_input(element):
            input_data = {}
            data = []

            # load input parameters:
            input_data = self.utils.load_struct(element.text, **element.attrib)

            # get parameters from input attributes:
            name = element.attrib.get('name', 'Default_Input')
            groups = element.attrib.get('groups', 'all')
            groups = [i.strip() for i in groups.split(',')]

            # if load is text:
            if isinstance(input_data, str):
                self.set_input(data=[('text_data', input_data)], input_name=name, groups=groups)
                return

            extensions = input_data.get('extensions', [])
            filters = input_data.get('filters', [])
            urls = input_data.get('url', [])

            # run checks:
            if not urls:
                raise SystemExit("ERROR: Input '{}', no 'url' parametr given".format(name))
            if isinstance(extensions, str): extensions=[extensions]
            if isinstance(filters, str): filters=[filters]
            if isinstance(urls, str): urls=[urls]
            if isinstance(groups, str): groups=[groups]

            # load data:
            for url in urls:
                url = self.data_path_prefix + url.lstrip('.')
                data += self.utils.load_files(url, extensions, filters, read=False)

            self.set_input(data=data, input_name=name, groups=groups)

        def parse_group(element):
            self.groups.append(
                _group_class(
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
            data = self.utils.load_struct(element.text, **element.attrib)
            if data is None:
                return
            self.lookups[name] = data

        def parse_template(element):
            self.templates.append(_template_class(
                template_text=ET.tostring(element, encoding="UTF-8"),
                DEBUG=self.DEBUG,
                data_path_prefix=self.data_path_prefix,
                ttp_vars=self.ttp_vars)
            )

        def parse_macro(element):
            funcs = {}
            # extract macro with all the __builtins__ provided
            try:
                if python_major_version is 2:
                    # if running ttp script directly
                    if __name__ == "__main__":
                        from ttp_load_py2 import load_python_exec
                    # if runnint ttp as a module
                    else:
                        from .ttp_load_py2 import load_python_exec
                elif python_major_version is 3:
                    if __name__ == "__main__":
                        from ttp_load_py3 import load_python_exec
                    else:
                        from .ttp_load_py3 import load_python_exec
                funcs = load_python_exec(element.text, builtins=__builtins__)
                self.macro.update(funcs)
            except SyntaxError as e:
                print("ERROR: Syntax error, failed to load macro:{}".format(element.text))
            
        def parse__anonymous_(element):
            elem = ET.XML('<g name="_anonymous_">\n{}\n</g>'.format(element.text))
            parse_group(elem)

        def invalid(C):
            print("Warning: Invalid tag '{}'".format(C.tag))

        def parse_hierarch_tmplt(element):
            # dict to store all top tags sorted parsing as need to
            # parse variablse fist after that all the rest
            tags = {
                'vars': [], 'groups': [],
                'inputs': [], 'outputs': [],
                'lookups': [], 'macro': []
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
            'lookup'    : lambda C: tags['lookups'].append(C),
            'template'  : parse_template,
            'macro'     : parse_macro
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
            # load template from text reconstructing it if required:
            try:
                template_ET = ET.XML(template_text)
                # check if top tag is not template:
                if template_ET.tag.lower() != 'template':
                    tmplt = ET.XML("<template />")
                    tmplt.insert(0, template_ET)
                    template_ET = tmplt
                else:
                    self.get_template_attributes(template_ET)
            except ET.ParseError as e:
                template_ET = ET.XML("<template>\n{}\n</template>".format(template_text))

            # check if template has children:
            if not list(template_ET):
                parse__anonymous_(template_ET)
            else:
                parse_hierarch_tmplt(template_ET)

        parse_template_XML(template_text)



"""
==============================================================================
GROUP CLASS
==============================================================================
"""
class _group_class():
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
            outputs (list): list of outputs to run for this group
            funcs (list):vlist of functions to run agaist group results
            method (str): indicate type of the group - [group | table]
            start_re (list): contains list of group start regular epressions
            end_re (list): contains list of group end regular expressions
            children (list): contains child group objects
            vars (dict): variables dictionary from template class
        """
        self.pathchar = pathchar
        self.top      = top
        self.path     = list(path)
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
        self.set_anonymous_path()
        self.get_regexes(element.text)
        self.get_children(list(element))

    def set_anonymous_path(self):
        """Mthod to set anonyous path for top group without name
        attribute.
        """
        if self.top is True:
            if self.path == []:
                self.path = ["_anonymous_"]
                self.name = "_anonymous_"
        

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
            self.path = self.path + O.split(self.pathchar)
            self.name = '.'.join(self.path)

        def extract_contains(O):
            if isinstance(O, str):
                self.funcs.append({
                    'name': 'contains',
                    'args': [i.strip() for i in O.split(',')]
                })
            elif isinstance(O, dict):
                self.funcs.append(O) 

        def extract_containsall(O):
            if isinstance(O, str):
                self.funcs.append({
                    'name': 'containsall',
                    'args': [i.strip() for i in O.split(',')]
                })
            elif isinstance(O, dict):
                self.funcs.append(O) 
            
        def extract_macro(O):
            if isinstance(O, str):
                self.funcs.append({
                    'name': 'macro',
                    'args': [i.strip() for i in O.split(',')]
                })
            elif isinstance(O, dict):
                self.funcs.append(O)            
     
        def extract_functions(O):
            funcs = self.utils.get_attributes(O)
            for i in funcs:
                name = i['name']
                if name in functions: functions[name](i)
                else: print('ERROR: Uncknown group function: "{}"'.format(name))

        # group attributes extract functions dictionary:
        options = {
        'method'      : extract_method,
        'input'       : extract_input,
        'output'      : extract_output,
        'name'        : extract_name,
        'default'     : extract_default
        }
        functions = {
        'contains'    : extract_contains,
        'containsall' : extract_containsall,        
        'macro'       : extract_macro,
        'functions'   : extract_functions,
        'fun'         : extract_functions    
        }

        for name, attributes in data.items():
            if name.lower() in options: options[name.lower()](attributes)
            elif name.lower() in functions: functions[name.lower()](attributes)
            else: print('ERROR: Uncknown group attribute: {}="{}"'.format(name, attributes))


    def get_regexes(self, data, tail=False):
        varaibles_matches=[] # list of dictionaries
        regexes=[]

        for line in data.splitlines():
            # skip empty lines and comments:
            if not line.strip(): continue
            elif line.startswith('##'): continue
            # strip leading spaces as they will be reconstructed in regex
            line = line.rstrip()
            # parse line against variable regexes
            match=re.findall('{{([\S\s]+?)}}', line)
            if not match:
                print("Warning: Variable not found in line: '{}'".format(line))
                continue
            varaibles_matches.append({'variables': match, 'line': line})

        for i in varaibles_matches:
            regex = ''
            variables = {}
            action = 'ADD'
            is_line = False
            skip_regex = False
            for variable in i['variables']:
                variableObj = _variable_class(variable, i['line'], DEBUG=self.debug, group=self)

                # check if need to skip appending regex dict to regexes list
                # have to skip it for unconditional 'set' function
                if variableObj.skip_regex_dict == True:
                    skip_regex = True
                    continue

                # creade variable dict:
                if variableObj.skip_variable_dict is False:
                    variables[variableObj.var_name] = variableObj

                # form regex:
                regex=variableObj.form_regex(regex)

                # check if IS_LINE:
                if is_line == False:
                    is_line = variableObj.IS_LINE

                # modify save action only if it is not START or STARTEMPTY already:
                if "START" not in action:
                    action = variableObj.SAVEACTION

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
            self.children.append(_group_class(
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
class _variable_class():
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
        self.utils = _ttp_utils()                    # ttp utils

        # add formatters:
        self.REs = _ttp_patterns()

        # form attributes - list of dictionaries:
        self.attributes = self.utils.get_attributes(variable)
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
            # handle conditional set when we have line to match
            if match_line:
                data['kwargs']['match_line'] = '\n' + match_line
                self.functions.append(data)
            # handle unconditional set without line to match
            else:
                self.group.defaults.update({self.var_name: data['args'][0]})
                self.skip_regex_dict = True                

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

        def extract_ignore(data):
            self.skip_variable_dict = True

        def extract_chain(data):
            """add items from chain to variable attributes and functions
            """
            variable_value = self.group.vars.get(data['args'][0], None)
            if variable_value is None:
                print("ERROR: chain variable '{}' not found".format(data['args'][0]))
                return
            attributes =  self.utils.get_attributes(variable_value)
            for i in attributes:
                name = i['name']
                if name in extract_funcs:
                    extract_funcs[name](i)
                else:
                    self.functions.append(i)
        
        def import_ipaddress(data):
            if "ipaddress" not in globals():
                try:
                    globals()["ipaddress"] = __import__("ipaddress")
                except ImportError:
                    print("ERROR: no ipaddress module installed, install: python -m pip install ipaddress")
            self.functions.append(data)

        extract_funcs = {
        'ignore'        : extract_ignore,
        '_start_'       : extract__start_,
        '_end_'         : extract__end_,
        '_line_'        : extract__line_,
        'chain'         : extract_chain,
        'set'           : extract_set,
        'default'       : extract_default,
        'joinmatches'   : extract_joinmatches,
        'to_ip'  : import_ipaddress,
        'to_net' : import_ipaddress, 'ip_info' : import_ipaddress,
        'is_ip'  : import_ipaddress, 'cidr_match': import_ipaddress,
        # regex formatters:
        're'       : lambda data: self.var_res.append(self.REs.patterns[data['args'][0]]),
        'PHRASE'   : lambda data: self.var_res.append(self.REs.patterns['PHRASE']),
        'ROW'      : lambda data: self.var_res.append(self.REs.patterns['ROW']),
        'ORPHRASE' : lambda data: self.var_res.append(self.REs.patterns['ORPHRASE']),
        'DIGIT'    : lambda data: self.var_res.append(self.REs.patterns['DIGIT']),
        'IP'       : lambda data: self.var_res.append(self.REs.patterns['IP']),
        'PREFIX'   : lambda data: self.var_res.append(self.REs.patterns['PREFIX']),
        'IPV6'     : lambda data: self.var_res.append(self.REs.patterns['IPV6']),
        'PREFIXV6' : lambda data: self.var_res.append(self.REs.patterns['PREFIXV6']),
        'MAC'      : lambda data: self.var_res.append(self.REs.patterns['MAC']),
        'WORD'     : lambda data: self.var_res.append(self.REs.patterns['WORD']),
        '_line_'   : lambda data: self.var_res.append(self.REs.patterns['_line_']),
        }
        # handle _start_, _line_ etc.
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
        if not '_exact_' in  esc_var:
            esc_var=re.sub('\d+', r'\\d+', esc_var)  # replace all numbers with \d+ in regex in variable, skip it if EXACT in variable
        esc_var=re.sub(r'(\\ )+', r'\\ +', esc_var)  # replace all spaces with ' +' in regex in variable

        # form escaped line:
        esc_line=re.escape(self.LINE.lstrip())         # escape all special chars in line like (){} [].* etc. and strip leading spaces to preserve indent
        if not '_exact_' in  esc_line:
            esc_line=re.sub('\d+',r'\\d+', esc_line)   # to replace all numbers with \d+ in regex
        esc_line=re.sub(r'(\\ )+',r'\\ +', esc_line)   # to replace all spaces with ' +' in regex

        # check if regex empty, if so, make self.regex equal to escaped line, reconstruct indent and add start/end of line:
        if regex == '':
            self.regex = esc_line
            self.regex = self.indent * ' ' + self.regex       # reconstruct indent
            self.regex = '\\n' + self.regex + ' *(?=\\n)'     # use lookalhead assertion for end of line and match any number of trailing spaces
        else:
            self.regex = regex

        def regex_ignore(data):
            if len(data['args']) == 0:
                self.regex = self.regex.replace(esc_var, '\S+', 1)
            elif len(data['args']) == 1:
                pattern = data['args'][0]
                if pattern in self.REs.patterns:
                    self.regex = self.regex.replace(esc_var, "(?:{})".format(self.REs.patterns[pattern]), 1)
                else:
                    self.regex = self.regex.replace(esc_var, "(?:{})".format(pattern), 1)

        def regex_deleteVar(data):
            result = None
            if esc_var in self.regex:
                index = self.regex.find(esc_var)
                # slice regex string before esc_var start:
                result = self.regex[:index]
                # delete "\ +" from end of line and add " *(?=\\n)":
                result = re.sub('(\\\\ \+)$', '', result) + ' *(?=\\n)'
            if result:
                self.regex = result

        # for variables like {{ ignore() }}
        regexFuncsVar={
        'ignore'   : regex_ignore,
        '_start_'  : regex_deleteVar,
        '_end_'    : regex_deleteVar
        }
        if self.var_name in regexFuncsVar:
            regexFuncsVar[self.var_name](self.var_dict)
            
        # for the rest of functions:
        regexFuncs={
        'set'      : regex_deleteVar
        }
        # go over all keywords to form regex:
        [regexFuncs[i['name']](i)
         for i in self.functions if i['name'] in regexFuncs]

        # assign default re if variable without regex formatters:
        if self.var_res == []: self.var_res.append(self.REs.patterns['WORD'])

        # form variable regex by replacing escaped variable, if it is in regex
        # except for the case if variable is "ignore" as it already was replaced
        # in regex_ignore function:
        if self.var_name != "ignore":
            self.regex = self.regex.replace(esc_var,
                '(?P<{}>(?:{}))'.format(self.var_name, ')|(?:'.join(self.var_res),1)
            )

        # after regexes formed we can delete unneccesary variables:
        if self.DEBUG == False:
            del self.attributes, esc_line, self.DEBUG
            del self.LINE, self.skip_defaults, self.indent
            del self.var_dict, self.REs, self.var_res, self.utils

        return self.regex



"""
==============================================================================
TTP PARSER OBJECT
==============================================================================
"""
class _parser_class():
    """Parser Object to run parsing of data and constructong resulted dictionary/list
    """
    def __init__(self, lookups, vars, groups, macro):
        self.lookups = lookups
        self.original_vars = vars
        self.groups = groups
        self.functions = _ttp_functions(parser_obj=self, macro=macro)
        self.utils = _ttp_utils()
        self.macro = macro


    def set_data(self, D):
        """Method to load data:
        Args:
            D (tuple): items are dict of (data_type, data_path,)
        """
        self.results = {}
        if D[0] == 'text_data':
            self.DATATEXT = '\n' + D[1] + '\n\n'
            self.DATANAME = 'text_data'
        else:
            data = self.utils.load_files(path=D[1], read=True)
            # data is a list of one tuple - [(data_type, data_text,)]
            self.DATATEXT = '\n' + data[0][1] + '\n\n'
            self.DATANAME = D[1]
        # set vars to original vars and update them based on DATATEXT:
        self.set_vars()


    def set_vars(self):
        """Method to load template
        Args:
            vars (dict): template variables dictionary
        """
        self.vars={
            'globals': {
                # need to copy as additional var can be recorded,
                # that can lead to changes in original vars dictionary
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
        unsort_rslts = [] # list of dictionaries - one item per top group, each dictionary
                          # contains all unsorted match results for all REs within group
        raw_results = []  # list to store sorted results for all groups
        grps_unsort_rslts = [] # group specific match results to run output against them
                               # each item is a tuple of (results, group.outputs,)
        grps_raw_results = []  # group specific sorted results

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
                                attrib = getattr(data, func_name)
                                if callable(attrib):
                                    run_result = attrib(*args, **kwargs)
                                else:
                                    run_result = attrib
                                if run_result is False:
                                    flag = False
                                elif run_result is True:
                                    flag = True
                                else:
                                    data = run_result
                                    flag = None        
                            except AttributeError as e:
                                flag = None
                                self.functions.invalid(data, func_name, scope='variable', skip=True)
                        if flag is True or flag is None:
                            continue
                        elif flag is False:
                            result = False # if flag False - checks produced negative result
                            break
                        elif isinstance(flag, dict):
                            # update new_field data preserving previously got new_field
                            if "new_field" in flags and "new_field" in flag:
                                flags["new_field"].update(flag["new_field"])
                            else:
                                flags.update(flag)

                    if result is False:
                        break

                    result.update({var_name: data})

                    if 'new_field' in flags:
                        result.update(flags['new_field'])

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
            s = 0                     # int to get the lowest start re span value
            e = -1                    # int to get the biggest end re span value
            group_start_found = False

            # run start REs:
            for R in group.start_re:
                matches = list(R['REGEX'].finditer(self.DATATEXT[start:end]))
                if not matches:
                    continue
                check_matches(R, matches, results, start)
                # if s is bigger, make it smaller:
                if s > matches[0].span()[0] or group_start_found is False:
                    group_start_found = True
                    s = matches[0].span()[0]
            start = start + s
            # if no matches found for any start REs of this group - skip the rest of REs
            if not group_start_found:
                # if empty group - tag only, no start REs - run children:
                if not group.start_re:
                    # run recursion:
                    [run_re(child_group, results, start, end) for child_group in group.children]
                return {}

            # run end REs:
            for R in group.end_re:
                matches = list(R['REGEX'].finditer(self.DATATEXT[start:end]))
                if not matches:
                    continue
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

        # run parsing to produce unsorted results:
        for group in self.groups:
            if group.name in groups_names or 'all' in groups_names:
                # get results for groups with global only outputs:
                if group.outputs == []:
                    unsort_rslts.append(run_re(group, results={}))
                # get results for groups with group specific results:
                else:
                    # for a tuple of (results, group.outputs,)
                    grps_unsort_rslts.append(
                        (run_re(group, results={}), group.outputs,)
                    )

        # sort global groups results:
        [ raw_results.append(
          [group_result[key] for key in sorted(list(group_result.keys()))]
          ) for group_result in unsort_rslts if group_result ]
        # form results for global groups:
        RSLTSOBJ = _results_class(macro=self.macro)
        RSLTSOBJ.form_results(self.vars['globals']['vars'], raw_results)
        self.results = RSLTSOBJ.RESULTS

        # sort results for group specific results:
        [ grps_raw_results.append(
            ([group_result[0][key] for key in sorted(list(group_result[0].keys()))],
            group_result[1],) # tuple item that contains group.outputs
        ) for group_result in grps_unsort_rslts if group_result[0] ]
        # form results for groups specific results with running groups through outputs:
        for grp_raw_result in grps_raw_results:
            RSLTSOBJ = _results_class(macro=self.macro)
            RSLTSOBJ.form_results(self.vars['globals']['vars'], [grp_raw_result[0]])
            grp_result = RSLTSOBJ.RESULTS
            for output in grp_raw_result[1]:
                grp_result = output.run(data=grp_result)
            # transform results into list:
            if isinstance(self.results, dict):
                if self.results:
                    self.results = [self.results]
                else:
                    self.results = []
            # save results into global results list:
            self.results.append(grp_result)



"""
==============================================================================
TTP RESULTS FORMATTER OBJECT
==============================================================================
"""
class _results_class():
    """
    Class to save results and do actions with them.
    Args:
        self.dyn_path_cache (dict): used to store dynamic path variables
    """
    def __init__(self, macro):
        self.RESULTS = {}
        self.GRPLOCK = {'LOCK': False, 'GROUP': ()} # GROUP - path tuple of locked group
        self.record={
            'RESULT'     : {},
            'PATH'       : [],
            'FUNCTIONS' : []
        }
        self.dyn_path_cache={}
        self.functions = _ttp_functions(results_obj=self, macro=macro)

    def form_results(self, vars, results):
        self.vars=vars
        saveFuncs={
            'START'      : self.START,       # START - to start new group;
            'ADD'        : self.ADD,         # ADD - to add data to group, defaul-normal action;
            'STARTEMPTY' : self.STARTEMPTY,  # STARTEMPTY - to start new empty group in case if _start_ found;
            'END'        : self.END,         # END - to explicitly signal the end of group to LOCK it;
            'JOIN'       : self.JOIN         # JOIN - to join results for given variable, e.g. joinmatches;
        }
        # save _vars_to_results_ to results if any:
        if results: self.save_vars(vars)
        # iterate over group results and form results structure:
        for group_results in results:
            # clear LOCK between groups as LOCK has intra group significanse only:
            self.GRPLOCK['LOCK'] = False
            self.GRPLOCK['GROUP'] = ()
            # iterate over each match result for the group:
            for result in group_results:
                # if result been matched by one regex only
                if len(result) == 1:
                    re=result[0][0]
                    result_data=result[0][1]
                # if same results captured by multiple regexes, need to do further descision checks:
                else:
                    for item in result:
                        item_re = item[0]
                        # pick up first start re:
                        if item_re['ACTION'].startswith('START'):
                            re = item[0]
                            result_data = item[1]
                            break
                        # pick up re with the same path as current group:
                        elif item_re["GROUP"].path == self.record["PATH"]:
                            re = item[0]
                            result_data = item[1]
                            break
                        # if IS_LINE - assign it but continue iterating:
                        elif item_re['IS_LINE'] is True:
                            re = item[0]
                            result_data = item[1]
                        # old logic - pick up first non IS_LINE re:
                        # elif re['IS_LINE'] == False:
                        #     result_data = item[1]
                        #     break
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
                    PATH       = list(group.path),
                    DEFAULTS   = group.runs,
                    FUNCTIONS = group.funcs,
                    REDICT     = re
                )
        # check the last group:
        if self.record['RESULT'] and self.PROCESSGRP() is not False:
            self.SAVE_CURELEMENTS()


    def save_vars(self, vars):
        for path, vars_keys in vars['_vars_to_results_'].items():
            # skip empty path:
            if not path: continue
            result = {}
            for key in vars_keys:
                result[key] = vars[key]
            self.record = {
                'RESULT'     : result,
                'PATH'       : [i.strip() for i in path.split('.')],
            }
            self.SAVE_CURELEMENTS()
        # set record to default value:
        self.record={'RESULT': {}, 'PATH': [], 'FUNCTIONS': []}


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
            return self.dict_by_path(PATH, ELEMENT[-1])       # run recursion with last item in the list


    def SAVE_CURELEMENTS(self):
        """Method to save current group results in self.RESULTS
        """
        RSLT = self.record['RESULT']
        PATH = self.record['PATH']
        # get ELEMENT from self.RESULTS by PATH
        E = self.dict_by_path(PATH=PATH, ELEMENT=self.RESULTS)
        if isinstance(E, list):
            E.append(RSLT)
        elif isinstance(E, dict):
            # check if PATH endswith "**" - update result's ELEMENET without converting it into list:
            if len(PATH[-1]) - len(str(PATH[-1]).rstrip('*')) == 2:
                E.update(RSLT)
            # to match all the other cases, like templates without "**" in path:
            elif E != {}:
                # transform ELEMENT dict to list and append data to it:
                self.RESULTS = self.value_to_list(DATA=self.RESULTS, PATH=PATH, RESULT=RSLT)
            else:
                E.update(RSLT)


    def START(self, RESULT, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
        if self.record['RESULT'] and self.PROCESSGRP() != False:
            self.SAVE_CURELEMENTS()
        self.record = {
            'RESULT'     : DEFAULTS.copy(),
            'DEFAULTS'   : DEFAULTS,
            'PATH'       : PATH,
            'FUNCTIONS' : FUNCTIONS
        }
        self.record['RESULT'].update(RESULT)


    def STARTEMPTY(self, RESULT, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
        if self.record['RESULT'] and self.PROCESSGRP() != False:
            self.SAVE_CURELEMENTS()
        self.record = {
            'RESULT'     : DEFAULTS.copy(),
            'DEFAULTS'   : DEFAULTS,
            'PATH'       : PATH,
            'FUNCTIONS' : FUNCTIONS
        }


    def ADD(self, RESULT, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
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


    def JOIN(self, RESULT, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
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
                    if isinstance(RESULT[k], list):
                        self.record['RESULT'][k] += RESULT[k]        # join lists
                    elif isinstance(RESULT[k], str):
                        self.record['RESULT'][k].append(RESULT[k])   # append to list
            else:
                self.record['RESULT'][k] = RESULT[k]                 # if first result


    def END(self, RESULT, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
        # action to end current group by locking it
        self.GRPLOCK['LOCK'] = True
        self.GRPLOCK['GROUP'] = list(PATH)


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
                    self.dyn_path_cache[m] = self.record['RESULT'][m]
                    repl = self.record['RESULT'].pop(m)
                    path[index] = re.sub(pattern, repl, item)
                elif m in self.dyn_path_cache:
                    path[index] = re.sub(pattern, self.dyn_path_cache[m], item)
                elif m in self.vars:
                    path[index] = re.sub(pattern, self.vars[m], item)
                else:
                    return False
        return path


    def PROCESSGRP(self):
        """Method to process group results
        """
        for item in self.record['FUNCTIONS']:
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
class _outputter_class():
    """Class to serve excel, yaml, json, xml etc. dumping functions
    Args:
        destination (str): if 'file' will save data to file,
            if 'terminal' will print data to terinal
        format (str): output format indicator on how to format data
        url (str): path to where to save data to e.g. OS path
        filename (str): name of hte file
        method (str): how to save results, in separate files or in one file
    """
    def __init__(self, element=None, **kwargs):
        self.utils = _ttp_utils()
        # set attributes default values:
        self.attributes = {
            'returner'    : ['self'],
            'format'      : 'raw',
            'url'         : './Output/',
            'method'      : 'join',
            'filename'    : 'output_{}.txt'.format(ctime)
        }
        self.name = None
        self.return_to_self = False
        self.functions = []
        self.functions_obj = _ttp_functions(out_obj=self)
        # get output attributes:
        if element is not None:
            self.element = element
            self.get_attributes(element.attrib)
        elif kwargs:
            self.get_attributes(kwargs)

    def get_attributes(self, data):

        def extract_name(O):
            self.name = O

        def extract_returner(O):
            supported_returners = ['file', 'terminal', 'self']
            if O in supported_returners:
                self.attributes['returner'] = [i.strip() for i in O.split(',')]
            else:
                raise SystemExit("Error: Unsupported output returner '{}'. Supported: {}. Exiting".format(
                    O, supported_returners))

        def extract_format(O):
            supported_formats = ['raw', 'yaml', 'json', 'csv', 'jinja2', 'pprint', 'tabulate', 'table']
            if O in supported_formats:
                self.attributes['format'] = O
            else:
                raise SystemExit("Error: Unsupported output format '{}'. Supported: {}. Exiting".format(
                    O, supported_formats))

        def extract_load(O):
            self.attributes['load'] = self.utils.load_struct(self.element.text, **self.element.attrib)

        def extract_url(O):
            self.attributes['url'] = O

        def extract_filename(O):
            self.attributes['filename'] = O

        def extract_method(O):
            supported_methods = ['split', 'join']
            if O in supported_methods:
                self.attributes['method'] = O
            else:
                raise SystemExit("Error: Unsupported file returner method '{}'. Supported: {}. Exiting".format(
                                O, supported_methods))

        def extract_functions(O):
            functions = self.utils.get_attributes(O)
            for i in functions:
                name = i['name']
                if name in opt_funcs:
                    opt_funcs[name](i)
                else:
                    print('ERROR: Uncknown output function: "{}"'.format(name))

        def function_is_equal(data):
            if not data['kwargs'] and not data['args']:
                # do nothing as self.attributes['load'] will be used
                self.functions.append(data)

        def extract_description(O):
            self.attributes['description'] = O

        def extract_format_attributes(O):
            """Extract formatter attributes
            """
            format_attributes = self.utils.get_attributes(
                            'format_attributes({})'.format(O))
            self.attributes['format_attributes'] = {
                'args': format_attributes[0]['args'],
                'kwargs': format_attributes[0]['kwargs']
            }

        def extract_path(O):
            self.attributes['path'] = [i.strip() for i in O.split('.')]

        def extract_headers(O):
            self.attributes['headers'] = [i.strip() for i in O.split(',')]

        opt_funcs = {
        'name'           : extract_name,
        'returner'       : extract_returner,
        'format'         : extract_format,
        'load'           : extract_load,
        'url'            : extract_url,
        'filename'       : extract_filename,
        'method'         : extract_method,
        'functions'      : extract_functions,
        'is_equal'       : function_is_equal,
        'description'    : extract_description,
        'format_attributes' : extract_format_attributes,
        'path'           : extract_path,
        'headers'        : extract_headers
        }

        for name, options in data.items():
            if name.lower() in opt_funcs: opt_funcs[name.lower()](options)
            else: self.attributes[name] = options

    def run(self, data):
        returners = self.attributes['returner']
        format = self.attributes['format']
        results = data
        # run fuctions:
        for item in self.functions:
            func_name = item['name']
            args = item['args']
            kwargs = item['kwargs']
            results = getattr(self.functions_obj, 'output_' + func_name)(results, *args, **kwargs)
        # format data using requested formatter:
        results = getattr(self, 'formatter_' + format)(results)
        # run returners:
        [getattr(self, 'returner_' + returner)(results) for returner in returners]
        # check if need to return processed data:
        if self.return_to_self is True:
            return results        
        # return unmodified data:
        return data

    def returner_self(self, D):
        """Method to indicate that processed data need to be returned
        """
        self.return_to_self = True

    def returner_file(self, D):
        """Method to write data into file
        Args:
            url (str): os path there to save files
            filename (str): name of the file
        """
        url = self.attributes.get('url', './Output/')
        filename = self.attributes.get('filename', 'output_{}.txt'.format(ctime))
        if self.name:
            filename = self.name + '_' + filename
        # check if path exists already, create it if not:
        if not os.path.exists(url):
            os.mkdir(url)
        with open(url + filename, 'w') as f:
            f.write(D)

    def returner_terminal(self, D):
        if python_major_version is 2:
            if isinstance(D, str) or isinstance(D, unicode):
                print(D)
            else:
                print(str(D).replace('\\n', '\n'))
        elif python_major_version is 3:
            if isinstance(D, str):
                print(D)
            else:
                print(str(D).replace('\\n', '\n'))
                
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
        try:
            from yaml import dump
        except ImportError:
            raise SystemExit("yaml not installed, install: 'python -m pip install pyyaml', exiting")
        return dump(data, default_flow_style=False)

    def formatter_json(self, data):
        """Method returns parsing result in json format.
        """
        from json import dumps
        return dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

    def formatter_table(self, data):
        """Method to form table there table is list of lists,
        firts item - heders row. Method used by csv/tabulate/excel
        formatters.
        """
        table = []
        headers = set()
        data_to_table = []
        source_data = []
        # get attributes:
        provided_headers = self.attributes.get('headers', [])
        path = self.attributes.get('path', [])
        extras = self.attributes.get('extras', 'ignore')
        missing = self.attributes.get('missing', '')
        key = self.attributes.get('key', '')
        # normilize source_data to list:
        if isinstance(data, list): # handle the case for template/global output
            source_data += data
        elif isinstance(data, dict): # handle the case for group specific output
            source_data.append(data)
        # form data_to_table:
        for datum in source_data:
            item = self.utils.traverse_dict(datum, path)
            if not item: # skip empty results
                continue
            elif isinstance(item, list):
                data_to_table += item
            elif isinstance(item, dict):
                # flatten dictionary data if key was given, e.g. if item looks like:
                # { "Fa0": {"admin": "administratively down"},
                #   "Ge0/1": {"access_vlan": "24"}}
                # it will become:
                # [ {"admin": "administratively down", "interface": "Fa0"},
                #   {"access_vlan": "24", "interface": "Ge0/1"} ]
                if key:
                    for k, v in item.items():
                        v.update({key: k})
                        data_to_table.append(v)
                else:
                    data_to_table.append(item)
        # create headers:
        if provided_headers:
            headers = provided_headers
        else:
            # headers is a set, set.update only adds unique values to set
            [headers.update(list(item.keys())) for item in data_to_table]
            headers = sorted(list(headers))
        # handle extras:
        if extras is "add":
            pass
        # save headers row in table:
        table.insert(0, headers)
        # fill in table with data:
        for item in data_to_table:
            row = [missing for _ in headers]
            for k, v in item.items():
                if k in headers:
                    row[headers.index(k)] = v
            table.append(row)
        return table

    def formatter_csv(self, data):
        """Method to dump list of dictionaries into table
        using provided separator, default is comma - ','
        """
        result = ""
        # form table - list of lists
        table = self.formatter_table(data)
        sep = self.attributes.get('sep', ',')
        # from results:
        result = sep.join(table[0])
        for row in table[1:]:
            result += "\n" + sep.join(row)
        return result

    def formatter_tabulate(self, data):
        """Method to format data as a table using tabulate module.
        """
        try:
            from tabulate import tabulate
        except ImportError:
            raise SystemExit("ERROR: tabulate not installed, install: 'python -m pip install tabulate', exiting")
        # form table - list of lists
        table = self.formatter_table(data)
        headers = table.pop(0)
        attribs = self.attributes.get('format_attributes', {'args': [], 'kwargs': {}})
        # run tabulate:
        return tabulate(table, headers=headers, *attribs['args'], **attribs['kwargs'])

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
        # render data making whole results accessible from _data_ variable in jinja
        result = template_obj.render(_data_=data)
        return result


"""
==============================================================================
TTP CLI PROGRAMM
==============================================================================
"""
def cli_tool():
    import argparse
    try:
        import templates as ttp_templates
        templates_exist = True
    except ImportError:
        templates_exist = False

    # form arg parser menu:
    description_text='''-d, --data      url        Data files location
-dp, --data-prefix         Prefix to add to template inputs' urls
-t, --template  template   Name of the template in "templates.py"
-o, --outputer  output     Specify output format'''
    argparser = argparse.ArgumentParser(description="Template Text Parser.", formatter_class=argparse.RawDescriptionHelpFormatter)
    argparser.add_argument('-T', '--Timing', action='store_true', dest='TIMING', default=False, help='Print timing')
    argparser.add_argument('-debug', action='store_true', dest='DEBUG', default=False, help='Print debug information')
    argparser.add_argument('--one', action='store_true', dest='ONE', default=False, help='Parse all in single process')
    argparser.add_argument('--multi', action='store_true', dest='MULTI', default=False, help='Parse multiprocess')
    run_options=argparser.add_argument_group(title='run options', description=description_text)
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
    DP = args.data_prefix        # string, to add to templates' inputs urls
    ONE = args.ONE               # boolean to indicate if run in single process
    MULTI = args.MULTI           # boolean to indicate if run in multi process

    def timing(message):
        if TIMING:
            print(round(time.time() - t0, 5), message)

    if TIMING:
        t0 = time.time()
    else:
        t0 = 0

    if templates_exist and TEMPLATE in vars(ttp_templates):
        parser_Obj = ttp(data=DATA, template=vars(ttp_templates)[TEMPLATE], DEBUG=DEBUG, data_path_prefix=DP)
    else:
        parser_Obj = ttp(data=DATA, template=TEMPLATE, DEBUG=DEBUG, data_path_prefix=DP)
    timing("Template and data descriptors loaded")

    parser_Obj.parse(one=ONE, multi=MULTI)
    timing("Data parsing finished")

    if output.lower() == 'yaml':
        parser_Obj.result(format='yaml', returner='terminal')
        timing("YAML dumped")
    elif output.lower() == 'raw':
        parser_Obj.result(format='raw', returner='terminal')
        timing("RAW dumped")
    elif output.lower() == 'json':
        parser_Obj.result(format='json', returner='terminal')
        timing("JSON dumped")
    elif output.lower() == 'pprint':
        parser_Obj.result(format='pprint', returner='terminal')
        timing("RAW pprint dumped")
    elif output:
        print("Error: Unsuported cli output format '{}', supported [yaml, json, raw, pprint]".format(output.lower()))

    timing("Done")
    
if __name__ == '__main__':
    cli_tool()