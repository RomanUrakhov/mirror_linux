from models.models import Repository, User
import datetime
from dateutil import relativedelta
from mirror.repository import LinuxRepoManager
from queries import task
from peewee import DoesNotExist


def get_repository_query(repo_id):
    repository = Repository.get_by_id(repo_id)
    return {
        "id": repo_id,
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


def repository_exist(name):
    try:
        Repository.get(Repository.name == name)
    except DoesNotExist:
        return False
    return True


def get_repository_list_query(offset=0, limit=15, username="", my=False):
    repository_list = []
    user = User.get(User.username == username)
    if not my:
        if user.group != 0:
            return "-1"
        query = Repository.select().offset(offset).limit(limit)
    else:
        query = Repository.select().where(Repository.user == user).offset(offset).limit(limit)

    for repository in query:
        repository_list.append({
            "id": repository.get_id(),
            "name": repository.name,
            "user": repository.user.username,
            "schedule_status": repository.schedule_status,
            "schedule_run": repository.schedule_run,
            "updated_at": repository.updated_at
        })
    return repository_list


def create_repository_query(json_repository, username):
    user = User.get(User.username == username)

    repository = Repository.create(
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
    )
    task.write_task_status(repo=repository, msg=f"{repository.name} creation")


def edit_repository_query(repo_id, json_repository):
    repository = Repository().get_by_id(repo_id)

    if repository_exist(json_repository['name']) and repository.name != json_repository['name']:
        return "-1"

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

    task.write_task_status(repo=repository, msg=f"{repository.name} editing")
    return 0


def delete_repository_query(repo_id):
    repository = Repository().get_by_id(repo_id)
    task.write_task_status(repo=repository, msg=f"{repository.name} deleting")
    try:
        manager = LinuxRepoManager(repository)
        manager.delete()
        repository.delete_instance()
    except Exception:
        # how to process exception?
        pass


def reset_repository_query(repo_id):
    repository = Repository().get_by_id(repo_id)
    task.write_task_status(repo=repository, msg=f"{repository.name} resetting")


def set_next_update_date(repo: Repository):
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
