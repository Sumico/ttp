def load_python(text_data, kwargs):
    data = {}
    exec(compile(text_data, '<string>', 'exec'), {"__builtins__" : None}, data)
    # run eval in case if data still empty as we might have python dictionary or list
    # expressed as string
    if not data:
        data = eval(text_data, None, None)
    return data