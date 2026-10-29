from typing import Any, Callable, TypeVar

TV = TypeVar("TV")
TJSONDump = Callable[[Any], str]
TJSONLoad = Callable[[str], Any]
