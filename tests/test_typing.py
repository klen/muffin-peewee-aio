"""Check the plugin's public type annotations.

`assert_type` is a no-op at runtime, these tests are verified by `pyrefly check`.
"""

from enum import Enum
from typing import assert_type

import muffin
import pendulum
from peewee_aio.fields import JSONGenericField

from muffin_peewee import EnumField, IntEnumField, Plugin, StrEnumField, URLField
from muffin_peewee.fields import DateTimeTZField


class Color(Enum):
    RED = "red"


class Num(Enum):
    ONE = 1


def test_enum_fields():
    field = StrEnumField(Color)
    assert_type(field, StrEnumField[Color])
    assert_type(field.python_value("red"), Color | None)
    assert_type(StrEnumField(Color, null=False), StrEnumField[Color])
    assert_type(StrEnumField(Color, null=True), StrEnumField[Color | None])
    assert_type(EnumField(Color), StrEnumField[Color])

    field = IntEnumField(Num)
    assert_type(field, IntEnumField[Num])
    assert_type(field.python_value(1), Num | None)
    assert_type(IntEnumField(Num, null=False), IntEnumField[Num])
    assert_type(IntEnumField(Num, null=True), IntEnumField[Num | None])


def test_url_field():
    assert_type(URLField(), URLField[str])
    assert_type(URLField(null=False), URLField[str])
    assert_type(URLField(null=True), URLField[str | None])


def test_datetime_field():
    field = DateTimeTZField()
    assert_type(field, DateTimeTZField[pendulum.DateTime])
    assert_type(field.python_value("2024-01-01"), pendulum.DateTime)
    assert_type(DateTimeTZField(null=True), DateTimeTZField[pendulum.DateTime | None])


def test_json_field():
    db = Plugin(muffin.Application(), connection="sqlite:///:memory:", migrations_enabled=False)
    assert_type(db.JSONField({"a": 1}), JSONGenericField[dict[str, int]])
    assert_type(db.JSONField({"a": 1}, null=True), JSONGenericField[dict[str, int] | None])
