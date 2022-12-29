from typing import List, Dict, Tuple

from .tokennode import TokenNode

def split_token_list(
    token: str, model: List[Tuple], nodes: Dict[str, TokenNode]
) -> List:
    """Splits a tokenized model by the given token"""

    splitter = nodes[token]
    sub_lists = []
    temp = None

    for token, content in model:

        if token == splitter.name:
            if temp:
                sub_lists.append(temp)
                temp = [(token, content)]
            else:
                temp = [(token, content)]
        elif nodes[splitter.name].order >= nodes[token].order:
            sub_lists.append(temp)
            temp = None
        elif temp:
            temp.append((token, content))
    else:
        sub_lists.append(temp)

    return [element for element in sub_lists if element is not None]

