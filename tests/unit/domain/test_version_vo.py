import pytest
from pydantic import ValidationError

from domain.value_object import Version


def test_should_create_version_with_previous_equal_current_first_created():
    """
    ควรสร้าง Version โดยมี previous_number เท่ากับ current_number
    เมื่อสร้างครั้งแรก
    """
    version = Version(current_number=1, previous_number=1)

    assert version.current_number == 1
    assert version.previous_number == 1


def test_should_set_previous_equal_current_when_version_initialized():

    version = Version.initial()
    assert version.previous_number == 1
    assert version.current_number == 1


def test_should_increment_current_num_when_version_increments_and_previous_as_before():
    version = Version.initial()
    version = version.increment()
    version = version.increment()
    assert version.current_number == 3
    assert version.previous_number == 1


def test_should_raise_error_when_current_number_is_zero():
    with pytest.raises(ValidationError) as e:
        Version(current_number=0, previous_number=0)
    assert "Input should be greater than or equal to 1" in str(e.value)


def test_should_raise_error_when_previous_number_is_zero():
    with pytest.raises(ValidationError) as e:
        Version(current_number=1, previous_number=0)
    assert "Input should be greater than or equal to 1" in str(e.value)

    try:
        Version(current_number=0, previous_number=0)
    except Exception as e:
        print(type(e))
