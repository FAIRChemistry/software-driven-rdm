# Test

This model tests all methods and types that are present within the sdRDM library.

## Objects

### Root

- str_value
  - Type: string
- float_value
  - Type: float
- int_value
  - Type: integer
- bool_value
  - Type: boolean
- date_value
  - Type: date
- datetime_value
  - Type: datetime
- posfloat_value
  - Type: posfloat
- posint_value
  - Type: PositiveInt
- http_url_value
  - Type: AnyHttpUrl
- email_value
  - Type: EmailStr
- bytes_value
  - Type: bytes
- multiple_primitives
  - Type: float
  - Multiple: True
- enum_value
  - Type: SomeEnum
- nested_single_obj
  - Type: Nested
- nested_multiple_obj
  - Type: Nested
  - Multiple: True
- referenced_value
  - Type: @Nested.id

### Nested

- str_value
  - Type: string
- float_value
  - Type: float
- int_value
  - Type: integer

## Enumerations

### SomeEnum

```python
VALUE1 = "value1"
VALUE2 = "value2"
```
