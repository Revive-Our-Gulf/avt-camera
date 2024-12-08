import json

def get_parameters(path):
    with open(path) as f:
        parameters = json.load(f)
    return parameters