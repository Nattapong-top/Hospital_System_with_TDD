from infrastructure.postgres_staff_repository import PostgresStaffRepository


def test_staff_repo_should_save_and_get_staff_success(
    pg_staffs_table, new_staff_doctor
):
    repo = PostgresStaffRepository(pg_staffs_table)
    repo.save(new_staff_doctor)

    retrieved_staff = repo.get_by_staff_id(new_staff_doctor.staff_id)

    assert retrieved_staff is not None
    assert retrieved_staff.staff_id == new_staff_doctor.staff_id
