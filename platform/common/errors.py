# platform/common/errors.py
from typing import Dict, Any, Optional
from fastapi import HTTPException

class SophiaError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }

def ok(data: Any = None) -> Dict[str, Any]:
    return {"status": "ok", "data": data}

def err(message: str, code: str = "ERROR", status_code: int = 400, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }

def raise_http_error(message: str, status_code: int = 400, code: str = "HTTP_ERROR") -> None:
    raise HTTPException(status_code=status_code, detail=err(message, code, status_code))