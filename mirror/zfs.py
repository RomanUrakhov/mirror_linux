import datetime
import subprocess


class Zfs:
    def __init__(self, dir_path):
        self.dir_path = dir_path

    def create(self):
        return subprocess.run(["zfs", "create", self.dir_path], check=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT).stdout

    def delete(self):
        return subprocess.run(["zfs", "destroy", "-r", self.dir_path], check=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT).stdout

    def snapshot(self):
        snap_name = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        return subprocess.run(
            ["zfs", "snapshot", f"{self.dir_path}@{snap_name}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        ).stdout

    def snapshot_list(self):
        out = subprocess.run(
            f"zfs list -H -r -t snapshot -o name -S creation {self.dir_path}",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        ).stdout
        snap_list = [snap for snap in out.decode("utf-8").split('\n')][:-1]
        return snap_list

    def filesystem_exist(self):
        out = subprocess.run(
            f"zfs list -H -o name {self.dir_path}",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        ).stdout
        if out:
            return True
        return False

    @staticmethod
    def destroy_snap(snap_path):
        return subprocess.run(
            f"zfs destroy {snap_path}",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        ).stdout

    @staticmethod
    def zpool_list():
        out = subprocess.run(
            "zpool list -H -o name",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        ).stdout
        zpool_list = [zpool for zpool in out.decode("utf-8").split('\n')][:-1]
        return zpool_list
