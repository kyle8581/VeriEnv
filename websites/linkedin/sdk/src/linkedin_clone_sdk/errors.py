class ApiError(RuntimeError):
    def __init__(self, *, status_code: int, message: str, details: object | None = None):
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.details = details

