def test_api_examination_should_start_consultation_and_update_state_in_progress(
    client, api_new_queues, api_staff_doctor, api_vitals
):
    staff_id = api_staff_doctor.json()["staff_id"]
    queue_data = api_new_queues.json()

    exam_payload = {
        "queue_id": queue_data["queue_id"],
        "staff_id": staff_id,
        "patient_id": queue_data["patient_id"],
        "vital_signs": api_vitals,
    }

    new_exam = client.post("/api/examination/start", json=exam_payload)
    assert new_exam.status_code == 200
    exam_data = new_exam.json()
    print(exam_data)
    assert exam_data["queue_id"] == queue_data["queue_id"]
    assert exam_data["patient_id"] == queue_data["patient_id"]
    assert exam_data["doctor_id"] == staff_id
    assert exam_data["status"] == "กำลังพบหมอ"
    assert exam_data["consultation_id"] is not None


# def test_api_examination_when_not_found_staff_id_should_raise_error(client, api_new_queues, api_vitals):
#
#     staff_id = str(uuid.uuid4())
#     queue_data = api_new_queues.json()
#
#     not_found_staff_id = {
#         'queue_id': queue_data['queue_id'],
#         'staff_id': staff_id,
#         'patient_id': queue_data["patient_id"],
#         'vital_signs': api_vitals
#     }
#
#     not_found = client.post("/api/examination/start", json=not_found_staff_id)
#
#     assert not_found.status_code == 400
#     assert 'ไม่พบรหัสพนักงาน' == not_found.json()['detail']
