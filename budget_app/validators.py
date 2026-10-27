from datetime import datetime

VALID_TYPES = {"income", "expense"}


def validate_amount(amount_str: str | int) -> int:
    """금액이 양의 정수인지 검증하고 int로 반환합니다."""
    amount_str = str(amount_str).strip()

    try:
        amount = int(amount_str)
    except ValueError:
        raise ValueError("금액은 정수로 입력해야 합니다.")

    if amount <= 0:
        raise ValueError("금액은 0보다 커야 합니다.")

    return amount

def validate_date(date_str: str) -> str:
    """날짜가 YYYY-MM-DD 형식인지 검증합니다."""
    date_str = date_str.strip()

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValueError("날짜 형식은 YYYY-MM-DD 이어야 합니다.")


def validate_transaction_type(type_str: str) -> str:
    """거래 타입이 income 또는 expense인지 검증합니다."""
    type_str = type_str.strip().lower()

    if type_str not in VALID_TYPES:
        raise ValueError("거래 타입은 'income' 또는 'expense'여야 합니다.")

    return type_str

def validate_type(type_str: str) -> str:
    """
    validate_transaction_type의 별칭 함수입니다.
    서비스 코드에서 validate_type이라는 이름을 쓸 수 있게 합니다.
    """
    return validate_transaction_type(type_str)


def validate_month(month_str: str) -> str:
    """월이 YYYY-MM 형식인지 검증합니다."""
    month_str = month_str.strip()

    try:
        datetime.strptime(month_str, "%Y-%m")
        return month_str
    except ValueError:
        raise ValueError("월 형식은 YYYY-MM 이어야 합니다.")

def validate_limit(limit_str: str | int) -> int:
    """limit 값이 양의 정수인지 검증합니다."""
    limit_str = str(limit_str).strip()

    try:
        limit = int(limit_str)
    except ValueError:
        raise ValueError("limit은 정수로 입력해야 합니다.")

    if limit <= 0:
        raise ValueError("limit은 1 이상의 정수여야 합니다.")

    return limit


def validate_date_range(start_date: str | None, end_date: str | None) -> None:
    """시작일과 종료일의 형식 및 순서를 검증합니다."""
    if start_date:
        start_date = validate_date(start_date)

    if end_date:
        end_date = validate_date(end_date)

    if start_date and end_date and start_date > end_date:
        raise ValueError("시작일은 종료일보다 늦을 수 없습니다.")