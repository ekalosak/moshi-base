import datetime

import pytest

from moshibase.versioned import Versioned
from moshibase.language import similar

@pytest.fixture
def versioned():
    return Versioned()

def test_versioned_created_at(versioned):
    assert isinstance(versioned.created_at, datetime.datetime)

def test_versioned_base_version(versioned):
    assert versioned.base_version

def test_versioned_to_dict(versioned):
    expected_dict = {"created_at": versioned.created_at, "base_version": versioned.base_version}
    assert versioned.to_dict() == expected_dict

def test_versioned_to_dict_exclude(versioned):
    expected_dict = {"base_version": versioned.base_version}
    assert versioned.to_dict(exclude=["created_at"]) == expected_dict

def test_versioned_to_jsons(versioned):
    expected_jsons = '{"created_at": "%s", "base_version": "%s"}' % (versioned.created_at.isoformat(), versioned.base_version)
    assert similar(versioned.to_jsons(), expected_jsons) > 0.9

def test_versioned_to_json(versioned):
    expected_json = {"created_at": versioned.created_at.isoformat() + 'Z', "base_version": versioned.base_version}
    assert versioned.to_json() == expected_json

def test_versioned_to_json_exclude(versioned):
    expected_json = {"base_version": versioned.base_version}
    assert versioned.to_json(exclude=["created_at"]) == expected_json
