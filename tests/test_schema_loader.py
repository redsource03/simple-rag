"""Tests for simple_rag.schema_loader module.

Covers:
- load_schema() success / failure / missing datasource
- list_schemas() discovery
- build_pipeline_config() output shape
- Schema loader uses temp directory with test YAML files (no real filesystem dependency)
"""

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from simple_rag import schema_loader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_test_schemas(tmpdir: str) -> str:
    """Write a minimal set of test YAML schemas into *tmpdir* and return the path."""
    schemas_dir = Path(tmpdir) / "schemas"
    schemas_dir.mkdir()

    # tech-architecture schema
    (schemas_dir / "tech-architecture.yaml").write_text(
        yaml.dump(
            {
                "node_types": ["System", "Component", "Interface"],
                "relationship_types": ["DEPENDS_ON", "PROXIES_TO"],
                "patterns": [["System", "DEPENDS_ON", "Component"]],
                "description": "Test tech-architecture schema",
            },
            default_flow_style=False,
        )
    )

    # research-paper schema
    (schemas_dir / "research-paper.yaml").write_text(
        yaml.dump(
            {
                "node_types": ["Paper", "Author"],
                "relationship_types": ["WRITES"],
                "patterns": [["Author", "WRITES", "Paper"]],
                "description": "Test research-paper schema",
            },
            default_flow_style=False,
        )
    )

    return str(schemas_dir)


# ---------------------------------------------------------------------------
# load_schema
# ---------------------------------------------------------------------------


class TestLoadSchema:
    def setup_method(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._schemas_dir = _write_test_schemas(self._tmpdir.name)

    def teardown_method(self) -> None:
        self._tmpdir.cleanup()

    def test_load_schema_success(self) -> None:
        result = schema_loader.load_schema("tech-architecture", schemas_dir=self._schemas_dir)
        assert result is not None
        assert result["node_types"] == ["System", "Component", "Interface"]
        assert result["relationship_types"] == ["DEPENDS_ON", "PROXIES_TO"]
        assert result["patterns"] == [["System", "DEPENDS_ON", "Component"]]
        assert result["description"] == "Test tech-architecture schema"

    def test_load_schema_missing_datasource_id(self) -> None:
        result = schema_loader.load_schema("nonexistent", schemas_dir=self._schemas_dir)
        assert result is None

    def test_load_schema_invalid_datasource_id(self) -> None:
        """Passing an empty or non-string datasource_id returns None."""
        result = schema_loader.load_schema("", schemas_dir=self._schemas_dir)
        assert result is None
        result = schema_loader.load_schema(None, schemas_dir=self._schemas_dir)  # type: ignore[arg-type]
        assert result is None

    def test_load_schema_missing_required_keys(self) -> None:
        """A YAML file with missing required keys returns None."""
        bad_dir = Path(self._schemas_dir) / "bad"
        bad_dir.mkdir()
        (bad_dir / "broken.yaml").write_text("node_types: [X]")  # missing others
        result = schema_loader.load_schema("broken", schemas_dir=str(bad_dir))
        assert result is None

    def test_load_schema_invalid_yaml(self) -> None:
        """Malformed YAML returns None."""
        bad_dir = Path(self._schemas_dir) / "bad"
        bad_dir.mkdir()
        (bad_dir / "invalid.yaml").write_text("::: not valid yaml {{{")
        result = schema_loader.load_schema("invalid", schemas_dir=str(bad_dir))
        assert result is None


# ---------------------------------------------------------------------------
# list_schemas
# ---------------------------------------------------------------------------


class TestListSchemas:
    def setup_method(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._schemas_dir = _write_test_schemas(self._tmpdir.name)

    def teardown_method(self) -> None:
        self._tmpdir.cleanup()

    def test_list_schemas_returns_all(self) -> None:
        schemas = schema_loader.list_schemas(schemas_dir=self._schemas_dir)
        ids = [s["id"] for s in schemas]
        assert "tech-architecture" in ids
        assert "research-paper" in ids
        assert len(schemas) == 2

    def test_list_schemas_empty_dir(self) -> None:
        empty_dir = tempfile.mkdtemp()
        schemas = schema_loader.list_schemas(schemas_dir=empty_dir)
        assert schemas == []

    def test_list_schemas_output_shape(self) -> None:
        schemas = schema_loader.list_schemas(schemas_dir=self._schemas_dir)
        for s in schemas:
            assert "id" in s
            assert "description" in s
            assert "node_types" in s
            assert "relationship_types" in s

    def test_list_schemas_ignores_non_yaml(self) -> None:
        Path(self._schemas_dir).joinpath("readme.txt").write_text("ignored")
        schemas = schema_loader.list_schemas(schemas_dir=self._schemas_dir)
        ids = [s["id"] for s in schemas]
        assert "readme" not in ids


# ---------------------------------------------------------------------------
# build_pipeline_config
# ---------------------------------------------------------------------------


class TestBuildPipelineConfig:
    def setup_method(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._schemas_dir = _write_test_schemas(self._tmpdir.name)

    def teardown_method(self) -> None:
        self._tmpdir.cleanup()

    def test_build_pipeline_config_success(self) -> None:
        config = schema_loader.build_pipeline_config("tech-architecture", schemas_dir=self._schemas_dir)
        assert isinstance(config, dict)
        assert config["node_types"] == ["System", "Component", "Interface"]
        assert config["relationship_types"] == ["DEPENDS_ON", "PROXIES_TO"]
        assert config["patterns"] == [["System", "DEPENDS_ON", "Component"]]

    def test_build_pipeline_config_missing_datasource(self) -> None:
        try:
            schema_loader.build_pipeline_config("nonexistent", schemas_dir=self._schemas_dir)
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "nonexistent" in str(exc)

    def test_build_pipeline_config_output_shape(self) -> None:
        config = schema_loader.build_pipeline_config("tech-architecture", schemas_dir=self._schemas_dir)
        assert set(config.keys()) == {"node_types", "relationship_types", "patterns"}


# ---------------------------------------------------------------------------
# Integration: load_schema vs list_schemas consistency
# ---------------------------------------------------------------------------


class TestIntegration:
    def setup_method(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._schemas_dir = _write_test_schemas(self._tmpdir.name)

    def teardown_method(self) -> None:
        self._tmpdir.cleanup()

    def test_list_schemas_ids_match_load_schema(self) -> None:
        schemas = schema_loader.list_schemas(schemas_dir=self._schemas_dir)
        for s in schemas:
            loaded = schema_loader.load_schema(s["id"], schemas_dir=self._schemas_dir)
            assert loaded is not None
            assert loaded["id"] == s["id"]
