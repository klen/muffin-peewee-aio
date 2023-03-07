from enum import Enum

import peewee


async def test_json_field(db, transaction):
    from muffin_peewee import JSONField

    @db.register
    class Test(db.Model):
        data = peewee.CharField()
        json = JSONField(default={})

    await Test.create_table()

    inst = Test(data="some", json={"key": "value"})
    inst = await inst.save()
    assert inst.json

    test = await Test.get()
    assert test.json == {"key": "value"}


async def test_uuid(db, transaction):
    """Test for UUID in Sqlite."""

    @db.register
    class M(db.Model):
        data = peewee.UUIDField()

    await M.create_table()

    import uuid

    m = M(data=uuid.uuid1())
    await m.save()

    assert await M.get() == m


async def test_enum_field(db, transaction):
    from muffin_peewee import EnumField

    class MyEnum(Enum):
        a = "A"
        b = "B"
        c = "C"

    @db.register
    class Test(db.Model):
        data = peewee.CharField()
        enum = EnumField(MyEnum)

    await Test.create_table()

    inst = Test(data="some", enum=MyEnum.a)
    inst = await inst.save()
    assert inst.enum == MyEnum.a

    test = await Test.get()
    assert test.enum == MyEnum.a


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
