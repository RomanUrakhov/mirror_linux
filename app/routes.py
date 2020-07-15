import re

from flask import jsonify, request, render_template, current_app as app
from flask_httpauth import HTTPBasicAuth
from peewee import DoesNotExist

import queries.repository
import queries.task
import queries.user
from mirror import zfs
from .models import User

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    try:
        User.get(User.username == username, User.password == User.encrypt(password))
    except DoesNotExist:
        return False
    return True


@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')


@app.route("/api/repository/check", methods=['POST'])
@auth.login_required
def check_repository():
    name = request.get_json()
    return jsonify(queries.repository.repository_exist(name["name"]))


@app.route("/api/repository", methods=['GET'])
@auth.login_required
def get_repository_list():
    offset = request.args.get("offset", default=0, type=int)
    limit = request.args.get("limit", default=15, type=int)
    data = queries.repository.get_repository_list_query(offset, limit, auth.username())
    if data == "-1":
        raise -1
    return jsonify(data)


@app.route("/api/repository/my", methods=['GET'])
@auth.login_required
def get_my_repository_list():
    offset = request.args.get("offset", default=0, type=int)
    limit = request.args.get("limit", default=15, type=int)
    return jsonify(queries.repository.get_repository_list_query(offset, limit, auth.username(), my=True))


@app.route("/api/repository/count", methods=['GET'])
@auth.login_required
def get_repository_count():
    return jsonify(queries.repository.get_repository_count_query())


@app.route("/api/repository/my/count", methods=['GET'])
@auth.login_required
def get_my_repository_count():
    return jsonify(queries.repository.get_repository_count_query(auth.username()))


@app.route("/api/repository/<int:repository_id>", methods=['GET'])
@auth.login_required
def get_repository(repository_id):
    return jsonify(queries.repository.get_repository_query(repository_id))


@app.route("/api/repository/create", methods=['POST'])
@auth.login_required
def create_repository():
    repository = request.get_json()
    if queries.repository.repository_exist(repository["name"]):
        return jsonify("-1")

    if int(repository["mirror_type"]) == 0:
        result = re.match(
            r"^(?:rsync:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$",
            repository["mirror_url"]
        )
    else:
        result = re.match(
            r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$",
            repository["mirror_url"]
        )
    if not result:
        return jsonify("-2")

    result = re.match(r"^[A-Za-z0-9_]+$", repository["mirror_location"])
    if not result:
        return jsonify("-3")

    # checks if the schedule is not set
    if not (repository["schedule_year"] or
            repository["schedule_month"] or
            repository["schedule_day"] or
            repository["schedule_hour"] or
            repository["schedule_minute"]):
        return jsonify("-4")

    queries.repository.create_repository_query(repository, auth.username())
    return jsonify("ok")


@app.route("/api/repository/<int:repository_id>/update", methods=['PUT'])
@auth.login_required
def update_repository(repository_id):
    repository = request.get_json()

    if int(repository["mirror_type"]) == 0:
        result = re.match(
            r"^(?:rsync:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$",
            repository["mirror_url"]
        )
    else:
        result = re.match(
            r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$",
            repository["mirror_url"]
        )

    if not result:
        return jsonify("-2")

    result = re.match(r"^[A-Za-z0-9_]+$", repository["mirror_location"])

    if not result:
        return jsonify("-3")

    # checks if the schedule is not set
    if not (repository["schedule_year"] or
            repository["schedule_month"] or
            repository["schedule_day"] or
            repository["schedule_hour"] or
            repository["schedule_minute"]):
        return jsonify("-4")

    code = queries.repository.edit_repository_query(repository_id, repository)
    if not code:
        return jsonify("ok")
    return jsonify(code)


@app.route("/api/repository/<int:repository_id>/delete", methods=['DELETE'])
@auth.login_required
def delete_repository(repository_id):
    queries.repository.delete_repository_query(repository_id)
    return jsonify("ok")


@app.route("/api/repository/<int:repository_id>/reset", methods=['get'])
@auth.login_required
def reset_repository(repository_id):
    queries.repository.reset_repository_query(repository_id)
    return jsonify("ok")


@app.route("/api/user/check", methods=['POST'])
@auth.login_required
def check_user():
    name = request.get_json()
    return jsonify(queries.user.check_user_query(name["name"]))


@app.route("/api/user/count", methods=['GET'])
@auth.login_required
def get_user_count():
    return jsonify(queries.user.get_user_count_query())


@app.route("/api/user", methods=['GET'])
@auth.login_required
def get_user_list():
    offset = request.args.get("offset", default=0, type=int)
    limit = request.args.get("limit", default=15, type=int)
    data = queries.user.get_user_list_query(offset, limit, auth.username())
    if data == "-1":
        raise -1
    return jsonify(data)


@app.route("/api/user/<int:user_id>", methods=['GET'])
@auth.login_required
def get_user(user_id):
    return jsonify(queries.user.get_user_query(user_id))


@app.route("/api/user/create", methods=['POST'])
@auth.login_required
def create_user():
    user = request.get_json()
    if queries.user.check_user_query(user["username"]):
        return jsonify("-1")

    queries.user.create_user_query(user)
    return jsonify("ok")


@app.route("/api/user/<int:user_id>/update", methods=['PUT'])
@auth.login_required
def update_user(user_id):
    user = request.get_json()
    code = queries.user.update_user_query(user_id, user)
    if not code:
        return jsonify("ok")
    return jsonify(code)


@app.route("/api/user/<int:user_id>/delete", methods=['DELETE'])
@auth.login_required
def delete_user(user_id):
    queries.user.delete_user_query(user_id)
    return jsonify("ok")


@app.route("/api/user/check_group", methods=['GET'])
@auth.login_required
def get_group():
    return jsonify(queries.user.get_group_query(auth.username()))


@app.route("/api/task/count", methods=['GET'])
@auth.login_required
def get_task_count():
    return jsonify(queries.task.get_task_count_query())


@app.route("/api/task", methods=['GET'])
@auth.login_required
def get_task_list():
    offset = request.args.get("offset", default=0, type=int)
    limit = request.args.get("limit", default=50, type=int)
    return jsonify(queries.task.get_task_list_query(offset, limit))


@app.route("/api/task/<int:task_id>", methods=['GET'])
@auth.login_required
def get_task(task_id):
    return jsonify(queries.task.get_task_query(task_id))


@app.route("/api/zpool", methods=['GET'])
@auth.login_required
def get_zpool_list_resp():
    return zfs.Zfs.zpool_list()
