# -*- coding: utf-8 -*-

import re
import os
import logging
from xml.etree import cElementTree as ET
from multiprocessing import Process, cpu_count, JoinableQueue, Queue
from sys import version_info
from sys import getsizeof

# Initiate global variables
python_major_version = version_info.major
log = logging.getLogger(__name__)
_ttp_ = {"macro": {}, "python_major_version": python_major_version}


"""
==============================================================================
TTP LAZY IMPORT SYSTEM
==============================================================================
"""
class CachedModule():
    """Class that contains name of the function and path to module/file
    that contains that function, on first call to this class, function
    will be imported into _ttp_ dictionary, subsequent calls we call 
    function directly
    """
    
    def __init__(self, import_path, parent_dir, function_name, functions):
        self.import_path = import_path
        self.parent_dir = parent_dir
        self.function_name = function_name
        self.parent_module_functions = functions

    def load(self):
        # import cached function and insert it into _ttp_ dictionary
        abs_import = "ttp."
        if __name__ == "__main__" or __name__ == "__mp_main__": 
            abs_import = ""
        path = "{abs}{imp}".format(abs=abs_import, imp=self.import_path)
        module = __import__(path, fromlist=[None])
        setattr(module, "_ttp_", _ttp_)
        try: _name_map_ = getattr(module, "_name_map_")
        except AttributeError: _name_map_ = {}
        for func_name in self.parent_module_functions:
            name = _name_map_.get(func_name, func_name)
            _ttp_[self.parent_dir][name] = getattr(module, func_name)
            
    def __call__(self, *args, **kwargs):
        # this method invoked on CachedModule class call, triggering function import
        log.info("calling CachedModule: module '{}', function '{}'".format(self.import_path, self.function_name))
        self.load()
        # call original function
        return _ttp_[self.parent_dir][self.function_name](*args, **kwargs)

    
def lazy_import_functions():
    """function to collect a list of all files/directories within ttp module,
    parse .py files using ast and extract information about all functions
    to cache them within _ttp_ dictionary
    """
    log.info("ttp.lazy_import_functions: starting functions lazy import")
    import ast
    # get exclusion suffix     
    if python_major_version == 2:
        exclude = "_py3.py"
    elif python_major_version == 3:
        exclude = "_py2.py"
    module_files = []
    exclude_modules = ["ttp.py"]
    # create a list of all ttp module files
    for item in os.walk(os.path.dirname(__file__)):
        root, dirs, files = item
        module_files += [open("{}/{}".format(root, f), "r") for f in files if (
            f.endswith(".py") and not f.startswith("_") and not f.endswith(exclude)
            and not f in exclude_modules)]
    log.info("ttp.lazy_import_functions: files loaded, starting ast parsing")
    # get all functions from modules and cache them in _ttp_
    for module_file in module_files:
        node = ast.parse(module_file.read())
        assignments = [n  for n in node.body if isinstance(n, ast.Assign)]
        functions = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        functions = [f for f in functions if (not f.startswith("_"))]
        # get _name_map_
        _name_map_ = {}
        for assignment in assignments:
            # stop if _name_map_ already found
            if _name_map_: 
                break
            for target in assignment.targets:
                if target.id == "_name_map_":
                    _name_map_.update({
                        key.s: assignment.value.values[index].s
                        for index, key in enumerate(assignment.value.keys)
                    })   
        # fill in _ttp_ dictionary with CachedModule class
        parent_path, filename = os.path.split(module_file.name)
        _, parent_dir = os.path.split(parent_path)
        for func_name in functions:
            name = _name_map_.get(func_name, func_name)
            if not parent_dir in _ttp_:
                _ttp_[parent_dir] = {}
            path = "{}.{}".format(parent_dir, filename.replace(".py", ""))
            _ttp_[parent_dir][name] = CachedModule(path, parent_dir, name, functions)
    log.info("ttp.lazy_import_functions: finished functions lazy import")
        
            
"""
==============================================================================
MAIN TTP CLASS
==============================================================================
"""
class ttp():
    """ Template Text Parser main class to load data, templates, lookups, variables
    and dispatch data to parser object to parse in single or multiple processes,
    construct final results and run outputs.
    
    **Parameters**
        
    * ``data`` file object or OS path to text file or directory with text files with data to parse
    * ``template`` file object or OS path to text file with template
    * ``base_path`` (str) base OS path prefix to load data from for template's inputs
    * ``log_level`` (str) level of logging "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    * ``log_file`` (str) path where to save log file
    * ``vars`` dictionary of variables to make available to ttp parser
    
    Example::
    
        from ttp import ttp
        parser = ttp(data="/os/path/to/data/dir/", template="/os/path/to/template.txt")
        parser.parse()
        result = parser.result(format="json")
        print(result[0])    
    """
    
    def __init__(self, data='', template='', log_level="WARNING", log_file=None, base_path='', vars={}):
        self.__data_size = 0
        self.__datums_count = 0
        self.__data = []
        self.__templates = []
        self.base_path = base_path
        self.multiproc_threshold = 5242880 # in bytes, equal to 5MBytes
        self.vars = vars                   # dictionary of variables to add to each template vars
        self.lookups = {}
        # setup logging if used as a module
        if __name__ != '__main__':
            logging_config(log_level, log_file)
        # lazy import all functions
        lazy_import_functions()
        # check if data given, if so - load it:
        if data is not '':
            self.add_input(data=data)
        # check if template given, if so - load it
        if template is not '':
            self.add_template(template=template)
            

    def add_input(self, data, input_name='Default_Input', groups=['all']):
        """Method to load additional data to be parsed. This data will be used
        to fill in template input with input_name and parse that data against
        a list of provided groups.
        
        **Parameters**        
        
        * ``data`` file object or OS path to text file or directory with text files with data to parse
        * ``input_name`` (str) name of the input to put data in, default is *Default_Input*
        * ``groups`` (list) list of group names to use to parse this input data
        """
        # form a list of ((type, url|text,), input_name, groups,) tuples
        data_items = _ttp_["utils"]["load_files"](path=data, read=False)
        if data_items:
            self.__data.append((data_items, input_name, groups,))


    def set_input(self, data, input_name='Default_Input', groups=['all']):
        """Method to replace existing templates data with new set of data. This 
        method run clear_input first and add_input method after that.
        
        **Parameters**        
        
        * ``data`` file object or OS path to text file or directory with text files with data to parse
        * ``input_name`` (str) name of the input to put data in, default is *Default_Input*
        * ``groups`` (list) list of group names to use to parse this input data        
        """
        self.clear_input()
        self.add_input(data=data, input_name=input_name, groups=groups)
        
        
    def clear_input(self):
        """Method to delete all input data for all templates, can be used prior
        to adding new set of data to parse with same templates, instead of
        re-initializing ttp object.
        """
        self.__data = []    
        self.__data_size = 0
        self.__datums_count = 0
        for template in self.__templates:
            template.inputs = {}
        
        
    def _update_templates_with_data(self):
        """Method to add data to templates from self.__data and calculate
        overall data size and count
        """
        self.__data_size = 0
        self.__datums_count = 0
        for template in self.__templates:
            # update template inputs with data
            [template.set_input(data=i[0], input_name=i[1], groups=i[2]) for i in self.__data] 
            # get overall data size and count
            for input_name, input_obj in template.inputs.items():
                self.__datums_count += len(input_obj.data)
                # get data size
                for i in input_obj.data:
                    if i[0] == "file_name":
                        self.__data_size += os.path.getsize(i[1])
                    elif i[0] == "text_data":
                        self.__data_size += getsizeof(i[1])


    def add_template(self, template, template_name=None):
        """Method to load TTP templates into the parser.
        
        **Parameters**
        
        * ``template`` file object or OS path to text file with template
        * ``template_name`` (str) name of the template
        """
        log.debug("ttp.add_template - loading template")
        # get a list of [(type, text,)] tuples or empty list []
        items = _ttp_["utils"]["load_files"](path=template, read=True)
        for i in items:
            template_obj = _template_class(
                template_text=i[1],
                base_path=self.base_path, 
                ttp_vars=self.vars,
                name=template_name)
            # if templates are empty - no 'template' tags in template:
            if template_obj.templates == []:
                self.__templates.append(template_obj)
            else:
                self.__templates += template_obj.templates
            
            
    def add_lookup(self, name, text_data="", include=None, load="python", key=None):
        """Method to add lookup table data to all templates loaded so far. Lookup is a
        text representation of structure that can be loaded into python dictionary using one 
        of the available loaders - python, csv, ini, yaml, json.
        
        **Parameters**
        
        * ``name`` (str) name to assign to this lookup table to reference in templates
        * ``text_data`` (str) text to load lookup table/dictionary from
        * ``include`` (str) absolute or relative /os/path/to/lookup/table/file.txt
        * ``load`` (str) name of TTP loader to use to load table data
        * ``key`` (str) specify key column for csv loader to construct dictionary
        
        ``include`` can accept relative OS path - relative to the directory where TTP will be
        invoked either using CLI tool or as a module
        """
        lookup_data = _ttp_["utils"]["load_struct"](text_data=text_data,
                                               include=include, load=load, key=key)
        self.lookups.update({name: lookup_data})
        [template.add_lookup({name: lookup_data}) for template in self.__templates]

        
    def add_vars(self, vars):
        """Method to add variables to ttp and its templates to reference during parsing
        
        **Parameters**
        
        * ``vars`` dictionary of variables to make available to ttp parser        
        """
        if isinstance(vars, dict):
            self.vars.update(vars)
            [template.add_vars(vars) for template in self.__templates]
            

    def parse(self, one=False, multi=False):
        """Method to parse data with templates.

        **Parameters**
        
        * ``one`` (boolean) if set to True will run parsing in single process
        * ``multi`` (boolean) if set to True will run parsing in multiprocess
        
        By default one and multi set to False and  TTP will run parsing following below rules:
        
            1. if one or multi set to True run in one or multi process
            2. if overall data size is less then 5Mbyte, use single process
            3. if overall data size is more then 5Mbytes, use multiprocess
        
        In addition to 3 TTP will check if number of input data items more then 1, if so 
        multiple processes will be used and one process otherwise.
        """
        # add self.__data to templates and get file count and size:
        self._update_templates_with_data()
        log.info("ttp.parse: loaded datums - {}, overall size - {} bytes".format(self.__datums_count, self.__data_size))
        if one is True and multi is True:
            log.critical("ttp.parse - choose one or multiprocess parsing")
            raise SystemExit()
        elif one is True:
            self.__parse_in_one_process()
        elif multi is True:
            self.__parse_in_multiprocess()
        elif self.__data_size > self.multiproc_threshold and self.__datums_count >= 2:
            self.__parse_in_multiprocess()
        else:
            self.__parse_in_one_process()
        # run outputters defined in templates:
        [template.run_outputs() for template in self.__templates]


    def __parse_in_multiprocess(self):
        """Method to parse data in bulk by parsing each data item
        against each template and saving results in results list.
        """
        log.info("ttp.parse: parse using multiple processes")
        num_processes = cpu_count()

        for template in self.__templates:
            num_jobs = 0
            tasks = JoinableQueue()
            results_queue = Queue()
            
            workers = [_worker(tasks, results_queue, lookups=template.lookups,
                              vars=template.vars, groups=template.groups, 
                              macro_text=template.macro_text)
                       for i in range(num_processes)]
            [w.start() for w in workers]
            
            for input_name, input_obj in sorted(template.inputs.items()):
                for datum in input_obj.data:
                    task_dict = {
                        'data'          : datum,
                        'groups_indexes': input_obj.groups_indexes
                    }
                    tasks.put(task_dict)
                    num_jobs += 1

            [tasks.put(None) for i in range(num_processes)]

            # wait for all tasks to complete
            tasks.join()

            for i in range(num_jobs):
                result = results_queue.get()
                template.form_results(result)


    def __parse_in_one_process(self):
        """Method to parse data in single process, each data item parsed
        against each template and results saved in results list
        """
        log.info("ttp.parse: parse using single process")
        for template in self.__templates:
            _ttp_["macro"] = template.macro
            parserObj = _parser_class(lookups=template.lookups,
                                     vars=template.vars,
                                     groups=template.groups)
            if template.results_method.lower() == 'per_input':
                for input_name, input_obj in sorted(template.inputs.items()):
                    for datum in input_obj.data:
                        parserObj.set_data(datum, main_results={})
                        parserObj.parse(groups_indexes=input_obj.groups_indexes)
                        result = parserObj.main_results
                        template.form_results(result)
            elif template.results_method.lower() == 'per_template':
                results_data = {}
                for input_name, input_obj in sorted(template.inputs.items()):
                    for datum in input_obj.data:
                        parserObj.set_data(datum, main_results=results_data)
                        parserObj.parse(groups_indexes=input_obj.groups_indexes)
                        results_data = parserObj.main_results
                template.form_results(results_data)     


    def result(self, templates=[], structure="list", returner='self', **kwargs):
        """Method to get parsing results, supports basic filtering based on 
        templates' names, results can be formatted and returned to specified
        returner.
        
        **Parameters**
        
        * ``templates`` (list or str) names of the templates to return results for
        * ``returner`` (str) returner to use to return data - self, file, terminal
        * ``structure`` (str) structure type, valid values - ``list`` or ``dictionary``
        
        **kwargs** - can contain any attributes supported by output tags, for instance:
        
        * ``format`` (str) formatter name - yaml, json, raw, pprint, csv, table, tabulate
        * ``functions`` (str) reference functions to run results through
        
        **Example**::
        
            from ttp import ttp
            parser = ttp(data="/os/path/to/data/dir/", template="/os/path/to/template.txt")
            parser.parse()
            json_result = parser.result(format="json")[0]
            yaml_result = parser.result(format="yaml")[0]
            print(json_result) 
            print(yaml_result)    
            
        **Returns**
        
        By default template results set to *per_input* and structure set to *list*, returns list such as::
        
            [  
               [ template_1_input_1_results,
                 template_1_input_2_results,
                 ...
                 template_1_input_N_results ],
               [ template_2_input_1_results,
                 template_2_input_2_results,
                 ...
            ]       

        If template results set to *per_template* and structure set to *list*, returns list such as::
        
            [  
               [ template_1_input_1_2...N_joined_results ],
               [ template_2_input_1_2...N_joined_results ]
            ]    
            
        If template results set to *per_input* and structure set to *dictionary*, returns dictionary such as::
        
            { 
               template_1_name: [
                 input_1_results,
                 input_2_results,
                 ...
                 input_N_results 
                ],
               template_2_name: [
                 input_1_results,
                 input_2_results
                ],
                 ...
            }      

        If template results set to *per_template* and structure set to *dictionary*, returns dictionary such as::
        
            {
               template_1_name: input_1_2...N_joined_results,
               template_2_name: input_1_2...N_joined_results
            }
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
            if structure.lower() == 'list':
                return [outputter.run(template.results, macro=template.macro) for template in templates_obj]
            elif structure.lower() == 'dictionary':
                return {template.name: outputter.run(template.results, macro=template.macro) 
                        for template in templates_obj if template.name}
        else:
            if structure.lower() == 'list':
                return [template.results for template in templates_obj]
            elif structure.lower() == 'dictionary':
                return {template.name: template.results for template in templates_obj if template.name}


"""
==============================================================================
TTP PARSER MULTIPROCESSING WORKER
==============================================================================
"""
class _worker(Process):
    """Class used in multiprocessing to parse data
    """

    def __init__(self, task_queue, results_queue, lookups, vars, groups, macro_text):
        Process.__init__(self)
        self.task_queue = task_queue
        self.results_queue = results_queue
        self.macro_text = macro_text
        self.parserObj = _parser_class(lookups, vars, groups)
        
    def load_functions(self):
        lazy_import_functions()
        # load macro from text
        funcs = {}
        # extract macro with all the __builtins__ provided
        for macro_text in self.macro_text:
            try:
                funcs = _ttp_["utils"]["load_python_exec"](macro_text, builtins=__builtins__)
                _ttp_["macro"].update(funcs)
            except SyntaxError as e:
                log.error("multiprocess_worker.load_functions: syntax error, failed to load macro: \n{},\nError: {}".format(macro_text, e))    
        
    def run(self):
        self.load_functions()
        # run tasks
        while True:
            next_task = self.task_queue.get()
            # check for dead pill to stop process
            if next_task is None:
                self.task_queue.task_done()
                break
            # set parser object parameters
            self.parserObj.set_data(next_task['data'], main_results={})
            # parse and get results
            self.parserObj.parse(groups_indexes=next_task['groups_indexes'])
            result = self.parserObj.main_results
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
TTP TEMPLATE CLASS
==============================================================================
"""
class _template_class():
    """Template class to hold template data
    """
    def __init__(self, template_text, base_path='', ttp_vars={}, name=None):
        self.PATHCHAR = '.'          # character to separate path items, like ntp.clock.time, '.' is pathChar here
        # _vars_to_results_ is a dict of {pathN:[var_key1, var_keyN]} data
        # to indicate variables and patch where they should be saved in results
        self.vars = {"_vars_to_results_":{}}
        # add vars from ttp class that supplied during ttp object instantiation
        self.ttp_vars = ttp_vars
        self.vars.update(ttp_vars)
        # initialize other variables and objects:
        self.outputs = []            # list hat contains global outputs
        self.groups_outputs = []     # list that contains groups specific outputs
        self.groups = []
        self.inputs = {}
        self.lookups = {}
        self.templates = []
        self.base_path = base_path
        self.results = []
        self.name = name
        self.macro = {}                   # dictionary of macro name to function mapping
        self.results_method = 'per_input' # how to join results
        self.macro_text = [] # dict to contain macro functions text to transfer into other processes

        # load template from string:
        self.load_template_xml(template_text)

        # update inputs with the groups it has to be run against:
        self.update_inputs_with_groups()
        # update groups with output references:
        self.update_groups_with_outputs()

        if log.isEnabledFor(logging.DEBUG):
            from yaml import dump
            #log.debug("Template self.outputs: \n{}".format(dump(self.outputs)))
            #log.debug("Template self.groups_outputs: \n{}".format(dump(self.groups_outputs)))
            #log.debug("Template self.vars: \n{}".format(dump(self.vars)))
            #log.debug("Template self.groups: \n{}".format(dump(self.groups)))
            [input.debug() for input in self.inputs.values()]
            #log.debug("Template self.lookups: \n{}".format(self.lookups))
            #log.debug("Template self.templates: \n{}".format(self.templates))

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
        for output in self.outputs:
            self.results = output.run(self.results, macro=self.macro)

    def form_results(self, result):
        """Method to add results to self.results
        """
        if not result:
            return
        if '_anonymous_' in result:
            self.results.append(result['_anonymous_'])
        else:
            if isinstance(result, list):
                self.results += result
            else:
                self.results.append(result)

    def set_input(self, data=None, input_name='Default_Input', groups='', preference='group_inputs'):
        """
        Method to set data for template input
        Args:
            data (list): list of (data_name, data_path,) tuples
            input_name (str): name of the input
            groups (list): list of groups to use for that input
        """
        if input_name in self.inputs:
            self.inputs[input_name].add_data(data=data, groups=groups, preference=preference)
        # add new input to self.inputs:
        else:
            input = _input_class(input_name=input_name, base_path=self.base_path, 
                                 template_obj=self, groups=groups, preference=preference)
            input.add_data(data=data)
            self.inputs.update({input.name: input})
            

    def update_inputs_with_groups(self):
        """
        Method to update self.inputs with groups_indexes
        """
        for G in self.groups:
            for input_name in G.inputs:
                input_name = self.base_path + input_name.lstrip('.')
                # add new input
                if input_name not in self.inputs:
                    data_items = _ttp_["utils"]["load_files"](path=input_name, read=False)
                    # skip 'text_data' from data as if by the time this method runs
                    # no input with such name found it means that group input is os path
                    # string and text_data will be returned by self.utils.load_files
                    # only if no such path exists, hence text_data does not make sense here
                    data = [i for i in data_items if 'text_data' not in i[0]]
                    input = _input_class(input_name=input_name, template_obj=self, preference='group_inputs')
                    input.add_data(data=data)
                    self.inputs.update({input.name: input})
                # add group index to input group_inputs
                self.inputs[input_name].group_inputs.append(G.grp_index)
        [input_obj.check_preference() for input_obj in self.inputs.values()]
            

    def update_groups_with_outputs(self):
        """Method to replace output names in group with
        output index from self.groups_outputs, also move
        output from self.outputs to group specific
        self.groups_outputs
        """
        for G in self.groups:
            for output_index, grp_output in enumerate(G.outputs):
                group_output_found = False
                # search through global outputs:
                for glob_index, glob_output in enumerate(self.outputs):
                    if glob_output.name == grp_output:
                        self.groups_outputs.append(self.outputs.pop(glob_index))
                        G.outputs[output_index] = self.groups_outputs[-1]
                        group_output_found = True
                # go to next output if this output found:
                if group_output_found:
                    continue
                # try to find output in group specific outputs:
                for index, output in enumerate(self.groups_outputs):
                    if output.name == grp_output:
                        G.outputs[output_index] = output
                        group_output_found = True
                # print error message if no output found:
                if not group_output_found:
                    G.outputs.pop(output_index)
                    log.error("template.update_groups_with_outputs: group '{}' - output '{}' not found.".format(G.name, grp_output))

    def get_template_attributes(self, element):

        def extract_name(O):
            if not self.name:
                self.name = O
            
        def extract_base_path(O):
            self.base_path = O
    
        def extract_results_method(O):
            self.results_method = O
        
        def extract_pathchar(O):
            self.PATHCHAR = str(O)

        opt_funcs = {
        'name'      : extract_name,
        'base_path' : extract_base_path,
        'results'   : extract_results_method,
        'pathchar'  : extract_pathchar
        }

        [opt_funcs[name](options) for name, options in element.attrib.items()
         if name in opt_funcs]

    def load_template_xml(self, template_text):

        def parse_vars(element):
            # method to parse vars data
            vars = _ttp_["utils"]["load_struct"](element.text, **element.attrib)
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
            input = _input_class(element, self.base_path, template_obj=self)
            if input.name in self.inputs:
                self.inputs[input.name].add_data(data=input.data, groups=input.attributes["groups"], 
                                                 preference=input.attributes["preference"])
                del input
            else:
                self.inputs[input.name] = input

        def parse_group(element, grp_index):
            self.groups.append(
                _group_class(
                    element,
                    top=True,
                    pathchar=self.PATHCHAR,
                    vars=self.vars,
                    grp_index=grp_index
                )
            )

        def parse_lookup(element):
            try:
                name = element.attrib['name']
            except KeyError:
                log.warning("Lookup 'name' attribute not found but required, skipping it")
                return
            lookup_data = _ttp_["utils"]["load_struct"](element.text, **element.attrib)
            if lookup_data is None:
                return
            self.lookups[name] = lookup_data

        def parse_template(element):
            self.templates.append(_template_class(
                template_text=ET.tostring(element, encoding="UTF-8"),
                base_path=self.base_path,
                ttp_vars=self.ttp_vars)
            )

        def parse_macro(element):
            funcs = {}
            # extract macro with all the __builtins__ provided
            try:
                funcs = _ttp_["utils"]["load_python_exec"](element.text, builtins=__builtins__)
                self.macro.update(funcs)
                # save macro text to be able to restore macro functions within another process
                self.macro_text.append(element.text)
            except SyntaxError as e:
                log.error("template.parse_macro: syntax error, failed to load macro: \n{},\nError: {}".format(element.text, e))
            
        def parse__anonymous_(element):
            elem = ET.XML('<g name="_anonymous_">\n{}\n</g>'.format(element.text))
            parse_group(elem, grp_index=0)

        def invalid(C):
            log.warning("template.parse: invalid tag '{}'".format(C.tag))

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
            [parse_lookup(L) for L in tags['lookups']]
            [parse_group(g, grp_index) for grp_index, g in enumerate(tags['groups'])]
            [parse_input(i) for i in tags['inputs']]

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
TTP INPUT CLASS
==============================================================================
"""
class _input_class():
    """Template input class to hold inputs data
    """
    def __init__(self, element=None, base_path="", template_obj=None,
                 input_name='Default_Input', groups='all', preference='group_inputs'):
        self.attributes = {
            'base_path': base_path,
            'load': 'python',
            'groups': groups,
            'preference': preference,
            'extensions': [],
            'filters': [],
            'urls': []            
        }
        self.template_obj = template_obj
        self.data = []
        self.groups_indexes = []
        self.group_inputs = []
        self.name = input_name
        self.funcs = []
        # extract attributes from input tag
        if element is not None:
            self.get_attributes(data=element.attrib, element_text=element.text)
            self.load_data(element.text)
        # get groups indexes if not extracted so far
        if not self.groups_indexes:
            self.get_attributes(data={
                'groups': self.attributes['groups']
            })
        
    def get_attributes(self, data, element_text=""):
        
        def extract_name(O):
            self.name = O.strip()
        
        def extract_load(O):
            self.attributes["load"] = O.strip()
            if self.attributes["load"] != 'text':
                attribs = _ttp_["utils"]["load_struct"](element_text, **data)
                self.get_attributes(data=attribs)
        
        def extract_groups(O):
            if isinstance(O, list):
                self.attributes["groups"] = O
            else:
                self.attributes["groups"] = [i.strip() for i in O.split(",")]
            if 'all' in self.attributes["groups"]:
                groups_indexes = [grp_obj.grp_index for grp_obj in self.template_obj.groups if not grp_obj.inputs]
            else:
                groups_indexes = [grp_obj.grp_index for grp_obj in self.template_obj.groups 
                                  if grp_obj.name in self.attributes["groups"] and not grp_obj.inputs] 
            self.groups_indexes += sorted(list(set(groups_indexes)))
            
        def extract_preference(O):
            self.attributes["preference"] = O.strip()
            
        def extract_extensions(O):
            if isinstance(O, str): 
                self.attributes["extensions"]=[O]
            else:
                self.attributes["extensions"]=O
                
        def extract_filters(O):
            if isinstance(O, str): 
                self.attributes["filters"]=[O]
            else:
                self.attributes["filters"]=O
                
        def extract_urls(O):
            if isinstance(O, str): 
                self.attributes["urls"]=[O]
            else:
                self.attributes["urls"]=O
        
        # group attributes extract functions dictionary:
        options = {
        'name'        : extract_name,
        'load'        : extract_load,
        'groups'      : extract_groups,
        'preference'  : extract_preference,
        'extensions'  : extract_extensions,
        'filters'     : extract_filters,
        'url'         : extract_urls
        }
        functions = {
        }

        # extract attributes from element tag attributes   
        for attr_name, attributes in data.items():
            if attr_name.lower() in options: options[attr_name.lower()](attributes)
            elif attr_name.lower() in functions: functions[attr_name.lower()](attributes)
            else: self.attributes[attr_name] = attributes    
                
    def load_data(self, element_text):
        if self.attributes["load"] == 'text':
            self.data = [('text_data', element_text)]
            return
        elif not self.attributes["urls"]:
            log.critical("template.parse_input: Input '{}', required 'url' parameter not given".format(self.name))
            raise SystemExit()
        # load data:
        for url in self.attributes["urls"]:
            url = self.attributes["base_path"] + url.lstrip('.')
            datums = _ttp_["utils"]["load_files"](path=url, extensions=self.attributes["extensions"], 
                                                  filters=self.attributes["filters"], read=False)
            self.data += datums
            
    def add_data(self, data=[], **kwargs):
        # get attributes:
        if kwargs:
            self.get_attributes(kwargs)
        # add data:
        if data:
            [self.data.append(d_item) for d_item in data if not d_item in self.data]
                
    def check_preference(self):
        if self.attributes['preference'] == 'group_inputs' and self.group_inputs:
            self.groups_indexes = self.group_inputs
        elif self.attributes['preference'] == 'input_groups':
            pass
        elif self.attributes['preference'] == 'merge' and self.group_inputs:
            self.groups_indexes += self.group_inputs
        self.groups_indexes = sorted(list(set(self.groups_indexes)))
        
    def debug(self):
        from pprint import pformat
        text = "Template '{}', Input '{}' content:\n{}".format(self.template_obj.name, self.name, pformat(vars(self), indent=4))
        log.debug(text)
            
            
"""
==============================================================================
GROUP CLASS
==============================================================================
"""
class _group_class():
    """group class to store template group objects data
    """

    def __init__(self, element, grp_index=0, top=False, path=[], pathchar=".",
                 vars={}, impot_list=[]):
        """Init method
        Attributes:
            element : xml ETree element to parse
            top (bool): to indicate that group is a top xml ETree group
            path (list): list containing results tree path, have to copy it otherwise
                it got overridden by recursion
            defaults (dict): contains group variables' default values
            runs (dict): to sotre modified defaults during parsing run
            default (str): group all variables' default value if no more specific default value given
            inputs (list): list of inputs names this group should be used for
            outputs (list): list of outputs to run for this group
            funcs (list): list of functions to run against group results
            method (str): indicate type of the group - [group | table]
            start_re (list): contains list of group start regular epressions
            end_re (list): contains list of group end regular expressions
            children (list): contains child group objects
            vars (dict): variables dictionary from template class
            grp_index (int): uniqie index of the group
        """
        self.pathchar = pathchar
        self.top      = top
        self.path     = list(path)
        self.defaults = {}
        self.runs     = {}
        self.default  = "_Not_Given_"
        self.outputs  = []
        self.funcs    = []
        self.method   = 'group'
        self.start_re = []
        self.end_re   = []
        self.re       = []
        self.children = []
        self.name     = ''
        self.vars     = vars
        self.grp_index = grp_index
        self.inputs = []
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
            if self.top: self.inputs = [(i.strip()) for i in O.split(',')]

        def extract_output(O):
            if self.top: self.outputs = [(i.strip()) for i in O.split(',')]

        def extract_name(O):
            self.path = self.path + O.split(self.pathchar)
            self.name = '.'.join(self.path)
            
        def extract_macro(O):
            if isinstance(O, str):
                for i in O.split(','):
                    self.funcs.append({
                        'name': 'macro',
                        'args': [i.strip()]
                    })
            elif isinstance(O, dict):
                self.funcs.append(O)          

        def extract_to_ip(O):
            if isinstance(O, str):
                attribs = _ttp_["utils"]["get_attributes"]('attribs({})'.format(O))
                self.funcs.append({
                    'name': 'to_ip',
                    'args': attribs[0]['args'],
                    'kwargs': attribs[0]['kwargs']
                })
            elif isinstance(O, dict):
                self.funcs.append(O)              
     
        def extract_functions(O):
            funcs = _ttp_["utils"]["get_attributes"](O)
            for i in funcs:
                func_name = i['name']
                if func_name in functions: 
                    functions[func_name](i)
                else: 
                    self.funcs.append(i)

        # group attributes extract functions dictionary:
        options = {
        'method'      : extract_method,
        'input'       : extract_input,
        'output'      : extract_output,
        'name'        : extract_name,
        'default'     : extract_default
        }
        functions = {
        'macro'       : extract_macro,
        'functions'   : extract_functions,
        'to_ip'       : extract_to_ip    
        }

        for attr_name, attributes in data.items():
            if attr_name.lower() in options: options[attr_name.lower()](attributes)
            elif attr_name.lower() in functions: functions[attr_name.lower()](attributes)
            else:
                self.funcs.append({'name': attr_name.lower(),
                                   'args': [i.strip() for i in attributes.split(',')]})


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
                log.warning("group.get_regexes: variable not found in line: '{}'".format(line))
                continue
            varaibles_matches.append({'variables': match, 'line': line})

        for i in varaibles_matches:
            regex = ''
            variables = {}
            action = 'add'
            is_line = False
            skip_regex = False
            for variable in i['variables']:
                variableObj = _variable_class(variable, i['line'], group=self)

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

                # modify save action only if it is not start or startempty already:
                if "start" not in action:
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
                if not 'start' in re_dict['ACTION']:
                    re_dict['ACTION'] ='start'
                self.start_re.append(re_dict)
            elif self.method == 'table':
                if not 'start' in re_dict['ACTION']:
                    re_dict['ACTION'] = 'start'
                self.start_re.append(re_dict)
            elif "start" in re_dict['ACTION']:
                self.start_re.append(re_dict)
            elif "end" in re_dict['ACTION']:
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
                vars=self.vars))
            # get regexes from tail
            if g.tail.strip():
                self.get_regexes(data=g.tail, tail=True)


    def set_runs(self):
        """runs - default variable values during group
        parsing run, have to preserve original defaults
        as values in defaults dictionried can change for 'set'
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
    def __init__(self, variable, line, group=''):
        """
        Args:
            variable (str): contains variable content
            line(str): original line, need it here to form "set" actions
        """

        # initiate variableClass object variables:
        self.variable = variable
        self.LINE = line                             # original line from template
        self.functions = []                          # actions and conditions list

        self.SAVEACTION = 'add'                      # to store action to do with results during saving
        self.group = group                           # template object current group to save some vars
        self.IS_LINE = False                         # to indicate that variable is _line_ regex
        self.skip_variable_dict = False              # will be set to true for 'ignore'
        self.skip_regex_dict = False                 # will be set to true for 'set'
        self.var_res = []                            # list of variable regexes

        # add formatters:
        self.REs = _ttp_patterns()

        # form attributes - list of dictionaries:
        self.attributes = _ttp_["utils"]["get_attributes"](variable)
        self.var_dict = self.attributes.pop(0)
        self.var_name = self.var_dict['name']

        # add defaults
        # list of variables names that should not have defaults:
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
            self.SAVEACTION='start'
            if self.var_name == '_start_':
                self.SAVEACTION='startempty'

        def extract__end_(data):
            self.SAVEACTION='end'

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
            self.SAVEACTION='join'

        def extract__line_(data):
            self.functions.append(data)
            self.SAVEACTION='join'
            self.IS_LINE=True

        def extract_ignore(data):
            self.skip_variable_dict = True

        def extract_chain(data):
            """add items from chain to variable attributes and functions
            """
            variable_value = self.group.vars.get(data['args'][0], None)
            if variable_value is None:
                log.error("match_variable.extract_chain: match variable - '{}', chain var '{}' not found".format(self.var_name, data['args'][0]))
                return
            if isinstance(variable_value, str):
                attributes =  _ttp_["utils"]["get_attributes"](variable_value)
            elif isinstance(variable_value, list):
                attributes = []
                for i in variable_value:
                    i_attribs = _ttp_["utils"]["get_attributes"](i)
                    attributes += i_attribs
            for i in attributes:
                name = i['name']
                if name in extract_funcs:
                    extract_funcs[name](i)
                else:
                    self.functions.append(i)
            
        def extract_re(data):
            regex = data['args'][0]
            re_from_var = self.group.vars.get(regex, None)
            # check group variables
            if re_from_var:
                self.var_res.append(re_from_var)
            # check built int RE patterns
            elif regex in self.REs.patterns:
                self.var_res.append(self.REs.patterns[regex])
            # use regex as is
            else:
                self.var_res.append(regex)
            
        extract_funcs = {
        'ignore'        : extract_ignore,
        '_start_'       : extract__start_,
        '_end_'         : extract__end_,
        '_line_'        : extract__line_,
        'chain'         : extract_chain,
        'set'           : extract_set,
        'default'       : extract_default,
        'joinmatches'   : extract_joinmatches,
        # regex formatters:
        're'       : extract_re,
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
            # form indent to honor leading space characters like \t or \s:
            first_non_space_char_index = len(self.LINE) - len(self.LINE.lstrip())
            indent = self.LINE[:first_non_space_char_index]
            # form regex:
            self.regex = esc_line
            self.regex = indent + self.regex               # reconstruct indent
            self.regex = '\\n' + self.regex + ' *(?=\\n)'  # use lookahead assertion for end of line and match any number of trailing spaces
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

        # for variables like {{ ignore }}
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

        # form variable regex by replacing escaped variable, if it is in regex,
        # except for the case if variable is "ignore" as it already was replaced
        # in regex_ignore function:
        if self.var_name != "ignore":
            self.regex = self.regex.replace(esc_var,
                '(?P<{}>(?:{}))'.format(self.var_name, ')|(?:'.join(self.var_res),1)
            )

        # after regexes formed we can delete unnecessary variables:
        if log.isEnabledFor(logging.DEBUG) == False:
            del self.attributes, esc_line
            del self.LINE, self.skip_defaults
            del self.var_dict, self.REs, self.var_res

        return self.regex



"""
==============================================================================
TTP PARSER OBJECT
==============================================================================
"""
class _parser_class():
    """Parser Object to run parsing of data and constructong resulted dictionary/list
    """
    def __init__(self, lookups, vars, groups):
        self.lookups = lookups
        self.original_vars = vars
        self.groups = groups


    def set_data(self, D, main_results={}):
        """Method to load data:
        Args:
            D (tuple): items are dict of (data_type, data_path,)
        """
        self.main_results = main_results
        if D[0] == 'text_data':
            self.DATATEXT = '\n' + D[1] + '\n\n'
            self.DATANAME = 'text_data'
        else:
            data = _ttp_["utils"]["load_files"](path=D[1], read=True)
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
        # run variable getters functions to update vars with functions results:
        self.run_functions()
        # create groups' runs dictionaries to hold defaults updated with var values
        [G.set_runs() for G in self.groups]
        # re initiate _ttp_ dictionary parser object
        _ttp_["parser_object"] = self


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
                    result = _ttp_["variable"][VARvalue](self.DATATEXT, self.DATANAME)
                    self.vars['globals']['vars'].update({VARname: result})
                except KeyError:
                    continue
                except:
                    log.error("ttp_parser.run_functions: {} function failed".format(VARvalue))


    def parse(self, groups_indexes):
        # groups_indexes - list of group indexes to run
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
                            data, flag = _ttp_["match"][func_name](data, *args, **kwargs)
                        except KeyError:
                            try: # try data built-in function. e.g. if data is string, can run data.upper()
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
                                log.error("ttp_parser.check_matches: match variable '{}' function failed, data '{}', error '{}'".format(func_name, data, e))
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
                    # run flags
                    if 'new_field' in flags:
                        result.update(flags['new_field'])
                # skip not start regexes that evaluated to False
                if result is False and not regex['ACTION'].startswith('start'):
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
        for group_index in groups_indexes:
            group = self.groups[group_index]
            # get results for groups with global only outputs:
            if group.outputs == []:
                unsort_rslts.append(run_re(group, results={}))
            # get results for groups with group specific results:
            else:
                # form a tuple of (results, group.outputs,)
                grps_unsort_rslts.append(
                    (run_re(group, results={}), group.outputs,)
                )
                    
        # update groups runs with most recent variables
        self.update_groups_runs(self.vars['globals']['vars'])
        
        # sort results for groups with global outputs
        [ raw_results.append(
          [group_result[key] for key in sorted(list(group_result.keys()))]
          ) for group_result in unsort_rslts if group_result ]
        # form results for global groups:
        RSLTSOBJ = _results_class()
        RSLTSOBJ.make_results(self.vars['globals']['vars'], raw_results, main_results=self.main_results)
        self.main_results = RSLTSOBJ.results

        # sort results for groups with group specific outputs
        [ grps_raw_results.append(
        # tuple item that contains group.outputs:
        ([group_result[0][key] for key in sorted(list(group_result[0].keys()))], group_result[1],) 
        ) for group_result in grps_unsort_rslts if group_result[0] ]
        # form results for groups specific results with running groups through outputs:
        for grp_raw_result in grps_raw_results:
            RSLTSOBJ = _results_class()
            RSLTSOBJ.make_results(self.vars['globals']['vars'], [grp_raw_result[0]], main_results={})
            grp_result = RSLTSOBJ.results
            for output in grp_raw_result[1]:
                grp_result = output.run(data=grp_result)
            # transform results into list:
            if isinstance(self.main_results, dict):
                if self.main_results:
                    self.main_results = [self.main_results]
                else:
                    self.main_results = []
            # save results into global results list:
            self.main_results.append(grp_result)



"""
==============================================================================
TTP results FORMATTER OBJECT
==============================================================================
"""
class _results_class():
    """
    Class to save results and do actions with them.
    Args:
        self.dyn_path_cache (dict): used to store dynamic path variables
    """
    def __init__(self):
        self.results = {}
        self.GRPLOCK = {'LOCK': False, 'GROUP': ()} # GROUP - path tuple of locked group
        self.record={
            'result'     : {},
            'PATH'       : [],
            'FUNCTIONS' : []
        }
        self.dyn_path_cache={}
        _ttp_["results_object"] = self
        

    def make_results(self, vars, raw_results, main_results):
        self.results = main_results
        self.vars=vars
        saveFuncs={
            'start'      : self.start,       # start - to start new group;
            'add'        : self.add,         # add - to add data to group, default action;
            'startempty' : self.startempty,  # startempty - to start new empty group in case if _start_ found;
            'end'        : self.end,         # end - to explicitly signal the end of group to LOCK it;
            'join'       : self.join         # join - to join results for given variable, e.g. joinmatches;
        }
        # save _vars_to_results_ to results if any:
        if raw_results: self.save_vars(vars)
        
        # iterate over group results and form results structure:
        for group_results in raw_results:
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
                        if item_re['ACTION'].startswith('start'):
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
                    elif re['ACTION'].startswith('start') and result_data is not False:
                        self.GRPLOCK['LOCK'] = False
                        self.GRPLOCK['GROUP'] = ()
                    else:
                        continue
                # Save results:
                saveFuncs[re['ACTION']](
                    result     = result_data,
                    PATH       = list(group.path),
                    DEFAULTS   = group.runs,
                    FUNCTIONS  = group.funcs,
                    REDICT     = re
                )
        # check the last group:
        if self.record['result'] and self.processgrp() is not False:
            self.save_curelements()


    def save_vars(self, vars):
        # need to sort keys first to introduce deterministic behaviour
        sorted_pathes = sorted(list(vars['_vars_to_results_'].keys()))
        for path_item in sorted_pathes:
            # skip empty path items:
            if not path_item: continue
            vars_names = vars['_vars_to_results_'][path_item]
            result = {}
            for var_name in vars_names:
                result[var_name] = vars[var_name]
            self.record = {
                'result'     : result,
                'PATH'       : [i.strip() for i in path_item.split('.')],
            }
            processed_path = self.form_path(self.record['PATH'])
            if processed_path:
                self.record['PATH'] = processed_path
            else:
                continue
            self.save_curelements()
        # set record to default value:
        self.record={'result': {}, 'PATH': [], 'FUNCTIONS': []}


    def value_to_list(self, DATA, PATH, result):
        """recursive function to get value at given PATH and transform it into the list
        Example:
            DATA={1:{2:{3:{4:5, 6:7}}}} and PATH=(1,2,3)
            running this function will transform DATA to {1:{2:{3:[{4:5, 6:7}]}}}
        Args:
            DATA (dict): data to add to the DATA
            PATH (list): list of path keys
            result : dict or list that contains results
        Returns:
            transformed DATA with list at given PATH and appended results to it
        """
        if PATH:
            name=str(PATH[0]).rstrip('*')
            if isinstance(DATA, dict):
                if name in DATA:
                    DATA[name]=self.value_to_list(DATA[name], PATH[1:], result)
                    return DATA
            elif isinstance(DATA, list):
                if name in DATA[-1]:
                    DATA[-1][name]=self.value_to_list(DATA[-1][name], PATH[1:], result)
                    return DATA
        else:
            return [DATA, result] # for resulting list - value at given PATH transformed into list with result appended to it


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


    def save_curelements(self):
        """Method to save current group results in self.results
        """
        RSLT = self.record['result']
        PATH = self.record['PATH']
        # get ELEMENT from self.results by PATH
        E = self.dict_by_path(PATH=PATH, ELEMENT=self.results)
        if isinstance(E, list):
            E.append(RSLT)
        elif isinstance(E, dict):
            # check if PATH endswith "**" - update result's ELEMENET without converting it into list:
            if len(PATH[-1]) - len(str(PATH[-1]).rstrip('*')) == 2:
                E.update(RSLT)
            # to match all the other cases, like templates without "**" in path:
            elif E != {}:
                # transform ELEMENT dict to list and append data to it:
                self.results = self.value_to_list(DATA=self.results, PATH=PATH, result=RSLT)
            else:
                E.update(RSLT)


    def start(self, result, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
        if self.record['result'] and self.processgrp() != False:
            self.save_curelements()
        self.record = {
            'result'     : DEFAULTS.copy(),
            'DEFAULTS'   : DEFAULTS,
            'PATH'       : PATH,
            'FUNCTIONS' : FUNCTIONS
        }
        self.record['result'].update(result)


    def startempty(self, result, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
        if self.record['result'] and self.processgrp() != False:
            self.save_curelements()
        self.record = {
            'result'     : DEFAULTS.copy(),
            'DEFAULTS'   : DEFAULTS,
            'PATH'       : PATH,
            'FUNCTIONS' : FUNCTIONS
        }


    def add(self, result, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
        if self.GRPLOCK['LOCK'] == True: return

        if self.record['PATH'] == PATH: # if same path - save into self.record
            self.record['result'].update(result)
        # if different path - that can happen if we have
        # group ended and result actually belong to another group, hence have
        # save directly into results
        else:
            processed_path = self.form_path(PATH)
            if processed_path is False:
                return
            ELEMENT = self.dict_by_path(PATH=processed_path, ELEMENT=self.results)
            if isinstance(ELEMENT, dict):
                ELEMENT.update(result)
            elif isinstance(ELEMENT, list):
                ELEMENT[-1].update(result)


    def join(self, result, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
        joinchar = '\n'
        for varname, varvalue in result.items():
            # skip vars that were added to results on the go
            if not varname in REDICT['VARIABLES']: 
                continue
            for item in REDICT['VARIABLES'][varname].functions:
                if item['name'] == 'joinmatches':
                    if item['args']:
                        joinchar = item['args'][0]
                        break
        # join results:
        for k in result.keys():
            if k in self.record['result']:                           # if we already have results
                if k in DEFAULTS:
                    if self.record['result'][k] == DEFAULTS[k]:      # check if we have default value
                        self.record['result'][k] = result[k]         # replace default value with new value
                        continue
                if isinstance(self.record['result'][k], str):
                    self.record['result'][k] += joinchar + result[k] # join strings
                elif isinstance(self.record['result'][k], list):
                    if isinstance(result[k], list):
                        self.record['result'][k] += result[k]        # join lists
                    else:
                        self.record['result'][k].append(result[k])   # append to list                            
                else: # transform result to list and append new result to it
                    self.record['result'][k] = [ self.record['result'][k], result[k] ]
            else:
                self.record['result'][k] = result[k]                 # if first result


    def end(self, result, PATH, DEFAULTS={}, FUNCTIONS=[], REDICT=''):
        # action to end current group by locking it
        self.GRPLOCK['LOCK'] = True
        self.GRPLOCK['GROUP'] = list(PATH)


    def form_path(self, path):
        """Method to form dynamic path
        """
        for index, path_item in enumerate(path):
            match=re.findall('{{\s*(\S+)\s*}}', path_item)
            if not match:
                continue
            for m in match:
                pattern='{{\s*' + m + '\s*}}'
                if m in self.record['result']:
                    self.dyn_path_cache[m] = self.record['result'][m]
                    repl = self.record['result'].pop(m)
                    path_item = re.sub(pattern, repl, path_item)
                elif m in self.dyn_path_cache:
                    path_item = re.sub(pattern, self.dyn_path_cache[m], path_item)
                elif m in self.vars:
                    path_item = re.sub(pattern, self.vars[m], path_item)
                else:
                    return False
            path[index] = path_item
        return path


    def processgrp(self):
        """Method to process group results
        """
        for item in self.record['FUNCTIONS']:
            func_name = item['name']
            args = item.get('args', [])
            kwargs = item.get('kwargs', {})
            try: # try group functions
                self.record['result'], flags = _ttp_["group"][func_name](self.record['result'], *args, **kwargs)
            except KeyError:
                log.error("ttp_results.processgrp: group '{}' function failed, data '{}'".format(func_name, self.record['result']))
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
            if 'terminal' will print data to terminal
        format (str): output format indicator on how to format data
        url (str): path to where to save data to e.g. OS path
        filename (str): name of hte file
        method (str): how to save results, in separate files or in one file
    """
    def __init__(self, element=None, **kwargs):
        from time import strftime
        ctime = strftime("%Y-%m-%d_%H-%M-%S")
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
        self.funcs = []
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
                log.critical("output.extract_returner: unsupported returner '{}'. Supported: {}. Exiting".format(O, supported_returners))
                raise SystemExit()

        def extract_format(O):
            supported_formats = ['raw', 'yaml', 'json', 'csv', 'jinja2', 'pprint', 'tabulate', 'table', 'excel', "graph"]
            if O in supported_formats:
                self.attributes['format'] = O
            else:
                log.critical("output.extract_format: unsupported format '{}'. Supported: {}. Exiting".format(O, supported_formats))
                raise SystemExit()

        def extract_load(O):
            self.attributes['load'] = _ttp_["utils"]["load_struct"](self.element.text, **self.element.attrib)

        def extract_filename(O):
            """File name can contain time formatters supported by strftime      
            """
            from time import strftime
            self.attributes['filename'] = strftime(O)

        def extract_method(O):
            supported_methods = ['split', 'join']
            if O in supported_methods:
                self.attributes['method'] = O
            else:
                log.critical("output.extract_method: unsupported file returner method '{}'. Supported: {}. Exiting".format(O, supported_methods))
                raise SystemExit()

        def extract_functions(O):
            funcs = _ttp_["utils"]["get_attributes"](O)
            for i in funcs:
                name = i['name']
                if name in functions:
                    functions[name](i)
                else:
                    log.error('output.extract_functions: unknown output function: "{}"'.format(name))

        def extract_macro(O):
            if isinstance(O, str):
                for i in O.split(','):
                    self.funcs.append({
                        'name': 'macro',
                        'args': [i.strip()]
                    })
            elif isinstance(O, dict):
                self.funcs.append(O)
                
        def extract_is_equal(O):
            if isinstance(O, dict):
                self.funcs.append(O)

        def extract_format_attributes(O):
            """Extract formatter attributes
            """
            format_attributes = _ttp_["utils"]["get_attributes"](
                            'format_attributes({})'.format(O))
            self.attributes['format_attributes'] = {
                'args': format_attributes[0]['args'],
                'kwargs': format_attributes[0]['kwargs']
            }

        def extract_path(O):
            self.attributes['path'] = [i.strip() for i in O.split('.')]

        def extract_headers(O):
            if isinstance(O, str):
                self.attributes['headers'] = [i.strip() for i in O.split(',')]
            else:
                self.attributes['headers'] = O

        def extract_dict_to_list(O):
            if isinstance(O, str):
                dict_to_list_attrs = _ttp_["utils"]["get_attributes"](
                    'dict_to_list({})'.format(O))
                self.funcs.append(dict_to_list_attrs[0])
            elif isinstance(O, dict):
                self.funcs.append(O)
            
        def extract_traverse(O):
            self.funcs.append(O)

        options = {
        'name'           : extract_name,
        'returner'       : extract_returner,
        'format'         : extract_format,
        'load'           : extract_load,
        'filename'       : extract_filename,
        'method'         : extract_method,
        'format_attributes' : extract_format_attributes,
        'path'           : extract_path,
        'headers'        : extract_headers
        }
        functions = {
        'functions'      : extract_functions,
        'is_equal'       : extract_is_equal,
        'macro'          : extract_macro,
        'dict_to_list'   : extract_dict_to_list,
        'traverse'       : extract_traverse
        }     
        for attr_name, attributes in data.items():
            if attr_name.lower() in options: options[attr_name.lower()](attributes)
            elif attr_name.lower() in functions: functions[attr_name.lower()](attributes)
            else: self.attributes[attr_name] = attributes

    def run(self, data, macro={}):
        _ttp_["output_object"] = self
        if macro:
            _ttp_["macro"] = macro
        returners = self.attributes['returner']
        format = self.attributes['format']
        results = data
        # run fuctions:
        for item in self.funcs:
            func_name = item['name']
            args = item.get('args', [])
            kwargs = item.get('kwargs', {})
            try:
                results = _ttp_["output"][func_name](results, *args, **kwargs)
            except KeyError:
                log.error("ttp_output.run: output '{}' function not found.".format(func_name))
        # format data using requested formatter
        results = _ttp_["formatters"][format](results)
        # run returners
        [_ttp_["returners"][returner](results) for returner in returners]
        # check if need to return processed data:
        if self.return_to_self is True:
            return results        
        # return unmodified data:
        return data
        
        
"""
==============================================================================
TTP LOGGING SETUP
==============================================================================
"""
def logging_config(LOG_LEVEL, LOG_FILE):
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL.upper() in valid_log_levels:
        logging.basicConfig(
            format='%(asctime)s.%(msecs)d [TTP %(levelname)s] %(lineno)d; %(message)s', 
            datefmt='%m/%d/%Y %I:%M:%S',
            level=LOG_LEVEL.upper(),
            filename=LOG_FILE,
            filemode='w'
        )


"""
==============================================================================
TTP CLI PROGRAMM
==============================================================================
"""
def cli_tool():
    import argparse
    import time
    # import templates
    abs_import = "ttp."
    if __name__ == "__main__": 
        abs_import = ""
    file = "{}templates.templates".format(abs_import)
    ttp_templates = __import__(file, fromlist=[None])

    # form argparser menu:
    description_text='''-d,  --data         Data files location
-dp, --data-prefix  Prefix to add to template inputs' urls
-t,  --template     Name of the template in "templates.py"
-o,  --outputer     Specify output format - yaml, json, raw, pprint
-l,  --logging      Set logging level - "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
-lf, --log-file     Path to save log file
-T,  --Timing       Print simple timing info
--one               Parse using single process
--multi             Parse using multiple processes'''
    argparser = argparse.ArgumentParser(description="Template Text Parser, version 0.0.1.", formatter_class=argparse.RawDescriptionHelpFormatter)
    run_options=argparser.add_argument_group(description=description_text)
    run_options.add_argument('--one', action='store_true', dest='ONE', default=False, help=argparse.SUPPRESS)
    run_options.add_argument('--multi', action='store_true', dest='MULTI', default=False, help=argparse.SUPPRESS)
    run_options.add_argument('-T', '--Timing', action='store_true', dest='TIMING', default=False, help=argparse.SUPPRESS)
    run_options.add_argument('-d', '--data', action='store', dest='DATA', default='', type=str, help=argparse.SUPPRESS)
    run_options.add_argument('-dp', '--data-prefix', action='store', dest='data_prefix', default='', type=str, help=argparse.SUPPRESS)
    run_options.add_argument('-t', '--template', action='store', dest='TEMPLATE', default='', type=str, help=argparse.SUPPRESS)
    run_options.add_argument('-o', '--outputter', action='store', dest='output', default='', type=str, help=argparse.SUPPRESS)
    run_options.add_argument('-l', '--logging', action='store', dest='LOG_LEVEL', default='WARNING', type=str, help=argparse.SUPPRESS)
    run_options.add_argument('-lf', '--log-file', action='store', dest='LOG_FILE', default=None, type=str, help=argparse.SUPPRESS)
    
    # extract argparser arguments:
    args = argparser.parse_args()
    DATA = args.DATA             # string, OS path to data files to parse
    TEMPLATE = args.TEMPLATE     # string, Template name
    output = args.output         # string, set output format
    TIMING = args.TIMING         # boolean, enabled timing
    BASE_PATH = args.data_prefix        # string, to add to templates' inputs urls
    ONE = args.ONE               # boolean to indicate if run in single process
    MULTI = args.MULTI           # boolean to indicate if run in multi process
    LOG_LEVEL = args.LOG_LEVEL   # level of logging
    LOG_FILE = args.LOG_FILE   # level of logging
    
    def timing(message):
        if TIMING:
            print(round(time.time() - t0, 5), message)

    # setup logging
    logging_config(LOG_LEVEL, LOG_FILE)
    
    if TIMING:
        t0 = time.time()
    else:
        t0 = 0

    if TEMPLATE in vars(ttp_templates):
        TEMPLATE = vars(ttp_templates)[TEMPLATE]
        
    parser_Obj = ttp(data=DATA, template=TEMPLATE, base_path=BASE_PATH)
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
        log.error("cli: unsuported output format '{}', supported [yaml, json, raw, pprint]".format(output.lower()))

    timing("Done")
    
if __name__ == '__main__':
    cli_tool()