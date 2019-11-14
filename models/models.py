from peewee import *
from models.db_getter import get_db
import datetime

db = get_db()

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField()
    password = CharField()
    group = IntegerField()

class Repository(BaseModel):
    name = CharField()
    mirror_url = CharField()
    mirror_location = CharField()
    mirror_type = IntegerField(default=0)
    user = ForeignKeyField(User, backref='tasks')

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

class Task(BaseModel):
    message = CharField()
    repository = ForeignKeyField(Repository, backref='tasks')
    user = ForeignKeyField(User, backref='logs')
    date = DateTimeField(default=datetime.datetime.now)

class QueueTask(BaseModel):
    repository = ForeignKeyField(Repository, backref='repositorys', unique=True)