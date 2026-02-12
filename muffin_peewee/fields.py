"""Custom fields/properties."""

from __future__ import annotations

import json
from contextlib import suppress
from datetime import datetime, timezone
from enum import EnumMeta
from typing import TYPE_CHECKING, Any, Generic, Literal, cast, overload

import peewee as pw
from asgi_tools.types import TV
from peewee_aio.fields import GenericField, JSONGenericField
from playhouse.postgres_ext import JSONField as PGJSONField
from playhouse.sqlite_ext import JSONField as SQLiteJSONField

if TYPE_CHECKING:
    from .types import TJSONDump, TJSONLoad


class JSONPGField(JSONGenericField[TV], PGJSONField):  # type: ignore[inconsistent-inheritance]
    pass


class JSONAsyncPGField(JSONPGField):
    def db_value(self, value):
        return value


class JSONSQLiteField(JSONGenericField[TV], SQLiteJSONField):  # type: ignore[inconsistent-inheritance]
    pass


class JSONAsyncSQLiteField(JSONSQLiteField):
    def db_value(self, value):
        return value


class JSONLikeField(JSONGenericField[TV], pw.Field):
    """Implement JSON field."""

    unpack = False
    field_type = "text"

    def __init__(
        self,
        json_dumps: TJSONDump | None = None,
        json_loads: TJSONLoad | None = None,
        *args,
        **kwargs,
    ):
        """Initialize the serializer."""
        self._json_dumps = json_dumps or json.dumps
        self._json_loads = json_loads or json.loads
        super().__init__(*args, **kwargs)

    def python_value(self, value):
        """Deserialize value from DB."""
        if value is not None and self.field_type == "text":
            with suppress(TypeError, ValueError):
                return self._json_loads(value)

        return value

    def db_value(self, value):
        """Convert python value to database."""
        if value is None:
            return value

        return self._json_dumps(value)


class EnumMixin(Generic[TV]):
    """Implement enum mixin."""

    def __init__(self, enum, *args, **kwargs):
        """Initialize the field."""
        self.enum = enum
        kwargs.setdefault("choices", [(e.value, e.name) for e in enum])
        super().__init__(*args, **kwargs)

    def db_value(self, value) -> TV | None:
        """Convert python value to database."""
        if value is None:
            return value

        return value.value

    def python_value(self, value: TV | None):
        """Convert database value to python."""
        if value is None:
            return value

        return self.enum(value)


class StrEnumField(EnumMixin[str], GenericField[TV], pw.CharField):
    """Implement enum field."""

    if TYPE_CHECKING:

        def __init__(self, enum: type[TV], **kwargs): ...


class IntEnumField(EnumMixin[int], GenericField[TV], pw.IntegerField):
    """Implement enum field."""

    if TYPE_CHECKING:

        def __init__(self, enum: type[TV], **kwargs): ...


class URLField(GenericField[TV], pw.CharField):
    """Implement URL field.

    The field is not validated, but it's just a placeholder for now.
    """

    if TYPE_CHECKING:

        @overload
        def __new__(cls, *args, null: Literal[True], **kwargs) -> URLField[str | None]: ...

        @overload
        def __new__(cls, *args, null: Literal[False] = False, **kwargs) -> URLField[str]: ...

        def __new__(cls, *args, **kwargs) -> Any: ...


with suppress(ImportError):
    from sqlite3 import register_adapter as sqlite_register

    from pendulum import instance
    from pendulum.date import Date
    from pendulum.datetime import DateTime
    from pendulum.parser import parse

    # Support pendulum DateTime in peewee (sqlite)
    sqlite_register(Date, lambda dd: dd.isoformat())
    sqlite_register(DateTime, lambda dt: dt.isoformat())

    UTC = timezone.utc
    from_isoformat = datetime.fromisoformat

    class DateTimeTZField(pw.DateTimeField, GenericField[TV]):
        """DateTime field with timezone support."""

        if TYPE_CHECKING:

            @overload
            def __new__(
                cls, *args, null: Literal[True], **kwargs
            ) -> DateTimeTZField[DateTime | None]: ...
            @overload
            def __new__(
                cls, *args, null: Literal[False] = False, **kwargs
            ) -> DateTimeTZField[DateTime]: ...

            def __new__(cls, *args, **kwargs) -> Any: ...

        def db_value(self, value: datetime | None) -> datetime | None:
            """Convert datetime to UTC."""
            if value is None:
                return value

            if isinstance(value, DateTime):
                return value.astimezone(UTC).naive()

            if isinstance(value, datetime):
                return value

            raise ValueError("Invalid datetime value")

        def python_value(self, value: str | datetime) -> DateTime:
            """Convert datetime to local timezone."""
            if isinstance(value, str):
                return cast("DateTime", parse(value))

            if isinstance(value, datetime):
                return instance(value)

            return value


class Choices:
    """Model's choices helper."""

    __slots__ = "_map", "_rmap"

    def __init__(self, choice: dict[str, Any] | EnumMeta | str, *choices: str):
        """Parse provided choices."""
        pw_choices = (
            [(value, name) for name, value in choice.items()]
            if isinstance(choice, dict)
            else (
                [(e.value, e.name) for e in choice]  # type: ignore[var-annotated]
                if isinstance(choice, EnumMeta)
                else [(choice, choice)]
            )
        )
        pw_choices.extend([(choice, choice) for choice in choices])

        self._map = {n: v for v, n in pw_choices}
        self._rmap = dict(pw_choices)

    def __str__(self) -> str:
        """Return string representation."""
        return ", ".join(self._map.keys())

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Choices: {self}>"

    def __iter__(self):
        """Iterate self."""
        return iter(self._rmap.items())

    def __getattr__(self, name: str, default=None):
        """Get choice value by name."""
        return self._map.get(name, default)

    def __getitem__(self, name: str):
        """Get value by name."""
        return self._map[name]

    def __call__(self, value):
        """Get name by value."""
        return self._rmap[value]

    def __deepcopy__(self, memo):
        """Deep copy self."""
        result = Choices(self._map)
        memo[id(self)] = result
        return result
