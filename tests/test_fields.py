import peewee


async def test_json_field(db, transaction):
    from muffin_peewee import JSONField

    @db.register
    class Test(peewee.Model):
        data = peewee.CharField()
        json = JSONField(default={})

    manager = db.manager

    await manager.create_tables(Test)

    ins = Test(data='some', json={'key': 'value'})
    ins = await manager.save(ins)
    assert ins.json

    test = await manager.get(Test)
    assert test.json == {'key': 'value'}


async def test_uuid(db, transaction):
    """ Test for UUID in Sqlite. """

    @db.register
    class M(peewee.Model):
        data = peewee.UUIDField()

    await db.manager.create_tables(M)

    import uuid
    m = M(data=uuid.uuid1())
    await db.manager.save(m)

    assert await db.manager.get(M) == m
