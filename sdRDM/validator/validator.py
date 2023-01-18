import toml
import sdRDM.config

from typing import List, Dict, Tuple, IO
from markdown_it import MarkdownIt
from importlib import resources as pkg_resources

from sdRDM.markdown.tokenizer import tokenize_markdown_model, clean_html_markdown
from .tokennode import TokenNode, build_token_tree
from .styler import pretty_print_report
from .utils import split_token_list
from .checks import (
    check_mandatories,
    check_exclusive,
    check_forbidden,
    check_occurences,
)

MAXIMUM_LEVEL = 3
VALIDATION_FUNCTIONS = [
    check_mandatories,
    check_exclusive,
    check_forbidden,
    check_occurences,
]


def validate_markdown_model(
    handle: IO, pretty_print: bool = False
) -> Tuple[bool, List[Dict]]:
    """Validates a given markdown model, prints report and returns result as well as machine-readable report"""

    html = MarkdownIt().render(handle.read())
    model_string = clean_html_markdown(html)
    model = tokenize_markdown_model(model_string)

    rules = toml.loads(pkg_resources.read_text(sdRDM.config, "syntax_rules.toml"))
    nodes = build_token_tree(rules)

    results, reports = [], []

    for level in range(MAXIMUM_LEVEL + 1):
        result, report = validate_by_level(level, nodes, model)

        results += result
        reports += report

    if pretty_print:
        pretty_print_report(reports, model)

    return all(results), reports


def validate_by_level(
    level: int, nodes: Dict[str, TokenNode], model: List[Tuple]
) -> Tuple[List[bool], List[Dict]]:
    """Gets TokenNodes by level and applies all VALIDATION FUNCTIONS. Resturns results and report."""

    subnodes = get_nodes_by_level(level, nodes)
    results, logs = [], []

    for token_rules in subnodes:
        for part in split_token_list(token_rules.name, model, nodes):

            params = {
                "token_rules": token_rules,
                "part": part,
                "model": model,
                "nodes": nodes,
            }

            result, log = validate_part(**params)

            results += result
            logs += log

    return results, logs


def get_nodes_by_level(level: int, nodes: Dict[str, TokenNode]) -> List[TokenNode]:
    """Gets TokenNode elements by their order"""
    return list(filter(lambda node: node.order == level, nodes.values()))


def validate_part(**kwargs):
    """Applies all VALIDATE FUNCTIONS to the given part and returns result and logs"""

    results, logs = [], []

    for fun in VALIDATION_FUNCTIONS:
        result, log = fun(**kwargs)

        results += [result]
        logs += log

    return results, logs
