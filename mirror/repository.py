from models.models import Repository
from mirror.zfs import Zfs
from mirror.networking import Yum, Rsync
from queries import task, repository
from utils import loger
import config
import subprocess


class LinuxRepoManager:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.dir_path = f"{repo.mirror_zpool}/{repo.mirror_location}"
        self.zfs = Zfs(self.dir_path)

    def __repr__(self):
        return f"Manager of {self.repo.name} repository"

    def __user_script_update(self):
        if not config.on_update or config.on_update == "":
            return 0, "ok"
        location = f"/{self.repo.mirror_zpool}/{self.repo.mirror_location}"
        try:
            return 0, subprocess.check_output([config.on_update, str(self.repo.get_id()), location])
        except subprocess.CalledProcessError as e:
            return 1, e.output

    def __user_script_truncate(self):
        if not config.on_truncate or config.on_truncate == "":
            return 0, "ok"
        try:
            return 0, subprocess.check_output([config.on_truncate, str(self.repo.get_id())])
        except subprocess.CalledProcessError as e:
            return 1, e.output

    @loger.state(start_msg="Create task started", end_msg="Create task finished")
    def create(self):
        out = self.zfs.create()
        task.write_task_status(self.repo, out)
        if out[0]:
            return 1
        return 0

    @loger.state(start_msg="Update task started", end_msg="Update task finished")
    def update(self):
        repository.update_date_task(repo=self.repo)
        out = tuple()
        if self.repo.mirror_type == 1:
            try:
                yum = Yum(self.dir_path, self.repo.mirror_url)
                out = yum.update()
            except Exception as e:
                out = 1, str(e)
        else:
            rsync = Rsync(self.dir_path, self.repo.mirror_url)
            out = rsync.update(self.repo.mirror_args)
        task.write_task_status(self.repo, out)
        if out[0]:
            return 1

        out = self.zfs.snapshot()
        task.write_task_status(self.repo, out)
        if out[0]:
            return 2

        out = self.zfs.snapshot_list()
        task.write_task_status(self.repo, out)
        if out[0]:
            return 3
        snap_list = out[1]

        if len(snap_list) > self.repo.schedule_number:
            out = self.zfs.destroy_snap(snap_list[-1])
            task.write_task_status(self.repo, out)
            if out[0]:
                return 4

        out = self.__user_script_update()
        task.write_task_status(self.repo, out)
        if out[0]:
            return 5
        return 0

    @loger.state(start_msg="Delete task started", end_msg="Delete task finished")
    def delete(self):
        out = self.zfs.delete()
        task.write_task_status(self.repo, out)
        if out[0]:
            return 2
        return 0

    @loger.state(start_msg="Full Create task started", end_msg="Full Create task finished")
    def full_create(self):
        if self.create():
            return 1
        if self.update():
            return 2
        repository.init_mirror(self.repo)
        return 0

    @loger.state(start_msg="Reset task started", end_msg="Reset task finished")
    def reset(self):
        out = self.__user_script_truncate()
        task.write_task_status(self.repo, out)
        if out[0]:
            return 1
        if self.delete():
            return 2
        repository.deinit_mirror(self.repo)
        if self.full_create():
            return 3
        return 0
