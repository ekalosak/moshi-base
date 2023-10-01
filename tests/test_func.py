import pytest
from typing import Callable

from moshibase.func import PType, Property, Parameters, Function

def test_Property_to_json():
    prop = Property(ptype=PType.STRING, description="A string property", enum=["foo", "bar"])
    expected = {'type': 'string', 'description': 'A string property', 'enum': ['foo', 'bar']}
    assert prop.to_json() == expected

def test_Property_to_json_no_description():
    with pytest.raises(ValueError):
        prop = Property(ptype=PType.NUMBER, enum=[1, 2, 3])

def test_Property_to_json_no_enum():
    prop = Property(ptype=PType.BOOLEAN, description="A boolean property")
    expected = {'type': 'boolean', 'description': 'A boolean property'}
    assert prop.to_json() == expected

def test_Property_to_json_enum_not_string():
    with pytest.raises(ValueError):
        prop = Property(ptype=PType.NUMBER, enum=[1, 2, 3])
        prop.to_json()

def test_Parameters_to_json():
    prop1 = Property(ptype=PType.STRING, description="A string property", enum=["foo", "bar"])
    prop2 = Property(ptype=PType.NUMBER, description="A number property")
    params = Parameters(properties={'prop1': prop1, 'prop2': prop2}, required=['prop1'])
    expected = {'type': 'object', 'properties': {'prop1': {'type': 'string', 'description': 'A string property', 'enum': ['foo', 'bar']}, 'prop2': {'type': 'number', 'description': 'A number property'}}, 'required': ['prop1']}
    result = params.to_json()
    assert result == expected

def test_Parameters_only_required():
    with pytest.raises(ValueError):
        Parameters(required=['prop1'])

def test_Parameters_to_json_no_properties():
    params = Parameters()
    expected = {'type': 'object', 'properties': {}}
    assert params.to_json() == expected

def test_Parameters_to_json_required_not_found():
    with pytest.raises(ValueError):
        params = Parameters(properties={'prop1': Property(ptype=PType.STRING)}, required=['prop2'])
        params.to_json()

def test_Function_to_json():
    prop1 = Property(ptype=PType.STRING, description="A string property", enum=["foo", "bar"])
    prop2 = Property(ptype=PType.NUMBER, description="A number property")
    params = Parameters(properties={'prop1': prop1, 'prop2': prop2}, required=['prop1'])
    func = Function(name='my_function', func=lambda x: x, parameters=params, description="My function description")
    expected = {'name': 'my_function', 'parameters': {'type': 'object', 'properties': {'prop1': {'type': 'string', 'description': 'A string property', 'enum': ['foo', 'bar']}, 'prop2': {'type': 'number', 'description': 'A number property'}}, 'required': ['prop1']}, 'description': 'My function description'}
    assert func.to_json() == expected 

def test_Parameters_from_callable_no_args(get_topic: Callable):
    params = Parameters.from_callable(get_topic)
    assert params.required == []
    assert params.properties == {}

def test_Parameters_from_callable(get_name: Callable):
    params = Parameters.from_callable(get_name)
    assert params.required == ['bcp47']
    assert params.properties == {
        'bcp47': Property(ptype=PType.STRING, description="The BCP-47 language code to use to pick the name."),
        'ssml_gender': Property(ptype=PType.STRING, description='The SSML gender to use to pick the name.', enum=['1', '2', '3']),
        'number': Property(ptype=PType.NUMBER, description='The number of names to return.')
    }

def test_Function_from_callable_no_args(get_topic: Callable):
    """ Examples for concrete instances of types and classes in this package. """
    func = Function.from_callable(get_topic)
    assert func.name == "get_topic"
    assert func.description == "Come up with a topic to talk about."
    assert func() in ["sports", "politics", "the weather", "media", "science"]

def test_Function_from_callable(get_name: Callable):
    """ Examples for concrete instances of types and classes in this package. """
    func = Function.from_callable(get_name)
    assert func.name == "get_name"
    assert func.description == "Get a random name."
    for name in func(bcp47="en-US", number=3):
        assert name in ["John", "Jane", "Bob", "Alice"]