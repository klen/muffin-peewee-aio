"""Custom fields/properties."""

from __future__ import annotations

import json
from contextlib import suppress
from enum import EnumMeta
from typing import TYPE_CHECKING, Any, Dict, Generic, Literal, Optional, Union, overload

import peewee as pw
from asgi_tools.types import TJSON, TV
from peewee_aio.fields import GenericField
from playhouse.postgres_ext import JSONField as PGJSONField

if TYPE_CHECKING:
    from .types import TJSONDump, TJSONLoad


class JSONLikeField(pw.Field, GenericField[TV]):

    """Implement JSON field."""

    unpack = False
    field_type = "text"

    @overload
    def __init__(
        self: JSONLikeField[TJSON],
        *args,
        null: Literal[False] = ...,
        **kwargs,
    ):
        ...

    @overload
    def __init__(
        self: JSONLikeField[Optional[TJSON]],
        *args,
        null: Literal[True] = ...,
        **kwargs,
    ):
        ...

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


class JSONPGField(PGJSONField, GenericField[TV]):
    @overload
    def __init__(self: JSONPGField[TJSON], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(
        self: JSONPGField[Optional[TJSON]],
        *args,
        null: Literal[True] = ...,
        **kwargs,
    ):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EnumMixin(Generic[TV]):

    """Implement enum mixin."""

    def __init__(self, enum: EnumMeta, *args, **kwargs):
        """Initialize the field."""
        self.enum = enum
        kwargs.setdefault(
            "choices",
            [(e.value, e.name) for e in enum],  # type: ignore[var-annotated]
        )
        super().__init__(*args, **kwargs)

    def db_value(self, value) -> Optional[TV]:
        """Convert python value to database."""
        if value is None:
            return value

        return value.value

    def python_value(self, value: Optional[TV]):
        """Convert database value to python."""
        if value is None:
            return value

        return self.enum(value)


class StrEnumField(EnumMixin[str], pw.CharField, GenericField[EnumMeta]):

    """Implement enum field."""


class IntEnumField(EnumMixin[int], pw.IntegerField, GenericField[EnumMeta]):

    """Implement enum field."""


class URLField(pw.CharField, GenericField[TV]):

    """Implement URL field.

    The field is not validated, but it's just a placeholder for now.
    """

    @overload
    def __init__(self: URLField[str], *args, null: Literal[False] = ..., **kwargs):
        ...

    @overload
    def __init__(
        self: URLField[Optional[str]],
        *args,
        null: Literal[True] = ...,
        **kwargs,
    ):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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
