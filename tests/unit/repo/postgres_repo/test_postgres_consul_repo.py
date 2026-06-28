from infrastructure.postgres_consultation_repo import PostgresConsultationRepository


def test_consul_repo_should_save_and_get_consul_id_success(
    pg_consul_table, new_consultation
):

    repo = PostgresConsultationRepository(pg_consul_table)

    repo.save(new_consultation)

    retrieved_consul = repo.get_by_consultation_id(new_consultation.id)

    assert retrieved_consul is not None
    assert retrieved_consul.id == new_consultation.id
