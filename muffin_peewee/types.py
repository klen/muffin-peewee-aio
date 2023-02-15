from typing import Any, Callable, Dict, List, Tuple, Union

TJSONDump = Callable[[Any], str]
TJSONLoad = Callable[[str], Any]
TChoice = Union[str, Tuple[str, Any]]
TChoices = Union[Dict[str, Any], List[TChoice]]
