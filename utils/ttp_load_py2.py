def load_python(text_data, kwargs):
    data = {}
    # below can run on python2.7 as exec is a statements not function for python2.7:
    exec compile(text_data, '<string>', 'exec') in {"__builtins__" : None}, data
    # run eval in case if data still empty as we might have python dictionary or list
    # expressed as string
    if not data:
        data = eval(text_data, None, None)
    return data