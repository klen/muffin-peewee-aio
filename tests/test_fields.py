from enum import Enum
from typing import Type

import peewee
from peewee_aio import AIOModel


async def test_json_field(db, transaction, model_cls: Type[AIOModel]):
    from muffin_peewee import JSONLikeField as JSONField

    @db.register
    class Test(model_cls):
        data = peewee.CharField()
        json = JSONField(default={})

    await Test.create_table()

    inst = Test(data="some", json={"key": "value"})
    inst = await inst.save()
    assert inst.json

    test = await Test.get()
    assert test.json == {"key": "value"}


async def test_uuid(db, transaction, model_cls: Type[AIOModel]):
    """Test for UUID in Sqlite."""

    @db.register
    class M(model_cls):
        data = peewee.UUIDField()

    await M.create_table()

    import uuid

    m = M(data=uuid.uuid1())
    await m.save()

    assert await M.get() == m


async def test_enum_field(db, transaction):
    from muffin_peewee import IntEnumField, StrEnumField

    class StrEnum(Enum):
        a = "A"
        b = "B"
        c = "C"

    class IntEnum(Enum):
        a = 1
        b = 2
        c = 3

    @db.register
    class Test(db.Model):
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


async def test_choices(db):
    from muffin_peewee import Choices

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
