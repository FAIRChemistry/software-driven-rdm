# Module

Some description

## Objects

Other description

### Object

- attribute
  - Type: int
  - Description: Primitive attribute
- multiple_primitive_attribute
  - Type: int[]
  - Description: Multiple primitive attribute
- nested
  - Type: Nested
  - Description: Nested attribute
- inherited_nested
  - Type: InheritedNested
  - Description: Inherited nested attribute

### Nested

- attribute
  - Type: int
  - Description: Primitive attribute

### InheritedNested [*Nested*]

- added_attr
  - Type: int
  - Description: Primitive attribute

## Enumerations

### SomeEnum

```python
VALUE = "value"
```
