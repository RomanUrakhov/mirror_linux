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
    snapshots_limit : int
        a maximum number of zfs-snapshots that can be created within a given file system

    Methods
    -------
    create()
        creates new zfs filesystem at `dir_path`

    delete()
        recursively deletes all file systems at `dir_path`

    reset()
        resets (deletes and then creates new one) zfs file system at `dit_path`

    snapshot()
        creates a snapshot of zfs file system at `dir_path`

    snapshots_count()
        counts a number of snapshots exist within zfs file system at `dir_path`
    """

    def __init__(self, dir_path, snapshots_limit=1):
        self.dir_path = dir_path
        self.snapshots_limit = snapshots_limit

    @loger.output
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

    @loger.output
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

    @loger.output
    def reset(self):
        """Resets (deletes and then creates new one) zfs file system at `dit_path`

        Returns
        _______
        a pair of values `execution code` and `message`: (code, msg).

        Return Codes
        ____________
        0: successful execution
        1: execution failed
        """
        res = self.delete()
        res2 = self.create()
        if not res and not res2:
            return 0, "reset zfs successfully done"
        else:
            return 1, "reset zfs filed"

    @loger.output
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
            if self.snapshots_count() > self.snapshots_limit:
                res += self.destroy_latest_snap()
        except subprocess.CalledProcessError as e:
            return 1, e.output
        return 0, res

    def snapshots_count(self):
        """Counts a number of snapshots exist within zfs file system at `dir_path`

        Returns
        _______
        int number of snapshots
        """

        snap_count = subprocess.check_output(
            f"zfs list -H -r -t snapshot -o name -S creation {self.dir_path} | wc -l",
            shell=True,
        )
        return int(snap_count)

    def destroy_latest_snap(self):
        """Destroys latest snapshot to save the condition `current_snap_count` = `snapshots_limit`

        Returns
        _______
        result of executing the snapshot destroying command
        """

        return subprocess.check_output(
            f"zfs list -H -r -t snapshot -o name -S creation {self.dir_path} | "
            f"tail -1 | xargs -n 1 zfs destroy",
            shell=True,
        )

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
            return 0, subprocess.check_output(
                "zpool list | awk '{if (FNR > 1) print $1}'",
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            return 1, e.output
