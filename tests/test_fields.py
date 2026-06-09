from __future__ import annotations

import datetime as dt
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Type

import peewee
import pendulum
import pytest

from muffin_peewee import (
    Choices,
    IntEnumField,
    JSONAsyncPGField,
    JSONPGField,
    StrEnumField,
    URLField,
)
from muffin_peewee.fields import DateTimeTZField, JSONLikeField, JSONSQLiteField

if TYPE_CHECKING:
    from aio_databases.backends import ABCTransaction
    from peewee_aio import AIOModel

    from muffin_peewee import Plugin


async def test_json_field_save_and_query(
    db: Plugin, transaction: ABCTransaction, model_cls: Type[AIOModel]
):
    @db.register
    class Test(model_cls):  # type: ignore[valid-type,misc]
        data = peewee.CharField()
        json = db.JSONField({})

    await Test.create_table()

    instance = Test(data="some", json={"key": "value"})
    saved = await instance.save()

    assert saved.json == {"key": "value"}

    retrieved = await Test.select().where(Test.json["key"] == "value").get()
    assert retrieved.json == {"key": "value"}


async def test_json_field_returns_correct_backend_type(db: Plugin):
    backend = db.manager.backend.name  # type: ignore[misc]
    expected_types = {
        "aiosqlite": JSONSQLiteField,
        "aiopg": JSONPGField,
        "aiopg+pool": JSONPGField,
        "asyncpg": JSONAsyncPGField,
        "asyncpg+pool": JSONAsyncPGField,
    }

    expected = expected_types.get(backend)
    if expected is None:
        pytest.fail(f"Unexpected backend: {backend}")

    assert isinstance(db.JSONField({}), expected)


async def test_json_field_defaults_are_independent(db: Plugin):
    f1 = db.JSONField({})
    f2 = db.JSONField({})

    assert id(f1.default) != id(f2.default)


async def test_uuid_field_save_and_load(
    db: Plugin, transaction: ABCTransaction, model_cls: Type[AIOModel]
):
    @db.register
    class M(model_cls):  # type: ignore[valid-type,misc]
        data = peewee.UUIDField()

    await M.create_table()

    instance = M(data=uuid.uuid1())
    await instance.save()

    assert await M.get() == instance


async def test_enum_field_save_and_query(
    db: Plugin, transaction: ABCTransaction, model_cls: Type[AIOModel]
):
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

    await Test.create_table()

    instance = Test(data="some", str_enum=StrEnum.a, int_enum=IntEnum.a)
    saved = await instance.save()

    assert saved.str_enum == StrEnum.a
    assert saved.int_enum == IntEnum.a

    retrieved = await Test.get()
    assert retrieved.str_enum == StrEnum.a
    assert retrieved.int_enum == IntEnum.a

    found_by_int = await Test.select().where(Test.int_enum << [IntEnum.a, IntEnum.b]).get()
    assert found_by_int == saved

    found_by_str = await Test.select().where(Test.str_enum << [StrEnum.a, StrEnum.b]).get()
    assert found_by_str == saved


def test_enum_field_choices():
    class StrEnum(Enum):
        a = "A"
        b = "B"
        c = "C"

    class IntEnum(Enum):
        a = 1
        b = 2
        c = 3

    str_field = StrEnumField(StrEnum)
    int_field = IntEnumField(IntEnum)

    assert str_field.choices == [("A", "a"), ("B", "b"), ("C", "c")]
    assert int_field.choices == [(1, "a"), (2, "b"), (3, "c")]


def test_datetimetzfield():
    field = DateTimeTZField()

    py_value = field.python_value(dt.datetime.now(dt.timezone.utc))

    assert py_value.tz
    assert py_value.tz.name == "UTC"

    db_value = field.db_value(py_value)

    assert db_value.tzinfo is None


def test_choices_from_strings():
    choices = Choices("a", "b", "c")

    assert choices.a == "a"
    assert choices["a"] == "a"
    assert choices("a") == "a"
    assert list(choices) == [("a", "a"), ("b", "b"), ("c", "c")]


def test_choices_from_dict():
    choices = Choices({"a": "A", "b": "B", "c": "C"})

    assert choices.a == "A"
    assert choices["a"] == "A"
    assert choices("A") == "a"
    assert list(choices) == [("A", "a"), ("B", "b"), ("C", "c")]


def test_choices_from_enum():
    class MyEnum(Enum):
        a = "A"
        b = "B"
        c = "C"

    choices = Choices(MyEnum)

    assert choices.a == "A"
    assert choices["a"] == "A"
    assert choices("A") == "a"
    assert list(choices) == [("A", "a"), ("B", "b"), ("C", "c")]


def test_url_field():
    field = URLField()
    assert field


def test_json_like_field():
    field = JSONLikeField()
    assert field.db_value({"key": "value"}) == '{"key": "value"}'
    assert field.python_value('{"key": "value"}') == {"key": "value"}
    assert field.python_value(None) is None


async def test_enum_field_with_none_values(
    db: Plugin, transaction: ABCTransaction, model_cls: Type[AIOModel]
):
    class StrEnum(Enum):
        a = "A"
        b = "B"

    class IntEnum(Enum):
        a = 1
        b = 2

    @db.register
    class Test(model_cls):  # type: ignore[valid-type,misc]
        data = peewee.CharField()
        str_enum = StrEnumField(StrEnum, null=True)
        int_enum = IntEnumField(IntEnum, null=True)

    await Test.create_table()

    instance = Test(data="some", str_enum=None, int_enum=None)
    saved = await instance.save()

    assert saved.str_enum is None
    assert saved.int_enum is None

    retrieved = await Test.get()
    assert retrieved.str_enum is None
    assert retrieved.int_enum is None


def test_datetime_tz_field_with_pendulum():
    field = DateTimeTZField()
    now = pendulum.now()

    db_value = field.db_value(now)
    assert db_value.tzinfo is None

    py_value = field.python_value(db_value)
    assert isinstance(py_value, pendulum.DateTime)


def test_datetime_tz_field_invalid_value_raises():
    field = DateTimeTZField()
    with pytest.raises(ValueError, match="Invalid datetime value"):
        field.db_value("not a datetime")
