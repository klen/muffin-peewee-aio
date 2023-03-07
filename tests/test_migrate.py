async def test_cli(app, db):
    assert "peewee-create" in app.manage.commands
    assert "peewee-migrate" in app.manage.commands
    assert "peewee-rollback" in app.manage.commands
    assert "peewee-list" in app.manage.commands
    assert "peewee-clear" in app.manage.commands
    assert "peewee-merge" in app.manage.commands


async def test_migrations(db, tmpdir, transaction):
    assert db.router

    db.router.migrate_dir = str(tmpdir.mkdir("migrations"))

    with db.manager.allow_sync():
        assert not db.router.todo
        assert not db.router.done
        assert not db.router.diff

        # Create migration
        name = db.router.create("test")
        assert name == "001_test"
        assert db.router.todo
        assert not db.router.done
        assert db.router.diff

        # Run migrations
        db.router.run()
        assert db.router.done
        assert not db.router.diff

        name = db.router.create()
        assert name == "002_auto"
