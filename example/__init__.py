"""Setup the application."""

import muffin

import muffin_peewee

# Setup application
app: muffin.Application = muffin.Application(
    "example",

    DEBUG=True,
    PEEWEE_CONNECTION="sqlite:///example.db",
    PEEWEE_MIGRATIONS_PATH="example/migrations",
)
db: muffin_peewee.Plugin = muffin_peewee.Plugin(app)

# Register views
from example.views import *  # noqa
