import peewee
import pytest

from muffin_peewee.fields import JSONAsyncPGField


@pytest.fixture
def backend():
    return "asyncpg"


async def test_asyncpg_json_field(db):
    @db.register
    class Test(db.Model):  # type: ignore[valid-type,misc]
        data = peewee.CharField()
        json = db.JSONField({})

    assert Test.json.field_type == "JSON"
    assert isinstance(Test.json, JSONAsyncPGField)
    assert Test.json.db_value({"key": "value"}) == {"key": "value"}
    assert Test.json.python_value({"key": "value"}) == {"key": "value"}
    assert Test.json.python_value('{"key": "value"}') == '{"key": "value"}'

    await Test.create_table()
    await Test.create(data="some", json={"key": "value"})

    instance = await Test.select().where(Test.json["key"] == "value").get()
    assert instance.json == {"key": "value"}
    assert isinstance(instance.json, dict)

    await Test.drop_table()
