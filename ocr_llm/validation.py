# def validate_receipt(data):
#     # mock function: ไม่เช็คอะไรเลย
#     return True
def validate_receipt(data, tolerance=0.5):
    """
    ตรวจสอบว่า sum(items.price) ≈ total
    data = {
        "date": "YYYY-MM-DD",
        "total": float,
        "items": [{"name": str, "price": float}, ...]
    }
    """
    try:
        item_sum = sum(float(item["price"]) for item in data["items"])
        if abs(item_sum - float(data["total"])) <= tolerance:
            return True, f"Total matches sum(items) ({item_sum} ≈ {data['total']})"
        else:
            return False, f"Validation failed: sum(items)={item_sum} != total={data['total']}"
    except Exception as e:
        return False, f"Validation error: {e}"
