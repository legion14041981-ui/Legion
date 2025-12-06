"""Fast JSON Serialization with orjson"""

import orjson
from starlette.responses import Response
from typing import Any


class ORJSONResponse(Response):
    """
    Fast JSON response using orjson (5-10x faster than standard json)
    
    Benefits:
    - 5-10x faster serialization
    - Lower CPU usage
    - Better P99 latency
    - Native datetime/UUID support
    """
    
    media_type = "application/json"
    
    def render(self, content: Any) -> bytes:
        return orjson.dumps(
            content,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )
