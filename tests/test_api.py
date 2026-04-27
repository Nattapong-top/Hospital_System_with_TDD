# Hospital_System/tests/test_api.py
from datetime import date
from uuid import uuid4


def test_api_register_new_patient_should_return_success(client, valid_patient_payload):
    # 1. จำลองข้อมูล JSON ที่หน้าเว็บจะส่งมาให้ (เหมือนกรอกฟอร์ม)
    # 2. ยิง API แบบ POST ไปที่ประตูรับลงทะเบียน
    response = client.post('/api/patients/register', json=valid_patient_payload)

    # 3. ตรวจข้อสอบ
    assert response.status_code == 200  # ต้องตอบกลับว่าสำเร็จ (200 OK)
    data = response.json()
    assert data['national_id'] == valid_patient_payload['national_id']
    assert data['first_name'] == valid_patient_payload['first_name']



def test_api_registrar_patient_duplicate_should_return_same_id(client, valid_patient_payload):
    # ยิงครั้งแรก (สร้างใหม่)
    res1 = client.post('/api/patients/register', json=valid_patient_payload)
    id1 = res1.json()['national_id']

    # ยิงครั้งที่ 2 (ข้อมูลเดิม)
    res2 = client.post('/api/patients/register', json=valid_patient_payload)
    id2 = res2.json()['national_id']

    # ตรวจสอบ: ต้อง 200 OK และ ID ตรงกัน
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert id1 == id2
    assert res2.json()['message'] == 'ลงทะเบียนสำเร็จ!'

def test_api_registrar_patient_should_fail_when_invalid_nation_id(client, valid_patient_payload):
    bad_payload = valid_patient_payload.copy()
    bad_payload['national_id'] = 'XYZ-888888888'

    response = client.post('/api/patients/register', json=bad_payload)

    assert response.status_code == 400
    assert 'String should match pattern' in response.json()['detail']

def test_api_new_queue_should_return_success_when_have_patient_id_and_vital_sign(client, valid_patient_payload):
    """
        Test the full integration flow:
        1. Register a new patient.
        2. Record vital signs and issue a queue.
    """

    # ลงทะเบียนผู้ป่วย
    reg_res = client.post('/api/patients/register', json=valid_patient_payload)
    new_patient_id = reg_res.json()['id']

    triage_payload = {
        "patient_id": new_patient_id,
        "vitals": {
            "systolic": 120, "diastolic": 80,
            "weight": 70.5, "height": 175.0,
            "temperature": 36.5,
            "symptom": "ปวดหัว ตัวร้อน"
        }
    }
    # ออกคิว ส่ง ข้อมูลสัญญาชีพและซักประวัติ
    response = client.post('/api/triage', json=triage_payload)

    # ... ก่อน assert status_code ...
    if response.status_code == 422:
        print(f"\n❌ ป๋าครับ Pydantic ด่าว่า: {response.json()['detail']}")

    # ตรวจคำตอบ
    assert response.status_code == 200
    assert 'queue_number' in response.json()
    print(response.json()['queue_id'])
    assert response.json()['queue_number'] == '1'
    assert response.json()['status'] == 'รอ'
    assert response.json()['queue_date'] == date.today().isoformat()

def test_api_triage_should_fail_when_no_vital_sign(client, valid_patient_payload):
    patient = client.post('/api/patients/register', json=valid_patient_payload)

    data = patient.json()
    print(data)
    payload = {
        "patient_id": data['id'],
        'vitals': None
    }

    response = client.post('/api/triage', json=payload)
    assert response.status_code == 400
    assert 'ลืมส่งสัญญาณชีพมานะ ออกคิวไม่ได้ครับ' in response.json()['detail']

def test_api_get_all_queues_today_should_return_list_all_queues_today(api_new_queues, client):
    q = api_new_queues
    assert q.status_code == 200
    response = client.get('/api/nurse/queues/today')

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]['queue_number'] == '1'
    assert data[0]['queue_id'] == q.json()['queue_id']

def test_api_queue_start_consultation_successfully(client, api_new_queues):
    queue_id = api_new_queues.json()['queue_id']

    response = client.post(f'/api/consultations/{queue_id}/start')

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'กำลังพบหมอ'
    assert data['queue_id'] == queue_id


def test_api_queue_start_consultation_duplicate_queue_should_fail(client, api_new_queues):
    queue_id = api_new_queues.json()['queue_id']
    first_call = client.post(f'/api/consultations/{queue_id}/start')
    assert first_call.status_code == 200

    duplicate_call = client.post(f'/api/consultations/{queue_id}/start')
    assert duplicate_call.status_code == 400
    assert 'ไม่สามารถเริ่มตรวจได้' in duplicate_call.json()['detail']


def test_api_queue_start_consultation_not_found_queue_should_return_404(client):
    fake_id = uuid4()
    response = client.post(f'/api/consultations/{fake_id}/start')

    assert response.status_code == 404
    assert 'ไม่พบคิว' in response.json()['detail']

def test_api_queue_complete_visit_successfully(client, api_new_queues, diagnosis_payload):
    queue_id = api_new_queues.json()['queue_id']
    q_start = client.post(f'/api/consultations/{queue_id}/start')

    assert q_start.status_code == 200
    q_complete = client.post(f'/api/consultations/{queue_id}/complete', json=diagnosis_payload)

    assert q_complete.status_code == 200
    data = q_complete.json()
    assert isinstance(data, dict)
    assert data['queue_id'] == queue_id
    assert data['status'] == 'ตรวจเสร็จแล้ว'
    assert data['message'] == 'บันทึกผลการตรวจเรียบร้อย'

def test_api_queue_complete_visit_whit_none_diagnosis_should_raise_missing_diagnosis_error_return_400(client, api_new_queues, diagnosis_payload):
    queue_id = api_new_queues.json()['queue_id']
    client.post(f'/api/consultations/{queue_id}/start')
    q_complete = client.post(f'/api/consultations/{queue_id}/complete', json={})
    assert q_complete.status_code == 400
    data = q_complete.json()
    assert 'กรุณากรอกข้อมูลการวินิจฉัยด้วยครับ' in data['detail']

def test_api_queue_cancel_visit_whit_status_waiting_should_successfully(client, api_new_queues, diagnosis_payload):
    queue_id = api_new_queues.json()['queue_id']
    q_cancel = client.post(f'/api/consultations/{queue_id}/cancel')
    assert q_cancel.status_code == 200
    data = q_cancel.json()
    assert isinstance(data, dict)
    assert data['queue_id'] == queue_id
    assert data['status'] == 'ยกเลิก'

def test_api_queue_cancel_visit_whit_status_in_progress_should_successfully(client, api_new_queues):
    queue_id = api_new_queues.json()['queue_id']
    q_start = client.post(f'/api/consultations/{queue_id}/start')
    assert q_start.json()['status'] == 'กำลังพบหมอ'

    q_cancel = client.post(f'/api/consultations/{queue_id}/cancel')
    assert q_cancel.status_code == 200
    data = q_cancel.json()
    assert isinstance(data, dict)
    assert data['queue_id'] == queue_id
    assert data['status'] == 'ยกเลิก'

def test_api_queue_cancel_visit_with_status_complete_should_return_400(client, api_new_queues, diagnosis_payload):
    queue_id = api_new_queues.json()['queue_id']
    q_start = client.post(f'/api/consultations/{queue_id}/start')
    assert q_start.json()['status'] == 'กำลังพบหมอ'

    q_complete = client.post(f'/api/consultations/{queue_id}/complete', json=diagnosis_payload)
    assert q_complete.status_code == 200

    q_cancel = client.post(f'/api/consultations/{queue_id}/cancel')
    assert q_cancel.status_code == 400
    assert 'ไม่สามารถยกเลิกการตรวจได้' in q_cancel.json()['detail']
