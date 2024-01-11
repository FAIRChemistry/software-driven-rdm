<p align="center">
![](https://cdni.iconscout.com/illustration/premium/thumb/coder-3462295-2895977.png){width=400}
</p>

# Basic Model

In this example, a simple model is setup to demonstrate the capabilities of sdRDM's markdown and how it can be used to generate a Python API. To start, the markdown based sepcification builds upon these blocks:

**Objects**
: The building blocks of the model are denoted by the `###` symbol followed by the name of the object. Any of the following blocks should be nested within an object.

**Attributes**
: The attributes of an object are denoted by a list using `*` or `-` symbol followed by the name of the attribute. Mandatory attributes are written in bold using either `__name__` or `**name**`. Ultimately, these attributes define the properties of the object.

**Options**
: The options of an attribute are denoted by an indented list using the `*` or `-` symbol followed by the name of the name of the option and its value. Both are separated by a colon `:` to be valid. These options are used to specify the type of the attribute and format specific properties, but can be used to add any other metadata to the attribute.

> [!IMPORTANT]
> As you might have noticed already, this document contains textual description and images mixed with the actual definition of the model. This by design allows you to document your data model in a single document. The textual description is ignored by the parser and can be used to describe the model in more detail.

## Structural headings

You can use level 2 headings `##` to further structure your data model. Suppose you are about to define a bigger concept and want to group multiple objects together. You can use a level 2 heading to do so. The heading will be ignored by the parser and can be used to describe the concept in more detail. Platforms like GitHub will render the heading as a section that can be accessed via the table of contents - Very handy!

### MyObject

This is a description of the object `MyObject`. It can be used to describe the object in more detail. This object includes primitive, mandatory and array attributes:

**Types**
: The type option is a mandatory option that specifies the type of the attribute. You can find a list of all supported types in `sdRDM/generator/datatypes.py`. In addtion to the primitive types, you can also use other objects as types. These will then help you to build more complex data models.

**Options**
: You can include many more options to shape the output of your data model. One of which is `XML` that allows you to specifiy an alias for the serialisation.

Lets define the object `MyObject`:

- attribute
  - Type: string
  - Description: This is an attribute of type string
- **mandatory_attribute**
  - Type: float
  - Description: This is a mandatory attribute of type string
- array_attribute
  - Type: float[]
  - Description: This is an array attribute of type float
- object_attribute
  - Type: AnotherObject
  - Description: This is an object attribute of type AnotherObject
- multiple_object_attribute
  - Type: AnotherObject[]
  - Description: This is an object attribute of type AnotherObject
- some_unit
  - Type: Unit
  - Description: This is an object attribute of type Unit

### AnotherObject

Since the object `AnotherObject` is used as a type in `MyObject`, it needs to be defined as well. Here we will make use of so called `SmallTypes` which can be used on the fly to create sub-objects. Sometimes you might not want to define trivial objects in a separate block and rather define them on the fly. This is where `SmallTypes` come in handy.

- small_type
  - Type: {value: float, name: string}
  - Description: This is an attribute of type string

