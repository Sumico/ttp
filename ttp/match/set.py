def set(data, value, match_line):
    vars = _ttp_["parser_object"].vars['globals']['vars']
    if data.rstrip() == match_line:
        if isinstance(value, str):
            if value in vars:
                return vars[value], None
        return value, None
    else:
        return data, False