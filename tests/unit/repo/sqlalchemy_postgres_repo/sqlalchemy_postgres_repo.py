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
