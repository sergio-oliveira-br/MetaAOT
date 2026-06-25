# webapp/services/infra/dynamodb_serializer.py

from decimal import Decimal

def convert_floats(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))

    if isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [convert_floats(i) for i in obj]

    return obj