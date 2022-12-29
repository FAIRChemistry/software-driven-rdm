import importlib

from typing import List, Dict, Tuple
from termcolor import colored

from .tokennode import TokenNode, AVAILABLE_TOKENS
from .utils import split_token_list


def check_mandatories(
    token_rules: TokenNode, part: List[Tuple], **kwargs
) -> Tuple[bool, List[Dict]]:
    """Checks mandatories of a token and returns a log"""

    if token_rules.mandatory is None:
        return True, []

    log, results = [], []

    for mandatory in token_rules.mandatory:

        assert isinstance(mandatory, str), f"Rule {mandatory} is not a string"

        if "!" in mandatory:
            mandatory = mandatory.replace("!", "")
            unique = True
        else:
            unique = False

        result, msg = has_mandatory(part, mandatory, unique)
        if msg:
            log += [msg]
        results += [result]

    return all(results), list(filter(lambda x: len(x) > 0, log))


def has_mandatory(
    part: List[Tuple], rule: str, unique: bool = False
) -> Tuple[bool, Dict]:
    """Checks whether a mandatory token is given"""

    token, name = part[0]
    check = [tok == rule for tok, _ in part]

    if check.count(True) == 0:
        return False, {
            "loc": name,
            "token": token,
            "message": f"{token.capitalize()} {colored(name, 'yellow')} is missing mandatory sub-field of type {colored(rule.capitalize(), 'cyan')}",
        }

    elif unique is True and check.count(True) > 1:
        return False, {
            "loc": name,
            "token": token,
            "message": f"{token.capitalize()} {colored(name, 'yellow')} contains mandatory sub-field of type '{colored(rule.capitalize(), 'cyan')}' more than once, but should only occur once.",
        }

    else:
        return True, {}


def check_exclusive(
    token_rules: TokenNode,
    part: List[Tuple],
    model: List[Tuple],
    nodes: Dict[str, TokenNode],
    **kwargs,
) -> Tuple[bool, List[Dict]]:
    """Checks whether the given element is exclusive within the model, given the token"""

    if token_rules.exclusive is False:
        return True, []

    token, content = part[0]

    assert token_rules.parent, "Parent is not existing"

    duplicates = find_duplicates(
        split_token_list(token_rules.parent.name, model, nodes),
        token=token,
        content=content,
    )

    if duplicates:

        assert token_rules.parent, "Parent is not existing"

        return False, [
            {
                "loc": content,
                "token": token,
                "message": f"{token_rules.name.capitalize()} {colored(content, 'yellow')} exists more than once in {token_rules.parent.name.lower()}/s {colored(str(duplicates), 'cyan')}",
            }
        ]
    else:
        return True, []


def find_duplicates(submodels: List[List[Tuple]], token: str, content: str):
    """Finds all duplicate instances within an object of order -1"""

    duplicates = []

    for submodel in submodels:
        count = sum([1 for tok, cont in submodel if content == cont and token == tok])
        if count > 1:
            return submodel[0][-1]

    return [duplicate for duplicate in duplicates if duplicate]


def check_forbidden(
    token_rules: TokenNode, part: List[Tuple], **kwargs
) -> Tuple[bool, List[Dict]]:
    """Checks whether the content of given token is forbidden"""

    if token_rules.forbidden is None:
        return True, []

    token, content = part[0]

    if content in token_rules.forbidden:
        return False, [
            {
                "loc": content,
                "token": token,
                "message": f"{token_rules.name.capitalize()} name {colored(content, 'yellow')} is forbidden - Value/s {colored(str(token_rules.forbidden), 'cyan')} are not allowed.",
            }
        ]
    else:
        return True, []


def check_occurences(
    token_rules: TokenNode, part: List[Tuple], model: List[Tuple], **kwargs
) -> Tuple[bool, List[Dict]]:
    """Checks if content is consistent across the model and libary"""

    if token_rules.occurs_in is None:
        return True, []

    token, content = part[0]
    failed = []
    check = None

    for destination in token_rules.occurs_in:

        assert isinstance(destination, str)

        if destination in AVAILABLE_TOKENS:
            check = is_part_of_model(destination, content, model)
        elif "@" in destination:
            address, enum = destination.split("@")
            enum = import_enum(address, enum)
            check = hasattr(enum, content)
            destination = enum.__name__

        if check is True:
            return True, []
        else:
            failed.append(destination.capitalize())

    return False, [
        {
            "loc": content,
            "token": token,
            "message": f"{token.capitalize()} {colored(content, 'yellow')} does not occur in any of the required location/s {colored(str(failed), 'cyan')}",
        }
    ]


def is_part_of_model(token: str, content: str, model: List[Tuple]) -> bool:
    """Checks whether if given content is occuring elsewhere in the model"""

    return any(content == cont for tok, cont in model if token == tok)


def import_enum(address: str, enum: str):
    """Imports from a given address"""
    module = importlib.import_module(address)

    assert hasattr(module, enum), f"Enum not found in {address}"

    return getattr(module, enum)
