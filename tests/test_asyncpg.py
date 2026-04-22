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

    # Converters pass values through as-is (asyncpg json=True handles encoding/decoding)
    assert Test.json.db_value({"key": "value"}) == {"key": "value"}
    assert Test.json.python_value({"key": "value"}) == {"key": "value"}
    assert Test.json.python_value('{"key": "value"}') == '{"key": "value"}'

    await Test.create_table()
    await Test.create(data="some", json={"key": "value"})

    inst = await Test.select().where(Test.json["key"] == "value").get()
    assert inst.json == {"key": "value"}
    assert isinstance(inst.json, dict)

    inst = await inst.save()
    assert inst.json == {"key": "value"}

    inst = await Test.select().where(Test.json["key"] == "value").get()
    assert inst.json == {"key": "value"}
    assert isinstance(inst.json, dict)

    await Test.drop_table()
