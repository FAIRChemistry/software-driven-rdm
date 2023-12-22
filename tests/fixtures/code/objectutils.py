from markdown_it.token import Token


def _correct_option():
    return Token(type="inline", tag="", nesting=0, content="Option: value")


def _invalid_option():
    return Token(type="inline", tag="", nesting=0, content="invalid option")


def _type_option():
    return Token(type="inline", tag="", nesting=0, content="Type: int")


def _multiple_option():
    return Token(type="inline", tag="", nesting=0, content="Multiple: True")


def _required_token():
    return Token(type="text", tag="strong", nesting=0, content="attr_name")


def _non_required_token():
    return Token(type="text", tag="", nesting=0, content="attr_name")


def _attribute_token(name: str):
    return Token(type="text", tag="", nesting=0, content=name)


def _attribute_token_wrong_type(name: str):
    return Token(type="heading", tag="", nesting=0, content=name)


def _empty_attribute_token():
    return Token(type="text", tag="", nesting=0, content="")
