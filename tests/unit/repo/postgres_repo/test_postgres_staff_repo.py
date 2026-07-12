from domain.value_object import Username
from infrastructure.postgres_staff_repository import PostgresStaffRepository


def test_staff_repo_should_save_and_get_staff_success(
    pg_staffs_table, new_staff_doctor
):
    repo = PostgresStaffRepository(pg_staffs_table)
    repo.save(new_staff_doctor)

    retrieved_staff = repo.get_by_staff_id(new_staff_doctor.staff_id)

    assert retrieved_staff is not None
    assert retrieved_staff.staff_id == new_staff_doctor.staff_id


def test_staff_repo_should_get_national_id_success(pg_staffs_table, new_staff_doctor):
    repo = PostgresStaffRepository(pg_staffs_table)
    repo.save(new_staff_doctor)
    result = repo.get_by_national_id_staff(new_staff_doctor.national_id)
    assert result is not None
    assert result.national_id == new_staff_doctor.national_id


def test_staff_repo_should_return_none_when_staff_does_not_exist(
    pg_staffs_table, new_staff_doctor
):
    repo = PostgresStaffRepository(pg_staffs_table)
    result = repo.get_by_national_id_staff(new_staff_doctor.national_id)
    assert result is None


def test_staff_repo_should_return_true_when_national_id_already_exist(
    pg_staffs_table, new_staff_doctor
):
    repo = PostgresStaffRepository(pg_staffs_table)
    repo.save(new_staff_doctor)
    result = repo.is_national_id_exists(new_staff_doctor.national_id)
    assert result is True


def test_staff_repo_should_return_false_when_staff_does_not_exist(
    pg_staffs_table, new_staff_nurse
):
    repo = PostgresStaffRepository(pg_staffs_table)
    result = repo.is_national_id_exists(new_staff_nurse.national_id)

    assert result is False


def test_staff_repo_should_update_staff_success(pg_staffs_table, new_staff_doctor):
    repo = PostgresStaffRepository(pg_staffs_table)
    repo.save(new_staff_doctor)
    retrieved_staff = repo.get_by_staff_id(new_staff_doctor.staff_id)

    assert retrieved_staff is not None
    assert retrieved_staff.first_name.value == "ณัฐพงศ์"

    retrieved_staff.change_first_name("PaaTopIT")
    repo.update(retrieved_staff)
    result = repo.get_by_national_id_staff(retrieved_staff.national_id)
    assert result is not None
    assert result.staff_id == new_staff_doctor.staff_id
    assert result.version.current_number == 2
    assert result.first_name.value == "PaaTopIT"


def test_staff_repo_get_by_username_should_success(pg_staffs_table, new_staff_doctor):
    repo = PostgresStaffRepository(pg_staffs_table)
    repo.save(new_staff_doctor)
    result = repo.get_by_username(new_staff_doctor.username)
    assert result is not None
    assert result.username.id == "nattapong-top"


def test_staff_repo_get_by_username_should_return_none_when_not_exist(
    pg_staffs_table, new_staff_nurse
):
    repo = PostgresStaffRepository(pg_staffs_table)

    result = repo.get_by_username(new_staff_nurse.username)
    assert result is None


def test_staff_repo_is_username_id_exist_already_should_return_true(
    pg_staffs_table, new_staff_nurse
):
    repo = PostgresStaffRepository(pg_staffs_table)
    repo.save(new_staff_nurse)
    result = repo.is_username_exists(new_staff_nurse.username)
    assert result is True


def test_staff_repo_is_username_id_exist_does_not_exist_should_return_false(
    pg_staffs_table,
):
    repo = PostgresStaffRepository(pg_staffs_table)
    result = repo.is_username_exists(Username(id="have-username"))
    assert result is False
