from markdown_it.token import Token


def _correct_option():
    return Token(type="inline", tag="", nesting=0, content="Option: value")


def _invalid_option():
    return Token(type="inline", tag="", nesting=0, content="invalid option")


def _type_option():
    return Token(type="inline", tag="", nesting=0, content="Type: int")


def _multiple_option():
    return Token(type="inline", tag="", nesting=0, content="Multiple: True")
