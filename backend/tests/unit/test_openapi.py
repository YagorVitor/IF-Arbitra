from app.main import app


def test_every_json_api_operation_declares_a_success_schema():
    schema = app.openapi()
    missing = []
    for path, operations in schema["paths"].items():
        if not path.startswith("/api/"):
            continue
        for method, operation in operations.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            success = next(
                (
                    response
                    for status, response in operation["responses"].items()
                    if status.startswith("2")
                ),
                None,
            )
            if success is None:
                missing.append(f"{method.upper()} {path}: missing success response")
                continue
            if success.get("content") and not any(
                media.get("schema") for media in success["content"].values()
            ):
                missing.append(f"{method.upper()} {path}: missing response schema")
    assert missing == []


def test_sensitive_orm_fields_are_absent_from_public_schemas():
    serialized = str(app.openapi())
    for field in ["password_hash", "token_hash", "LoginSession", "LoginThrottle"]:
        assert field not in serialized
