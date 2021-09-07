"""Application's views."""

import random
import string

import muffin

from . import app, db
from .models import DataItem


@app.route('/')
async def list(request):
    """List items."""
    objects = await db.manager.run(DataItem.select())
    template = """
        <html>
            <a href="/generate"> Generate new Item </a>&nbsp;&nbsp;&nbsp;
            <a href="/clean"> Clean everything </a>
            <h3>Items in database: </h3>
            <ul>%s</ul>
        </html>
    """ % "".join(f"<li>{d.__data__!r}</li>" for d in objects)
    return template


@app.route('/generate')
async def generate(request):
    """Create a new DataItem."""
    await db.manager.create(
        DataItem,
        content=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    )
    return muffin.ResponseRedirect('/')


@app.route('/clean')
async def clean(request):
    """Create a new DataItem."""
    await db.manager.execute(DataItem.delete())
    return muffin.ResponseRedirect('/')
