from typing import Any, Callable

TJSONDump = Callable[[Any], str]
TJSONLoad = Callable[[str], Any]
