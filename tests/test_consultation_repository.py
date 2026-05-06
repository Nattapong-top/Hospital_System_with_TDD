from tests.conftest import new_consultation
from tests.fake_repository.fake_repository import InMemConsulRepo


def test_consultation_repository_should_save_and_get_consultation_success(new_consultation):
    # 1. Arrange: สร้าง Repository จำลอง (InMemory)
    repo = InMemConsulRepo()
    # 2. Act: บันทึกใบตรวจลงตู้
    repo.save(new_consultation)
    # 3. Assert: ลองดึงออกมาด้วย ID เดิม
    found = repo.get_by_consultation_id(new_consultation.id)

    assert found is not None
    assert found.id == new_consultation.id
    assert found.doctor.staff_id == new_consultation.doctor.staff_id

def test_consultation_repo_return_none_if_not_found():
    repo = InMemConsulRepo()
    import uuid
    assert repo.get_by_consultation_id(uuid.uuid4()) is None