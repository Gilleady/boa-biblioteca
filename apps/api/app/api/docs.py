from app.schemas.error import ErrorResponse, ValidationErrorResponse

AUTH_401_RESPONSE = {
    "model": ErrorResponse,
    "description": "Authentication is required or token is invalid.",
}

INVALID_CREDENTIALS_401_RESPONSE = {
    "model": ErrorResponse,
    "description": "Invalid username or password.",
}

NOT_FOUND_404_RESPONSE = {
    "model": ErrorResponse,
    "description": "Requested resource was not found.",
}

CONFLICT_409_RESPONSE = {
    "model": ErrorResponse,
    "description": "Conflict with existing data (unique constraint or relationship rule).",
}

INVALID_PAYLOAD_400_RESPONSE = {
    "model": ErrorResponse,
    "description": "Request payload is invalid for this operation.",
}

VALIDATION_422_RESPONSE = {
    "model": ValidationErrorResponse,
    "description": "Request payload/query/params failed validation.",
}
