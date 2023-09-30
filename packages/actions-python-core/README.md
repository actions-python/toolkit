# `actions-python-core`

> Core functions for setting results, logging, registering secrets and exporting variables across actions

## Usage

### Import the package

```python
from actions import core
```

#### Inputs/Outputs

Action inputs can be read with `get_input` which returns a `str` or `get_boolean_input` which parses a boolean based on the [yaml 1.2 specification](https://yaml.org/spec/1.2/spec.html#id2804923). If `required` set to be false, the input should have a default value in `action.yml`.

Outputs can be set with `set_output` which makes them available to be mapped into inputs of other actions to ensure they are decoupled.

```python
my_input = core.get_input("input_name", required=True)
my_boolean_input = core.get_boolean_input("boolean_input_name", required=True)
my_multiline_input = core.get_multiline_input("multiline_input_name", required=True)

core.set_output("output_key", "output_value")
```

#### TBD
