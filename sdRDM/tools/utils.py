import re
import yaml


class YAMLDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(YAMLDumper, self).increase_indent(flow, False)


def snake_to_camel(word: str, pascal: bool = True) -> str:

    if "_" not in word:
        # Return names that are already camel
        if pascal and word[0].isupper():
            return word
        elif not pascal and all(char.isupper() for char in word):
            return word.lower()
        else:
            return f"{word[0].lower()}{word[1::]}"

    pascal_case = "".join(x.capitalize() or "_" for x in word.split("_"))

    if pascal:
        "PASCAL"
        return pascal_case
    else:
        "CAMEL"
        return f"{pascal_case[0].lower()}{pascal_case[1::]}"


def camel_to_snake(name: str) -> str:
    name = re.sub("@", "", name)
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def check_numeric(value):
    # Checks whether the given value is of special type

    if value.lower() == "none":
        return value

    if value.lower() in ["false", "true"]:
        return value

    try:
        int(value)
        float(value)
        bool(value)
        return value
    except ValueError:
        return f'"{value}"'
