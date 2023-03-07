"""Custom fields/properties."""

from __future__ import annotations

import json
from contextlib import suppress
from enum import EnumMeta
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import peewee as pw

try:
    from playhouse.postgres_ext import Json, JsonLookup
except ImportError:
    Json = JsonLookup = None

if TYPE_CHECKING:
    from .types import TJSONDump, TJSONLoad


class JSONField(pw.Field):

    """Implement JSON field."""

    unpack = False

    def __init__(
        self,
        json_dumps: Optional[TJSONDump] = None,
        json_loads: Optional[TJSONLoad] = None,
        *args,
        **kwargs,
    ):
        """Initialize the serializer."""
        self._json_dumps = json_dumps or json.dumps
        self._json_loads = json_loads or json.loads
        super(JSONField, self).__init__(*args, **kwargs)

    def __getitem__(self, value) -> JsonLookup:
        """Lookup item in database."""
        return JsonLookup(self, [value])

    @cached_property
    def field_type(self):
        """Return database field type."""
        database = self.model._meta.database
        if isinstance(database, pw.Proxy):
            database = database.obj
        if Json and isinstance(database, pw.PostgresqlDatabase):
            return "json"
        return "text"

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

        if self.field_type == "text":
            return self._json_dumps(value)

        if not isinstance(value, Json):
            return pw.Cast(self._json_dumps(value), "json")

        return value


class EnumField(pw.CharField):

    """Implement enum field."""

    def __init__(self, enum: EnumMeta, *args, **kwargs):
        """Initialize the field."""
        self.enum = enum
        kwargs.setdefault(
            "choices",
            [(e.value, e.name) for e in enum],  # type: ignore[var-annotated]
        )
        super().__init__(*args, **kwargs)

    def db_value(self, value) -> Optional[str]:
        """Convert python value to database."""
        if value is None:
            return value

        return value.value

    def python_value(self, value: Optional[str]):
        """Convert database value to python."""
        if value is None:
            return value

        return self.enum(value)


class Choices:

    """Model's choices helper."""

    __slots__ = "_map", "_rmap"

    def __init__(self, choice: Union[Dict[str, Any], EnumMeta, str], *choices: str):
        """Parse provided choices."""
        pw_choices = (
            [(value, name) for name, value in choice.items()]
            if isinstance(choice, dict)
            else [(e.value, e.name) for e in choice]  # type: ignore[var-annotated]
            if isinstance(choice, EnumMeta)
            else [(choice, choice)]
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
