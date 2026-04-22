import peewee
import pytest

from muffin_peewee.fields import JSONAsyncPGField


@pytest.fixture
def backend():
    return "asyncpg"


async def test_json_field(db):
    assert db.manager.backend.name == "asyncpg"

    @db.register
    class Test(db.Model):  # type: ignore[valid-type,misc]
        data = peewee.CharField()
        json = db.JSONField({})

    assert Test.json.field_type == "JSON"
    assert isinstance(Test.json, JSONAsyncPGField)

    await Test.create_table()
    await Test.create(data="some", json={"key": "value"})

    inst = await Test.select().where(Test.json["key"] == "value").get()
    assert inst.json == {"key": "value"}

    inst = await inst.save()
    assert inst.json

    inst = await Test.select().where(Test.json["key"] == "value").get()
    assert inst.json == {"key": "value"}

    await Test.drop_table()
