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
            print(f"DEBUG: 에러 발생! {type(e).__name__}: {e}") # 에러 타입과 내용을 출력
            import traceback
            traceback.print_exc() # 상세 위치 출력
            print("[알 수 없는 오류] 'NoneType' object has no attribute 'strip'")
    return wrapper