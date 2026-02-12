from __future__ import annotations

import datetime as dt
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Type

import peewee

from muffin_peewee import Choices, IntEnumField, JSONPGField, StrEnumField
from muffin_peewee.fields import DateTimeTZField, JSONSQLiteField

if TYPE_CHECKING:
    from aio_databases.backends import ABCTransaction
    from peewee_aio import AIOModel

    from muffin_peewee import Plugin


async def test_json_field(db: Plugin, transaction: ABCTransaction, model_cls: Type[AIOModel]):
    @db.register
    class Test(model_cls):  # type: ignore[valid-type,misc]
        data = peewee.CharField()
        json = db.JSONField(dict)

    await Test.create_table()

    inst = Test(data="some", json={"key": "value"})
    inst = await inst.save()
    assert inst.json

    test = await Test.select().where(Test.json["key"] == "value").get()
    assert test.json == {"key": "value"}

    assert isinstance(db.JSONField(dict), JSONSQLiteField)

    db.manager.backend.db_type = "postgresql"  # type: ignore[misc]
    assert isinstance(db.JSONField(dict), JSONPGField)


async def test_uuid(db: Plugin, transaction: ABCTransaction, model_cls: Type[AIOModel]):
    """Test for UUID in Sqlite."""

    @db.register
    class M(model_cls):  # type: ignore[valid-type,misc]
        data = peewee.UUIDField()

    await M.create_table()

    m = M(data=uuid.uuid1())
    await m.save()

    assert await M.get() == m


async def test_enum_field(db: Plugin, transaction: ABCTransaction, model_cls: Type[AIOModel]):

    class StrEnum(Enum):
        a = "A"
        b = "B"
        c = "C"

    class IntEnum(Enum):
        a = 1
        b = 2
        c = 3

    @db.register
    class Test(model_cls):  # type: ignore[valid-type,misc]
        data = peewee.CharField()
        str_enum = StrEnumField(StrEnum)
        int_enum = IntEnumField(IntEnum)

    assert Test.str_enum.choices == [("A", "a"), ("B", "b"), ("C", "c")]
    assert Test.int_enum.choices == [(1, "a"), (2, "b"), (3, "c")]

    await Test.create_table()

    inst = Test(data="some", str_enum=StrEnum.a, int_enum=IntEnum.a)
    inst = await inst.save()
    assert inst.str_enum == StrEnum.a
    assert inst.int_enum == IntEnum.a

    test = await Test.get()
    assert test.str_enum == StrEnum.a
    assert test.int_enum == IntEnum.a

    assert await Test.select().where(Test.int_enum << [IntEnum.a, IntEnum.b]).get()
    assert await Test.select().where(Test.str_enum << [StrEnum.a, StrEnum.b]).get()


async def test_datetimetzfield():

    field = DateTimeTZField()
    assert field

    py_value = field.python_value(dt.datetime.now(dt.timezone.utc))
    assert py_value
    assert py_value.tz
    assert py_value.tz.name == "UTC"

    db_value = field.db_value(py_value)
    assert db_value
    assert db_value.tzinfo is None


async def test_choices(db: Plugin):

    choices = Choices("a", "b", "c")

    assert choices.a == "a"
    assert choices.b == "b"
    assert choices.c == "c"
    assert choices["a"] == "a"
    assert choices["b"] == "b"
    assert choices["c"] == "c"
    assert choices("a") == "a"

    assert list(choices) == [("a", "a"), ("b", "b"), ("c", "c")]

    choices = Choices({"a": "A", "b": "B", "c": "C"})
    assert choices.a == "A"
    assert choices["a"] == "A"
    assert choices("A") == "a"

    assert list(choices) == [("A", "a"), ("B", "b"), ("C", "c")]

    class MyEnum(Enum):
        a = "A"
        b = "B"
        c = "C"

    choices = Choices(MyEnum)
    assert choices.a == "A"
    assert choices["a"] == "A"
    assert choices("A") == "a"

    assert list(choices) == [("A", "a"), ("B", "b"), ("C", "c")]
