from pydantic.fields import ModelField
from typing import Tuple, Dict, Optional


def is_compliant_to_references(obj) -> bool:
    """Checks if individual fields that have been set are compliant to their references, if specified"""

    is_compliant, report = True, {}
    checks = get_fields_to_check(obj)

    for attribute, (root, path) in checks.items():
        value = getattr(obj, attribute)

        root_obj = traverse_to_root_node(obj, root)

        if root_obj is None:
            continue

        if value not in root_obj.get_by_meta_path(path):
            is_compliant = False
            report[
                attribute
            ] = f"""Value '{value}' for attribute '{attribute}' of object '{obj.id}' does not appear at path '{'/'.join([root, path])}' yet is required.
                """

    if not is_compliant:
        rendered_report = "\n\n".join([f"- {message}" for message in report.values()])
        raise ValueError(
            f"""Object is not compliant to the model:
            
            {rendered_report}
            """
        )

    return is_compliant


def traverse_to_root_node(obj: "DataModel", root: str) -> Optional["DataModel"]:
    """Traverses a data model until it arrives a the specified root node"""

    while True:
        if obj.__class__.__name__ == root:
            return obj
        elif obj.__parent__ is None:
            return None

        obj = obj.__parent__


def get_fields_to_check(obj: "DataModel") -> Dict:
    """Extracts all fields and their corresponding compliance check"""
    checks = {}
    for name, field in obj.__class__.__fields__.items():
        if not has_reference_check(field):
            continue

        root, path = get_field_reference_check(field)

        checks[name] = (root, path)

    return checks


def has_reference_check(field: ModelField) -> bool:
    """Checks whether a field has a reference info"""
    return "references" in field.field_info.extra


def get_field_reference_check(field: ModelField) -> Tuple[str, str]:
    """Extracts root and path from a refrence field"""
    root, *path = field.field_info.extra["references"].split(".")
    return (root, "/".join(path))
