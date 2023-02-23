import datetime

import peewee
from peewee_aio.model import AIOModel

from example import db


@db.register
class DataItem(AIOModel):
    created = peewee.DateTimeField(default=datetime.datetime.utcnow)
    content = peewee.CharField()
