from queries.repository import create_repository_query
from app.models import User


def init_user():
    User(username="root", password=User().encrypt("123"), group=0).save()
    User(username="user1", password=User().encrypt("123"), group=1).save()


def init_repos():
    for i in range(1):
        create_repository_query({
            "mirror_zpool": "zroot",
            "mirror_args": "-vaHz",
            "mirror_location": f"debian{i}",
            "mirror_type": 0,
            "mirror_url": "rsync://mirror.yandex.ru/debian/doc/FAQ/",
            "name": f"debian{i}",
            "schedule_day": 0,
            "schedule_hour": 1,
            "schedule_minute": 0,
            "schedule_month": 0,
            "schedule_number": 2,
            "schedule_status": True,
            "schedule_year": 0
        }, "root")

        create_repository_query({
            "mirror_zpool": "zroot",
            "mirror_args": "-vaHz",
            "mirror_location": f"centos{i}",
            "mirror_type": 0,
            "mirror_url": "rsync://mirror.yandex.ru/debian/doc/FAQ/",
            "name": f"centOS{i}",
            "schedule_day": 0,
            "schedule_hour": 1,
            "schedule_minute": 0,
            "schedule_month": 0,
            "schedule_number": 2,
            "schedule_status": True,
            "schedule_year": 0
        }, "user1")

        create_repository_query({
            "mirror_zpool": "zroot",
            "mirror_args": "-vaHz",
            "mirror_location": f"opensuse{i}",
            "mirror_type": 0,
            "mirror_url": "rsync://mirror.yandex.ru/debian/doc/FAQ/",
            "name": f"opensuse{i}",
            "schedule_day": 0,
            "schedule_hour": 1,
            "schedule_minute": 0,
            "schedule_month": 0,
            "schedule_number": 2,
            "schedule_status": False,
            "schedule_year": 0
        }, "user1")

        create_repository_query({
            "mirror_location": f"ubuntu{i}",
            "mirror_zpool": "zroot",
            "mirror_args": "-vaHz",
            "mirror_type": 0,
            "mirror_url": "rsync://mirror.yandex.ru/debian/doc/FAQ/",
            "name": f"ubuntu{i}",
            "schedule_day": 0,
            "schedule_hour": 2,
            "schedule_minute": 0,
            "schedule_month": 0,
            "schedule_number": 2,
            "schedule_status": True,
            "schedule_year": 0
        }, "root")
