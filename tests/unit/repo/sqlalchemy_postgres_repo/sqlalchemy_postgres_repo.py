from infrastructure.sqlalchemy_staff_repo import SqlAlchemyStaffRepository


def test_sqlalchemy_postgres_repo(new_staff_doctor, db_session):
    repo = SqlAlchemyStaffRepository(session=db_session)
    repo.save(new_staff_doctor)
    result = repo.get_by_staff_id(new_staff_doctor.staff_id)
    assert result == new_staff_doctor
