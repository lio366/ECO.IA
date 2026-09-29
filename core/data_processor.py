"""Data processing service — transforms and analyzes data payloads."""
import logging
import json
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes data payloads with various operations."""

    SUPPORTED_OPERATIONS = [
        "summarize", "classify", "extract", "transform",
        "validate", "aggregate", "filter", "sort",
    ]

    async def process(
        self,
        data: Any,
        operation: str,
        options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Process data with the given operation."""
        if operation not in self.SUPPORTED_OPERATIONS:
            return {
                "status": "error",
                "message": f"Unsupported operation: {operation}. "
                           f"Supported: {self.SUPPORTED_OPERATIONS}",
            }

        options = options or {}
        handler = getattr(self, f"_op_{operation}", self._op_default)
        result = await handler(data, options)

        logger.info("DataProcessor: op=%s input_type=%s", operation, type(data).__name__)
        return {
            "status": "processed",
            "operation": operation,
            "input_type": type(data).__name__,
            "result": result,
        }

    async def _op_summarize(self, data: Any, opts: Dict) -> str:
        if isinstance(data, dict):
            return f"Dict with {len(data)} keys: {list(data.keys())[:5]}"
        if isinstance(data, list):
            return f"List with {len(data)} items"
        return str(data)[:200]

    async def _op_classify(self, data: Any, opts: Dict) -> Dict:
        return {"type": type(data).__name__, "size": len(str(data))}

    async def _op_extract(self, data: Any, opts: Dict) -> Any:
        fields = opts.get("fields", [])
        if isinstance(data, dict) and fields:
            return {k: data.get(k) for k in fields}
        return data

    async def _op_transform(self, data: Any, opts: Dict) -> Any:
        fmt = opts.get("format", "json")
        if fmt == "json":
            return json.loads(json.dumps(data, default=str))
        return str(data)

    async def _op_validate(self, data: Any, opts: Dict) -> Dict:
        schema = opts.get("schema", {})
        errors = []
        if schema and isinstance(data, dict):
            for field, typ in schema.items():
                if field not in data:
                    errors.append(f"Missing field: {field}")
        return {"valid": len(errors) == 0, "errors": errors}

    async def _op_aggregate(self, data: Any, opts: Dict) -> Any:
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            return {
                "count": len(data), "sum": sum(data),
                "min": min(data), "max": max(data),
                "avg": sum(data) / len(data) if data else 0,
            }
        return {"count": len(data) if hasattr(data, "__len__") else 1}

    async def _op_filter(self, data: Any, opts: Dict) -> Any:
        condition = opts.get("condition", {})
        if isinstance(data, list) and condition:
            key = condition.get("key")
            value = condition.get("value")
            if key:
                return [item for item in data if isinstance(item, dict) and item.get(key) == value]
        return data

    async def _op_sort(self, data: Any, opts: Dict) -> Any:
        if isinstance(data, list):
            key = opts.get("key")
            reverse = opts.get("reverse", False)
            if key:
                return sorted(data, key=lambda x: x.get(key, 0) if isinstance(x, dict) else x, reverse=reverse)
            return sorted(data, reverse=reverse)
        return data

    async def _op_default(self, data: Any, opts: Dict) -> Any:
        return data
