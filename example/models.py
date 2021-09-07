import datetime

import peewee

from example import db


class DataItem(db.Model):
    created = peewee.DateTimeField(default=datetime.datetime.utcnow)
    content = peewee.CharField()
