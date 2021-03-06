async def test_cli(app, db):
    assert 'pw_create' in app.manage.commands
    assert 'pw_migrate' in app.manage.commands
    assert 'pw_rollback' in app.manage.commands
    assert 'pw_list' in app.manage.commands


async def test_migrations(db, tmpdir, transaction):
    assert db.router

    db.router.migrate_dir = str(tmpdir.mkdir('migrations'))

    with db.manager.allow_sync():
        assert not db.router.todo
        assert not db.router.done
        assert not db.router.diff

        # Create migration
        name = db.router.create('test')
        assert '001_test' == name
        assert db.router.todo
        assert not db.router.done
        assert db.router.diff

        # Run migrations
        db.router.run()
        assert db.router.done
        assert not db.router.diff

        name = db.router.create()
        assert '002_auto' == name
