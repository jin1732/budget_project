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
        except EOFError:
            print("[입력 오류] 입력이 중단되었습니다. 다시 시도해주세요.")
            return 1
        except KeyboardInterrupt:
            print("\n[입력 오류] 사용자 입력을 취소했습니다.")
            return 1
        except Exception as e:
            print(f"[시스템 오류] {type(e).__name__}: {e}")
            return 1

    return wrapper