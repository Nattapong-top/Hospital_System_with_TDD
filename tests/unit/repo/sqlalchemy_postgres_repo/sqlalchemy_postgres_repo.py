import pytest

from domain.custom_error import ConcurrentUpdateError
from infrastructure.sqlalchemy_staff_repo import SqlAlchemyStaffRepository


def test_sqlalchemy_postgres_repo(new_staff_doctor, db_session):
    repo = SqlAlchemyStaffRepository(session=db_session)
    repo.save(new_staff_doctor)
    result = repo.get_by_staff_id(new_staff_doctor.staff_id)
    assert result == new_staff_doctor


def test_sqlalchemy_staff_repo_get_username_shout_return_staff_success(
    new_staff_doctor, db_session
):
    repo = SqlAlchemyStaffRepository(session=db_session)
    repo.save(new_staff_doctor)
    result = repo.get_by_username(new_staff_doctor.username)
    assert result.username == new_staff_doctor.username


def test_sqlalchemy_staff_repo_get_username_shout_return_none_when_dont_username(
    db_session, new_staff_nurse
):
    repo = SqlAlchemyStaffRepository(session=db_session)
    result = repo.get_by_username(new_staff_nurse.username)
    assert result is None


def test_sqlalchemy_staff_repo_is_username_exists(new_staff_doctor, db_session):
    repo = SqlAlchemyStaffRepository(session=db_session)
    repo.save(new_staff_doctor)
    result = repo.is_username_exists(new_staff_doctor.username)
    assert result is True


def test_sqlalchemy_staff_repo_is_username_not_exists(new_staff_nurse, db_session):
    repo = SqlAlchemyStaffRepository(session=db_session)
    result = repo.is_username_exists(new_staff_nurse.username)
    assert result is False


def test_sqlalchemy_staff_repo_update_staff_success(new_staff_doctor, db_session):
    repo = SqlAlchemyStaffRepository(session=db_session)
    repo.save(new_staff_doctor)

    updated_staff_doctor = repo.get_by_staff_id(new_staff_doctor.staff_id)
    assert updated_staff_doctor is not None
    assert updated_staff_doctor.version.current_number == 1
    assert updated_staff_doctor.version.previous_number == 1

    updated_staff_doctor.suspend()
    assert updated_staff_doctor.version.current_number == 2
    assert updated_staff_doctor.version.previous_number == 1

    repo.update(updated_staff_doctor)
    result = repo.get_by_staff_id(new_staff_doctor.staff_id)

    assert result.staff_id == new_staff_doctor.staff_id == updated_staff_doctor.staff_id
    assert result.is_active is False
    assert result.version.current_number == 2
    assert result.version.previous_number == 2


def test_sqlalchemy_staff_repo_update_staff_optimistic_concurrency(
    new_staff_doctor, db_session
):
    repo = SqlAlchemyStaffRepository(session=db_session)
    repo.save(new_staff_doctor)
    a_staff = repo.get_by_staff_id(new_staff_doctor.staff_id)
    b_staff = repo.get_by_staff_id(new_staff_doctor.staff_id)

    a_staff.change_first_name(first_name_str="ณัฐนัน")
    repo.update(a_staff)
    result = repo.get_by_staff_id(new_staff_doctor.staff_id)
    assert result.version.current_number == 2
    assert b_staff.version.current_number == 1
    b_staff.change_first_name(first_name_str="นันฐณัฐ")
    with pytest.raises(ConcurrentUpdateError) as e:
        repo.update(b_staff)

    assert "มีคนอื่นแก้ไขข้อมูลนี้ไปแล้วก่อนหน้านี้" in str(e.value)
