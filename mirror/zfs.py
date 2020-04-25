# скрипты кот. зап. при обновлении и после сброса
import datetime
import subprocess
from utils import loger


class Zfs:
    """
    A class used for working with the zfs file system"

    Attributes
    ----------
    dir_path : str
        a unique path for creating a new file system

    Methods
    -------
    create()
        creates new zfs filesystem at `dir_path`

    delete()
        recursively deletes all file systems at `dir_path`

    snapshot()
        creates a snapshot of zfs file system at `dir_path`

    snapshots_list()
        returns a list of snapshots exist within zfs file system at `dir_path`

    delete_snap()
        deletes snapshot with specified name argument

    zpool_list()
        returns a list of existing zfs pools
    """

    def __init__(self, dir_path):
        self.dir_path = dir_path

    def create(self):
        """Creates new zfs filesystem at `dir_path`

        Returns
        _______
        a pair of values `execution code` and `message`: (code, msg).

        Return Codes
        ____________
        0: successful execution
        1: execution failed
        """

        try:
            return 0, subprocess.check_output(["zfs", "create", self.dir_path])
        except subprocess.CalledProcessError as e:
            return 1, e.output

    def delete(self):
        """Recursively deletes all file systems at `dir_path`

        Returns
        _______
        a pair of values `execution code` and `message`: (code, msg).

        Return Codes
        ____________
        0: successful execution
        1: execution failed
        """

        try:
            return 0, subprocess.check_output(["zfs", "destroy", "-r", self.dir_path])
        except subprocess.CalledProcessError as e:
            return 1, e.output

    def snapshot(self):
        """Creates a snapshot of zfs file system at `dir_path`

        Returns
        _______
        a pair of values `execution code` and `message`: (code, msg).

        Return Codes
        ____________
        0: successful execution
        1: execution failed
        """

        snap_name = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        try:
            res = subprocess.check_output(["zfs", "snapshot", f"{self.dir_path}@{snap_name}"])
        except subprocess.CalledProcessError as e:
            return 1, e.output
        return 0, res

    def snapshot_list(self):
        try:
            out = subprocess.check_output(
                f"zfs list -H -r -t snapshot -o name -S creation {self.dir_path}",
                shell=True,
            )
            snap_list = [snap for snap in out.decode("utf-8").split('\n')][:-1]
            return 0, snap_list
        except subprocess.CalledProcessError as e:
            return 1, e.output

    @staticmethod
    def destroy_snap(snap_path):
        """Destroys snapshot by its name`

        Returns
        _______
        result of executing the snapshot destroying command
        """
        try:
            return 0, subprocess.check_output(
                f"zfs destroy {snap_path}",
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            return 1, e.output

    @staticmethod
    def zpool_list():
        """Defines the names of ZFS storage device pools

        Returns
        _______
        a pair of values `execution code` and `message`: (code, msg). In case of successful execution returns
        byte string that contains names of ZFS pools separated by '\n' symbol

        Return Codes
        ____________
        0: successful execution
        1: execution failed
        """

        try:
            out = subprocess.check_output("zpool list -H -o name", shell=True)
            pool_list = [pool for pool in out.decode("utf-8").split('\n')][:-1]
            return 0, pool_list
        except subprocess.CalledProcessError as e:
            return 1, e.output
