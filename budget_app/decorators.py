from functools import wraps

def print_call(func):
    @wraps(func)
    def wrapper(*aegs, **kwargs):
        print(f"{func.__name__} 함수가 실행됩니다.")
        return func(*args, **kwargs)
    return wrapper
