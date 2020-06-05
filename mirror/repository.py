import subprocess

import config
from mirror.networking import Yum, Rsync
from mirror.zfs import Zfs
from models.models import Repository
from utils import loger


class LinuxRepoManager:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.dir_path = f"{repo.mirror_zpool}/{repo.mirror_location}"
        self.zfs = Zfs(self.dir_path)

    def __repr__(self):
        return f"Manager of {self.repo.name} repository"

    def __user_script_update(self, snap):
        if not config.on_update or config.on_update == "":
            return ""
        location = f"/{self.repo.mirror_zpool}/{self.repo.mirror_location}"
        return subprocess.run(
            [config.on_update, self.repo.mirror_zpool, self.repo.mirror_location, location, snap],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        ).stdout

    def __user_script_truncate(self):
        if not config.on_truncate or config.on_truncate == "":
            return ""
        return subprocess.run(
            [config.on_truncate, self.repo.mirror_zpool, self.repo.mirror_location],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        ).stdout

    def filesystem_exist(self):
        return self.zfs.filesystem_exist()

    @loger.state(start_msg="Create task started", end_msg="Create task finished")
    def create(self):
        print("Zfs create")
        print(self.zfs.create())

    @loger.state(start_msg="Update task started", end_msg="Update task finished")
    def update(self):
        if self.repo.mirror_type == 1:
            print("Yum update")
            yum = Yum(self.dir_path, self.repo.mirror_url)
            print(yum.update())
        else:
            print("Rsync update")
            rsync = Rsync(self.dir_path, self.repo.mirror_url)
            print(rsync.update(self.repo.mirror_args))

        print("Create snapshot")
        print(self.zfs.snapshot())

        snap_list = self.zfs.snapshot_list()
        if len(snap_list) > self.repo.schedule_number:
            print(f"Delete snapshot {snap_list[-1]}")
            print(self.zfs.destroy_snap(snap_list[-1]))

        print("User script on delete")
        print(self.__user_script_update(snap_list[0]))

    @loger.state(start_msg="Delete task started", end_msg="Delete task finished")
    def delete(self):
        print("User script on truncate")
        print(self.__user_script_truncate())
        print("Zfs delete")
        print(self.zfs.delete())
