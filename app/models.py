from peewee import *
import datetime
import hashlib
from . import db_wrapper


class User(db_wrapper.Model):
    username = CharField()
    password = CharField()
    group = IntegerField()

    @staticmethod
    def encrypt(passwd):
        return hashlib.sha256(passwd.encode('utf-8')).hexdigest()


class Repository(db_wrapper.Model):
    name = CharField()
    mirror_url = CharField()
    mirror_zpool = CharField()
    mirror_location = CharField()
    mirror_type = IntegerField(default=0)
    mirror_args = CharField()
    mirror_init = BooleanField(default=False)

    user = ForeignKeyField(User, backref='daemon', on_delete='cascade')

    schedule_status = BooleanField(default=False)
    schedule_run = BooleanField(default=False)
    schedule_number = IntegerField(default=1)

    schedule_minute = IntegerField(default=0)
    schedule_hour = IntegerField(default=0)
    schedule_day = IntegerField(default=0)
    schedule_month = IntegerField(default=0)
    schedule_year = IntegerField(default=0)

    schedule_next_update = DateTimeField(default=datetime.datetime.now())

    created_at = DateTimeField(default=datetime.datetime.now())
    updated_at = DateTimeField(default=datetime.datetime.now())


class Task(db_wrapper.Model):
    message = CharField()
    repository = CharField()
    user = CharField()
    date = DateTimeField(default=datetime.datetime.now)


class QueueTask(db_wrapper.Model):
    repository = ForeignKeyField(Repository, backref='repositories', unique=True, on_delete='cascade')
    pid = IntegerField()
