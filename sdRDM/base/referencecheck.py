from typing import Tuple, Dict, Optional


def object_is_compliant_to_references(obj) -> Dict:
    """Checks if individual fields that have been set are compliant to their references, if specified"""

    report = {}
    checks = get_fields_to_check(obj)

    for attribute, (root, path) in checks.items():
        value = getattr(obj, attribute)

        root_obj = traverse_to_root_node(obj, root)

        if root_obj is None:
            # Reference is not yet part of the tree
            continue

        if value not in root_obj.get(path):
            report[
                attribute
            ] = f"""Value '{value}' for attribute '{attribute}' of object '{obj.id}' does not appear at path '{'/'.join([root, path])}' yet is required.
                """

    return report


def value_is_compliant_to_references(attribute, value, parent: "DataModel") -> Dict:
    """Checks whether an assigned value is compliant to the model"""

    checks = get_fields_to_check(parent)

    if attribute not in checks:
        return {}

    root, path = checks[attribute]

    if root == parent.__class__.__name__:
        root_obj = parent
    else:
        root_obj = traverse_to_root_node(parent, root)

    if root_obj is None:
        # Reference is not yet part of the tree
        return {}

    if value in root_obj.get_by_meta_path(path):
        return {}

    return {
        attribute: f"""Value '{value}' for attribute '{attribute}' of object '{parent.id}' does not appear at path '{'/'.join([root, path])}' yet is required.
                """
    }


def traverse_to_root_node(obj: "DataModel", root: str) -> Optional["DataModel"]:
    """Traverses a data model until it arrives a the specified root node"""

    while True:
        if obj.__class__.__name__ == root:
            return obj
        elif hasattr(obj, "_parent") and obj._parent is None:
            return None

        obj = obj._parent


def get_fields_to_check(obj: "DataModel") -> Dict:
    """Extracts all fields and their corresponding compliance check"""
    checks = {}
    for name, field in obj.__class__.model_fields.items():
        if not has_reference_check(field):
            continue

        root, path = get_field_reference_check(field)

        checks[name] = (root, path)

    return checks


def has_reference_check(field) -> bool:
    """Checks whether a field has a reference info"""

    if not hasattr(field, "json_schema_extra"):
        return False
    elif field.json_schema_extra is None:
        return False

    return "references" in field.json_schema_extra


def get_field_reference_check(field) -> Tuple[str, str]:
    """Extracts root and path from a refrence field"""

    root, *path = field.json_schema_extra["references"].split(".")
    return (root, "/".join(path))
