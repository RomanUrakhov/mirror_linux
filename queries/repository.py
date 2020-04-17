from models.models import *
import datetime
from dateutil.relativedelta import relativedelta
from mirror.repository import LinuxRepoManager
from tasks.TaskRunner import TaskRunner
from queries import task


def get_repository_query(id=1):
    repository = Repository.get_by_id(id)
    print(repository)
    return {
        "id": int(repository.__str__()),

        "name": repository.name,
        "mirror_url": repository.mirror_url,
        "mirror_zpool": repository.mirror_zpool,
        "mirror_location": repository.mirror_location,
        "mirror_type": repository.mirror_type,
        "mirror_args": repository.mirror_args,
        "user": repository.user.username,
        "mirror_init": repository.mirror_init,
        "schedule_status": repository.schedule_status,
        "schedule_run": repository.schedule_run,
        "schedule_number": repository.schedule_number,

        "schedule_minute": repository.schedule_minute,
        "schedule_hour": repository.schedule_hour,
        "schedule_day": repository.schedule_day,
        "schedule_month": repository.schedule_month,
        "schedule_year": repository.schedule_year,

        "created_at": repository.created_at,
        "updated_at": repository.updated_at,
    }


def get_repository_count_query(username=""):
    if username == "":
        query = Repository.select().count()
    else:
        user = User.get(User.username == username)
        query = Repository.select().where(Repository.user == user).count()

    return query


def check_repository_query(name):
    try:
        Repository.get(Repository.name == name)
    except DoesNotExist as e:
        return False
    return True


def get_repository_list_query(offset=0, limit=15, username="", my=False):
    repository_list = []
    query = None
    user = User.get(User.username == username)
    if not my:
        if user.group != 0:
            return "-1"
        query = Repository.select().offset(offset).limit(limit)
    else:
        query = Repository.select().where(Repository.user == user).offset(offset).limit(limit)

    for repository in query:
        repository_list.append({
            "id": int(repository.__str__()),
            "name": repository.name,
            "user": repository.user.username,
            "schedule_status": repository.schedule_status,
            "schedule_run": repository.schedule_run,
            "updated_at": repository.updated_at
        })
    return repository_list


def create_repository_query(json_repository, username):
    user = User.get(User.username == username)

    repository = Repository(
        name=json_repository["name"],
        mirror_url=json_repository["mirror_url"],
        mirror_zpool=json_repository["mirror_zpool"],
        mirror_location=json_repository["mirror_location"],
        mirror_type=json_repository["mirror_type"],
        mirror_args=json_repository["mirror_args"],

        user=user,

        schedule_status=json_repository["schedule_status"],
        schedule_number=json_repository["schedule_number"],

        schedule_minute=json_repository["schedule_minute"],
        schedule_hour=json_repository["schedule_hour"],
        schedule_day=json_repository["schedule_day"],
        schedule_month=json_repository["schedule_month"],
        schedule_year=json_repository["schedule_year"]
    ).save()
    repository = Repository.get(Repository.name == json_repository["name"])
    # создание таска здесь не должно быть -- задача модуля task (создать метод)
    Task(repository=repository.name, message="{} create".format(json_repository["name"]), user=user.username).save()
    TaskRunner(LinuxRepoManager(repository)).run()


def update_repository_query(id, json_repository, username):
    user = User.get(User.username == username)
    repository = Repository().get_by_id(id)

    if check_repository_query(json_repository["name"]) and repository.name != json_repository["name"]:
        return "-1"

    mirror_location = repository.mirror_location

    repository.name = json_repository["name"]
    repository.mirror_url = json_repository["mirror_url"]
    repository.mirror_zpool = json_repository["mirror_zpool"]
    repository.mirror_location = json_repository["mirror_location"]
    repository.mirror_type = json_repository["mirror_type"]
    repository.mirror_args = json_repository["mirror_args"]

    repository.schedule_status = json_repository["schedule_status"]
    repository.schedule_run = json_repository["schedule_run"]
    repository.schedule_number = json_repository["schedule_number"]

    repository.schedule_minute = json_repository["schedule_minute"]
    repository.schedule_hour = json_repository["schedule_hour"]
    repository.schedule_day = json_repository["schedule_day"]
    repository.schedule_month = json_repository["schedule_month"]
    repository.schedule_year = json_repository["schedule_year"]

    repository.updated_at = datetime.datetime.now()

    repository.save()

    repository = Repository.get(Repository.name == json_repository["name"])
    task.write_task_status(repo=repository, msg="{} update".format(json_repository["name"]))
    if repository.mirror_location != mirror_location:
        TaskRunner(LinuxRepoManager(repository)).run()
    return 0


def delete_repository_query(id, username):
    user = User.get(User.username == username)
    repository = Repository().get_by_id(id)
    TaskRunner(LinuxRepoManager(repository)).run()
    task.write_task_status(repo=repository, msg="{} delete".format(repository.name))
    repository.delete_instance()


def run_repository_query(id, username):
    user = User.get(User.username == username)
    repository = Repository().get_by_id(id)
    ###############
    TaskRunner(RepositoryUpdate(repository)).run()
    ###############
    Task(repository=repository.name, message="{} run".format(repository.name), user=user.username).save()


def reset_repository_query(id, username):
    user = User.get(User.username == username)
    repository = Repository().get_by_id(id)
    repository.mirror_init = False
    ###############
    TaskRunner(RepositoryReset(repository)).run()
    ###############
    Task(repository=repository.name, message="{} run".format(repository.name), user=user.username).save()


def update_date_task(repo: Repository):
    date = datetime.datetime.now()
    date += relativedelta(
        years=repo.schedule_year,
        months=repo.schedule_month,
        days=repo.schedule_day,
        hours=repo.schedule_hour,
        minutes=repo.schedule_minute
    )
    repo.schedule_next_update = date
    repo.save()


def init_mirror(repo: Repository):
    repo.mirror_init = True
    repo.save()


def deinit_mirror(repo: Repository):
    repo.mirror_init = False
    repo.save()
