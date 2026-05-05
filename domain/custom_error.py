class DomainError(Exception):
    pass


class DuplicationQueueError(DomainError):
    pass


class InvalidStatusTransitionError(DomainError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class DoNotChangeIDError(DomainError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class MissingDiagnosisError(DomainError):
    def __init__(self, message='กรุณากรอกข้อมูลการวินิจฉัยด้วยครับ'):
        self.message = message
        super().__init__(self.message)


class InvalidCancelRequestError(DomainError):
    pass


class RegistryNotConfiguredError(DomainError):
    pass


class DuplicateNationalIDError(DomainError):
    pass


class VitalSignsMissingError(DomainError):
    """ด่าเวลาพยายามออกคิวโดยไม่มีสัญญาณชีพ"""

    def __init__(self, message="ป๋าครับ! ไม่มีสัญญาณชีพ ออกคิวให้ไม่ได้นะ!"):
        self.message = message
        super().__init__(self.message)

class QueueNotFoundError(DomainError):
    def __init__(self, queue_id=None):
        if queue_id:
            self.message = f'ไม่พบคิว ID: {queue_id} นี้ในระบบครับ'
        else:
            self.message = 'ไม่พบคิวที่ระบุครับ'
        super().__init__(self.message)

class DuplicateUsernameError(DomainError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class PermissionDeniedError(DomainError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)