import subprocess
import config
from utils import loger


@loger.output
def run_user_script_update(repo):
    if not config.on_update or config.on_update == "":
        return 0, "ok"

    location = f"/{repo.mirror_zpool}/{repo.mirror_location}"
    if not config.isWork:
        print(f"Run user script update: {config.on_update} {repo.get_id()} {location}")
        return 0, "ok"
    else:
        try:
            return 0, subprocess.check_output([config.on_update, str(repo.get_id()), location])
        except subprocess.CalledProcessError as e:
            return 1, e.output


@loger.output
def run_user_script_truncate(repo):
    if not config.on_update or config.on_truncate == "":
        return 0, "ok"

    if not config.isWork:
        print(f"Run user script truncate: {config.on_truncate}  {repo.get_id()} ")
        return 0, "ok"
    else:
        try:
            return 0, subprocess.check_output([config.on_truncate, str(repo.get_id())])
        except subprocess.CalledProcessError as e:
            return 1, e.output
