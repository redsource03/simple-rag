"""Schema loader for simple_rag.

Loads predefined YAML schemas from ``.agents/schemas/`` and provides discovery
and validation functions used by the MCP tools.

Domain: personal knowledge management — schemas are the user's vocabulary.
Predefined YAML is the source of truth. The LLM (ADK agent) picks the
datasource_id; it never invents schemas.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Default location for predefined schemas
_DEFAULT_SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".agents" / "schemas"

_REQUIRED_KEYS = {"node_types", "relationship_types", "patterns", "description"}


def load_schema(
    datasource_id: Any,
    schemas_dir: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Load a predefined YAML schema by datasource_id.

    Args:
        datasource_id: The identifier for the schema to load.
        schemas_dir: Optional override for the schemas directory.
            Defaults to ``.agents/schemas/`` relative to this package.

    Returns:
        A dict with keys ``node_types``, ``relationship_types``, ``patterns``,
        ``description``, or ``None`` if the schema is not found or invalid.
    """
    if not isinstance(datasource_id, str) or not datasource_id:
        return None

    schemas_dir = Path(schemas_dir or _DEFAULT_SCHEMAS_DIR)
    schema_path = schemas_dir / f"{datasource_id}.yaml"

    if not schema_path.is_file():
        return None

    try:
        with schema_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None

    if not isinstance(data, dict):
        return None

    if not _REQUIRED_KEYS.issubset(data.keys()):
        return None

    result = dict(data)
    result["id"] = datasource_id
    return result


def list_schemas(schemas_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Discover all available predefined schemas.

    Args:
        schemas_dir: Optional override for the schemas directory.

    Returns:
        A list of dicts with ``id``, ``description``, ``node_types``,
        ``relationship_types`` for each valid schema.
    """
    schemas_dir = Path(schemas_dir or _DEFAULT_SCHEMAS_DIR)
    if not schemas_dir.is_dir():
        return []

    schemas: List[Dict[str, Any]] = []
    for path in sorted(schemas_dir.glob("*.yaml")):
        schema = load_schema(path.stem, schemas_dir=str(schemas_dir))
        if schema is not None:
            schemas.append({
                "id": schema["id"],
                "description": schema["description"],
                "node_types": schema["node_types"],
                "relationship_types": schema["relationship_types"],
            })
    return schemas


def build_pipeline_config(
    datasource_id: Any,
    schemas_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a schema dict suitable for ``SimpleKGPipeline(schema=...)``.

    Args:
        datasource_id: The identifier for the schema.
        schemas_dir: Optional override for the schemas directory.

    Returns:
        A dict with ``node_types``, ``relationship_types``, ``patterns``.

    Raises:
        ValueError: If the datasource_id is not found.
    """
    schema = load_schema(datasource_id, schemas_dir=schemas_dir)
    if schema is None:
        raise ValueError(
            f"Schema '{datasource_id}' not found. "
            f"Available schemas: {[s['id'] for s in list_schemas(schemas_dir=schemas_dir)]}"
        )
    return {
        "node_types": schema["node_types"],
        "relationship_types": schema["relationship_types"],
        "patterns": schema["patterns"],
    }
