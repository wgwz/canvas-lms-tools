from typing import Any, Dict, Iterator, Optional

# Request types:
RequestHeaders = Optional[Dict[str, Any]]
RequestParams = Optional[Dict[str, Any]]

PaginatedResponse = Iterator[Dict[Any, Any]]
