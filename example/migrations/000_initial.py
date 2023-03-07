""" Peewee migrations. """

import datetime as dt

import peewee as pw


def migrate(migrator, database, **kwargs):
    """ Write your migrations here.

    > Model = migrator.orm['name']

    > migrator.sql(sql)
    > migrator.create_table(Model)
    > migrator.drop_table(Model, cascade=True)
    > migrator.add_columns(Model, **fields)
    > migrator.change_columns(Model, **fields)
    > migrator.drop_columns(Model, *field_names, cascade=True)
    > migrator.rename_column(Model, old_field_name, new_field_name)
    > migrator.rename_table(Model, new_table_name)
    > migrator.add_index(Model, *col_names, unique=False)
    > migrator.drop_index(Model, index_name)
    > migrator.add_not_null(Model, field_name)
    > migrator.drop_not_null(Model, field_name)
    > migrator.add_default(Model, field_name, default)

    """
    @migrator.create_table
    class DataItem(pw.Model):
        created = pw.DateTimeField(default=dt.datetime.utcnow)
        content = pw.CharField()
