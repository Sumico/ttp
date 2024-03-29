_name_map_ = { 
"sprint": "print"
}

def exclude(data, pattern):
    if not pattern in data:
        return data, True
    return data, False

def equal(data, value):
    if data == value:
        return data, True
    return data, False

def notequal(data, value):
    if data != value:
        return data, True
    return data, False

def isdigit(data):
    if data.strip().isdigit():
        return data, True
    return data, False

def notdigit(data):
    if not data.strip().isdigit():
        return data, True
    return data, False

def greaterthan(data, value):
    if data.strip().isdigit() and value.strip().isdigit():
        if int(data.strip()) > int(value.strip()):
            return data, True
    return data, False

def lessthan(data, value):
    if data.strip().isdigit() and value.strip().isdigit():
        if int(data.strip()) < int(value.strip()):
            return data, True
    return data, False

def join(data, char):
    if isinstance(data, list):
        return char.join(data), None
    else:
        return data, None

def append(data, char):
    vars = _ttp_["parser_object"].vars['globals']['vars']
    char = vars.get(char, char)
    if isinstance(data, str):
        return (data + char), None
    elif isinstance(data, list):
        data.append(char)
        return data, None
    else:
        return data, None

def prepend(data, char):
    vars = _ttp_["parser_object"].vars['globals']['vars']
    char = vars.get(char, char)
    if isinstance(data, str):
        return (char + data), None
    elif isinstance(data, list):
        data.insert(0, char)
        return data, None
    else:
        return data, None

def sprint(data):
    print(data)
    return data, None
		
def contains(data, pattern):
    if pattern in data:
        return data, True
    return data, False
	
def sformat(data, string):
    """String format function
    """
    ret = string.format(data)
    return ret, None
	
def replaceall(data, *args):
    vars = _ttp_["parser_object"].vars['globals']['vars']
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

def truncate(data, truncate):
    d_split=data.split(' ')
    if len(truncate) == 1:
        t_len=int(truncate[0])
        if len(d_split) >= t_len:
            data = ' '.join(d_split[0:t_len])
    return data, None