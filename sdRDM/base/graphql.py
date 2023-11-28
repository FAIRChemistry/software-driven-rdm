import graphql

from sdRDM.base.listplus import ListPlus
from typing import Dict, List


def parse_query_to_selections(query: str):
    """Extracts the selections found in the GraphQL query"""
    return graphql.parse(query).to_dict()["definitions"][0]["selection_set"][
        "selections"
    ]


def traverse_graphql_query(selections, object):
    """Traverses multiple queries"""

    data = {}

    for selection in selections:
        attr = selection["name"]["value"]
        value = object.get(attr)
        arguments = extract_arguments(selection["arguments"])
        is_multiple = isinstance(value, (ListPlus, list))

        if is_data_model(value) and is_multiple:
            data[attr] = [
                traverse_graphql_query(selection["selection_set"]["selections"], entry)
                for entry in value
                if is_compliant(arguments, entry)
            ]
        elif is_data_model(value):
            if not is_compliant(arguments, value):
                continue

            data[attr] = traverse_graphql_query(
                selection["selection_set"]["selections"], value
            )
        else:
            data[attr] = object.get(attr)

    return data


def extract_arguments(arguments: List) -> Dict:
    """Turns the given data structure of the arguments into an easier one"""
    return {arg["name"]["value"]: arg["value"]["value"] for arg in arguments}


def is_compliant(arguments: Dict, object):
    """Checks whether the given is compliant to the query parameters"""
    return all(
        getattr(object, argument) == value for argument, value in arguments.items()
    )


def is_data_model(object) -> bool:
    """Checks whether the given is an sdRDM object"""

    if not isinstance(object, list):
        object = [object]

    return all(hasattr(subobject, "model_fields") for subobject in object)
