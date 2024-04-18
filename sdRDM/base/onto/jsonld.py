from typing import get_args, get_origin

from pydantic.fields import FieldInfo


def process_term(
    obj,
    attr: str,
):
    """Processes the term of a field."""

    from sdRDM.base.datatypes.identifier import Identifier

    field_info = obj.model_fields[attr]
    is_multiple = get_origin(field_info.annotation) == list
    is_identifier = any(dtype == Identifier for dtype in get_args(field_info.annotation))

    term = _get_object_uri(obj, attr)
    wrap = _get_term_wrap(is_multiple, is_identifier)

    if wrap and term:
        return {"@id": term, **wrap}
    else:
        return term


def _get_term_wrap(
    is_multiple: bool,
    is_identifier: bool,
):
    if is_multiple:
        return {"@container": "@list"}
    elif is_identifier:
        return {"@type": "@id"}

def _get_object_uri(obj, field: str):
    """Extracts the URI of a complex type."""

    field_info = obj.model_fields[field]
    extra = field_info.json_schema_extra

    if extra is not None and "term" in extra: # type: ignore
        return extra["term"] # type: ignore
    else:
        return None

    # elif _is_complex_type(obj, field):
    #     return _extract_repo_term_from_complex(obj, field_info)
    # else:
    #     return _extract_repo_term_simple(obj, field, obj._repo) # type: ignore

def _extract_repo_term_simple(
    obj,
    field_name: str,
    url: str,
):
    """Creates the object URI based on the repository URL."""

    return f"{url}/{field_name}"


def _extract_repo_term_from_complex(obj, field_info: FieldInfo):
    """Constructs a custom ontology term based on the GitHub repository."""

    dtype = field_info.annotation
    origin = get_origin(dtype)
    is_optional = any(subtype == type(None) for subtype in get_args(dtype))

    if dtype is None:
        raise ValueError(f"Field {field_info.title} has no annotation.")

    if get_origin(dtype) == list:
        cls_name = get_args(dtype)[0].__name__
    elif is_optional:
        subtypes = [
            subtype
            for subtype in get_args(dtype)
            if hasattr(subtype, "model_fields")
        ]

        cls_name = subtypes[0].__name__
    else:
        cls_name = dtype.__name__

    return f"{obj._repo}/{cls_name}"

def _is_complex_type(obj, field: str):
    """Determines if a field is a complex type or not."""

    dtype = obj.model_fields[field].annotation
    origin = get_origin(dtype)
    is_optional = any(subtype == type(None) for subtype in get_args(dtype))

    if origin == list:
        dtype = get_args(dtype)[0]
        return hasattr(dtype, "model_fields")
    elif is_optional:
        return any(hasattr(subtype, "model_fields") for subtype in get_args(dtype))
    else:
        return hasattr(dtype, "model_fields")
