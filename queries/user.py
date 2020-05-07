from models.models import User
from peewee import DoesNotExist


def get_user_query(id=1):
    user = User.get_by_id(id)
    return {
        "id": user.get_id(),
        "username": user.username,
        "group": user.group,
    }


def check_user_query(name):
    try:
        User.get(User.username == name)
    except DoesNotExist:
        return False
    return True


def get_user_count_query():
    return User.select().count()


def get_user_list_query(offset=0, limit=15, username=""):
    user_list = []

    user = User.get(User.username == username)
    if user.group != 0:
        return "-1"

    for user in User.select().offset(offset).limit(limit):
        user_list.append({
            "id": user.get_id(),
            "username": user.username,
            "group": user.group,
        })
    return user_list


def create_user_query(json_user):
    User(
        username=json_user["username"],
        password=User().sha256(json_user["password"]),
        group=json_user["group"]
    ).save()


def update_user_query(id, json_user):
    user = User().get_by_id(id)
    if check_user_query(json_user["username"]) and user.username != json_user["username"]:
        return "-1"

    user.username = json_user["username"]
    if json_user["password"]:
        user.password = User().sha256(json_user["password"])
    user.group = json_user["group"]
    user.save()


def delete_user_query(id):
    user = User().get_by_id(id)
    if user.username == "root":
        raise -1
    user.delete_instance(id)


def get_group_query(username):
    user = User.get(User.username == username)
    return {
        "id": user.get_id(),
        "username": user.username,
        "group": user.group
    }
