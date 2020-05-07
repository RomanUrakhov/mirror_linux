from models.models import Repository, Task


def get_task_query(id=1):
    task = Task.get_by_id(id)
    return {
        "id": task.get_id(),
        "repository": task.repository,
        "message": task.message[-20000:],
        "user": task.user,
        "date": task.date,
    }


def get_task_count_query():
    return Task.select().count()


def get_task_list_query(offset=0, limit=15):
    task_list = []
    for task in Task.select().offset(offset).limit(limit):
        task_list.append({
            "id": task.getid(),
            "repository": task.repository,
            "message": task.message[:50],
            "user": task.user,
            "date": task.date,
        })
    return task_list


def write_task_status(repo: Repository, msg):
    if msg:
        if type(msg) is not str:
            if type(msg) is tuple:
                if type(msg[1]) in (bytes, bytearray):
                    msg = f"code: {msg[0]}, message: {msg[1].decode('utf-8')}"
                elif type(msg[1]) is str:
                    msg = f"code: {msg[0]}, message: {msg[1]}"
                else:
                    msg = "Unreadable characters"
            else:
                msg = "Unreadable characters"
        Task(repository=repo.name, message=msg, user=repo.user.username).save()
