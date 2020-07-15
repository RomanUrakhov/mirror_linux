from app import db_wrapper, create_app
from app.models import User, Task, Repository, QueueTask
from utils.test_data import init_repos, init_user

application = create_app()

with db_wrapper.database:
    db_wrapper.database.create_tables([User, Task, Repository, QueueTask], safe=True)
    init_user()  # тестовые пользователи
    init_repos()  # тестовые репозиториии

if __name__ == '__main__':
    application.run()
