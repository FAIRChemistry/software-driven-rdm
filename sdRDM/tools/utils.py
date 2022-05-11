import re

from collections import OrderedDict


def snake_to_camel(word: str) -> str:
    return ''.join(x.capitalize() or '_' for x in word.split('_'))


def camel_to_snake(name: str) -> str:
    name = re.sub('@', '', name)
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def change_dict_keys(dictionary, fun) -> dict:

    nu_dict = {}
    for key, item in dictionary.items():

        if isinstance(item, OrderedDict):
            item = dict(item)
            value = dict(change_dict_keys(item, fun)[key])
        elif isinstance(item, list):
            try:
                value = [change_dict_keys(val, fun)[key] for val in dict(item)]
            except AttributeError:
                # TODO Find a better solution to handle the "force_list" effect
                value = item
            except KeyError:
                value = item

        else:
            value = item

        nu_dict[fun(key)] = value

    return nu_dict

    return {
        fun(key):
        change_dict_keys(item, fun) if isinstance(item, dict) else item
        for key, item in dictionary.items()
    }


def generate_documentation(fields) -> str:

    for name, parameter in parameters.items():
        names.append(name)
        types.append(parameter["type"].__name__)
        descriptions.append(parameter["description"])

    return "lol"
