from re import finditer

def gethostname(data, data_name, *args, **kwargs):
    """Description: Method to find hostname in show
    command output, uses symbols '# ', '<', '>' to find hostname
    """
    REs = [ # ios-xr prompt re must go before ios privilege prompt re
        {'juniper': '\n\S*@(\S+)>.*(?=\n)'},       # e.g. 'some.user@router-fw-host>'
        {'huawei': '\n\S*<(\S+)>.*(?=\n)'},        # e.g. '<hostname>'
        {'ios_exec': '\n(\S+)>.*(?=\n)'},          # e.g. 'hostname>'
        {'ios_xr': '\n\S+:(\S+)#.*(?=\n)'},        # e.g. 'RP/0/4/CPU0:hostname#'
        {'ios_priv': '\n(\S+)#.*(?=\n)'},          # e.g. 'hostname#'
        {'fortigate': '\n(\S+ \(\S+\)) #.*(?=\n)'} # e.g. 'forti-hostname (Default) #'
    ]
    for item in REs:
        name, regex = list(item.items())[0]
        match_iter = finditer(regex, data)
        try:
            match = next(match_iter)
            return match.group(1)
        except StopIteration:
            continue
    log.error('ttp.functions.variable_gethostname: "{}" file, Hostname not found'.format(data_name))
    return False