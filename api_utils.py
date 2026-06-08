import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.http import JsonResponse


def json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON body: {exc}") from exc


def serialize_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_datetime(value):
    return value.isoformat() if value else None


def form_errors(form):
    return {field: [str(item) for item in errors] for field, errors in form.errors.items()}


def api_error(message, status=400, errors=None):
    payload = {"ok": False, "message": message}
    if errors:
        payload["errors"] = errors
    return JsonResponse(payload, status=status)


def api_ok(data=None, status=200):
    payload = {"ok": True}
    if data:
        payload.update(data)
    return JsonResponse(payload, status=status)
