from functools import wraps


def handle_cli_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"[입력 오류] {e}")
            return 1
        except FileNotFoundError as e:
            print(f"[파일 오류] {e}")
            return 1
        except Exception as e:
            print(f"[알 수 없는 오류] {e}")
            return 1
    return wrapper