import functools
from queries import task


def state(_target_func=None, *, start_msg="Task started", end_msg="Task finished"):
    def decorator_func(target_func):
        @functools.wraps(target_func)
        def wrapper(*args, **kwargs):
            task.write_task_status(args[0].repo, msg=start_msg)
            value = target_func(*args)
            task.write_task_status(args[0].repo, msg=end_msg)
            return value

        return wrapper

    if _target_func is None:
        return decorator_func
    return decorator_func(_target_func)
