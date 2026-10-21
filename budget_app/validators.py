from datetime import datetime

def validate_amount(amount_str: str) -> int:
    """금액이 양의 정수인지 검증하고 int로 반환합니다."""

    if not amount_str.isdigit():
        raise ValueError("금액은 0보다 큰 숫자여야 합니다.")
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError("금액은 0보다 커야 합니다.")
        return amount

def validate_date(date_str: str) -> str:
    """날짜가 YYYY-MM-DD 형식인지 검증합니다."""
    try:
        datetime.strftime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValueError("날짜 형식은 YYYY-MM-DD 이어야 합니다.")

def validate_transaction_type(type_str: str) -> str:
    """거래 타입이 income 또는 expense인지 검증합니다."""
    if type_str not in ["income", "expense"]:
        raise ValueError("거래 타입은 'income' 또는 'expense'여야 합니다.")
        return type_str
    