import functools
from models.models import Repository
from mirror.zfs import Zfs
from mirror.networking import Yum, Rsync
from queries import task, repository
from mirror import scripts


def logable(_target_func=None, *, start_msg="Task started", end_msg="Task finished"):
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


class LinuxRepoManager:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.dir_path = f"{repo.mirror_zpool}/{repo.mirror_location}"
        self.zfs = Zfs(self.dir_path, self.repo.schedule_number)
        self.yum = Yum(self.dir_path, self.repo.mirror_url)
        self.rsync = Rsync(self.dir_path, self.repo.mirror_url)

    def __repr__(self):
        return f"Manager of {self.repo.name} repository"

    @logable(start_msg="Create task started", end_msg="Create task finished")
    def create(self):
        out = self.zfs.create()
        if out[0]:
            return 1
        return 0

    @logable(start_msg="Update task started", end_msg="Update task finished")
    def update(self):
        repository.update_date_task(repo=self.repo)
        out = tuple()
        if self.repo.mirror_type == 1:
            try:
                out = self.yum.update()
            except Exception as e:
                out = 1, str(e)
        else:
            out = self.rsync.update(self.repo.mirror_args)
        if out[0]:
            return 1
        out = self.zfs.snapshot()
        if out[0]:
            return 2
        out = scripts.run_user_script_update(self.repo)
        if out[0]:
            return 3
        return 0

    @logable(start_msg="Delete task started", end_msg="Delete task finished")
    def delete(self):
        out = self.zfs.delete()
        if out[0]:
            return 2
        return 0

    @logable(start_msg="Full Create task started", end_msg="Full Create task finished")
    def full_create(self):
        if self.create():
            return 1
        if self.update():
            return 2
        repository.init_mirror(self.repo)
        return 0

    @logable(start_msg="Reset task started", end_msg="Reset task finished")
    def reset(self):
        out = scripts.run_user_script_truncate(self.repo)
        if out[0]:
            return 1
        if self.delete():
            return 2
        repository.deinit_mirror(self.repo)
        if self.full_create():
            return 3
        return 0
