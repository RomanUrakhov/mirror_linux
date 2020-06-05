import functools


def state(_target_func=None, *, start_msg="Task started", end_msg="Task finished"):
    def decorator_func(target_func):
        @functools.wraps(target_func)
        def wrapper(*args, **kwargs):
            print(start_msg)
            value = target_func(*args)
            print(end_msg)
            return value

        return wrapper

    if _target_func is None:
        return decorator_func
    return decorator_func(_target_func)
