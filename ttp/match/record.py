def record(data, record):
    _ttp_["parser_object"].vars['globals']['vars'].update({record: data})
    return data, None