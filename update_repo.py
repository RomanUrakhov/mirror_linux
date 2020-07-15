import sys

from playhouse.db_url import connect

import api_config
from app.models import Repository
from mirror.repository import LinuxRepoManager
from queries.repository import init_mirror


def run(repository: Repository):
    manager = LinuxRepoManager(repository)
    if not repository.mirror_init:
        if manager.filesystem_exist():
            manager.delete()
        manager.create()
        init_mirror(repository)
    # штатный процесс обновления
    manager.update()


if __name__ == '__main__':
    repo_id = sys.argv[1]
    # соединение с БД
    db = connect(api_config.DATABASE_URL, reuse_if_open=True)
    # привязываем модель ORM к БД
    db.bind([Repository])
    repo = Repository.get_by_id(repo_id)
    run(repo)
    db.close()
