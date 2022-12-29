import textwrap

from typing import Dict, List, Tuple, Optional
from termcolor import colored, cprint


PRINT_OBJS = ["OBJECT", "ENUM"]
WIDTH = 150


def retrieve_error_message(
    token: str, content: str, report: List[Dict]
) -> Optional[str]:
    """Retrieves an error message from a report"""

    msg = list(
        filter(
            lambda message: message["loc"] == content and message["token"] == token,
            report,
        )
    )

    if msg:
        assert "message" in msg[0], "Report message has no message lol"
        return msg[0]["message"]


def pretty_print_report(report: List[Dict], model: List[Tuple]):
    """Pretty prints an sdRDM Validation Report"""

    cprint("\nsdRDM Model Validation Report", "green")
    cprint(
        f"\nFound {len(report)} errors",
        color="green" if len(report) == 0 else "red",
    )

    prefix = "  - "
    parent = ""
    parent_printed = False

    for token, content in model:
        if token in PRINT_OBJS:
            parent_printed = False
            parent = colored(
                f"\n{content} ({token.capitalize()})\n", attrs=["underline"]
            )

        message = retrieve_error_message(token, content, report)

        if message and not parent_printed:
            parent_printed = True
            wrapper = textwrap.TextWrapper(
                initial_indent=prefix, width=WIDTH, subsequent_indent=" " * len(prefix)
            )

            print(parent)
            print(wrapper.fill(message))

        elif message and parent_printed:
            wrapper = textwrap.TextWrapper(
                initial_indent=prefix, width=WIDTH, subsequent_indent=" " * len(prefix)
            )
            print(wrapper.fill(message))
            
    print("\n")
            