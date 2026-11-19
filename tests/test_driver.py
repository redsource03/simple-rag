"""Tests for simple_rag.graph.driver module.

Covers:
- _get_driver() singleton lifecycle
- _ensure_vector_index() creates chunk_index and entity_index
- Vector index creation uses mocked Neo4j driver (no real DB needed)
"""

from unittest.mock import MagicMock, patch

from simple_rag.config import Neo4jConfig
from simple_rag.graph import driver

# ---------------------------------------------------------------------------
# _get_driver
# ---------------------------------------------------------------------------


class TestGetDriver:
    def setup_method(self) -> None:
        """Reset the singleton before each test."""
        driver._driver = None

    def test_get_driver_returns_singleton(self) -> None:
        """Two calls to _get_driver() return the same driver instance."""
        with patch.object(driver, "Neo4jConfig") as MockConfig:
            mock_config = MagicMock(spec=Neo4jConfig)
            mock_config.uri = "bolt://test:7687"
            mock_config.database = "test"
            mock_config.username = "neo4j"
            mock_config.password = "test"
            mock_config.auth = ("neo4j", "test")
            mock_config.max_connection_lifetime = 3600
            mock_config.max_connection_pool_size = 20
            mock_config.connection_acquisition_timeout = 30
            MockConfig.from_env.return_value = mock_config

            d1 = driver._get_driver()
            d2 = driver._get_driver()
            assert d1 is d2

    def test_get_driver_creates_driver_with_correct_params(self) -> None:
        """First call creates a GraphDatabase driver with config values."""
        with patch.object(driver, "Neo4jConfig") as MockConfig, \
             patch.object(driver, "GraphDatabase") as MockGraphDB:
            mock_config = MagicMock(spec=Neo4jConfig)
            mock_config.uri = "bolt://test:7687"
            mock_config.database = "test"
            mock_config.username = "neo4j"
            mock_config.password = "test"
            mock_config.auth = ("neo4j", "test")
            mock_config.max_connection_lifetime = 7200
            mock_config.max_connection_pool_size = 50
            mock_config.connection_acquisition_timeout = 60
            MockConfig.from_env.return_value = mock_config

            mock_driver = MagicMock()
            MockGraphDB.driver.return_value = mock_driver

            _ = driver._get_driver()

            MockGraphDB.driver.assert_called_once_with(
                "bolt://test:7687",
                auth=("neo4j", "test"),
                max_connection_lifetime=7200,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )

    def test_get_driver_handles_empty_config(self) -> None:
        """Driver is created even with default config values."""
        with patch.object(driver, "Neo4jConfig") as MockConfig, \
             patch.object(driver, "GraphDatabase") as MockGraphDB:
            mock_config = MagicMock(spec=Neo4jConfig)
            mock_config.uri = "bolt://localhost:7687"
            mock_config.database = "neo4j"
            mock_config.username = "neo4j"
            mock_config.password = "password"
            mock_config.auth = ("neo4j", "password")
            mock_config.max_connection_lifetime = 3600
            mock_config.max_connection_pool_size = 20
            mock_config.connection_acquisition_timeout = 30
            MockConfig.from_env.return_value = mock_config

            mock_driver = MagicMock()
            MockGraphDB.driver.return_value = mock_driver

            _ = driver._get_driver()
            assert MockGraphDB.driver.called


# ---------------------------------------------------------------------------
# _ensure_vector_index
# ---------------------------------------------------------------------------


class TestEnsureVectorIndex:
    def test_ensure_vector_index_creates_both_indexes(self) -> None:
        """Both chunk_index and entity_index are created."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        # No existing indexes
        mock_session.run.return_value = []
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        with patch.object(driver, "create_vector_index") as MockCreateIndex:
            driver._ensure_vector_index(mock_driver)

            assert MockCreateIndex.call_count == 2
            calls = MockCreateIndex.call_args_list
            # name is passed positionally (2nd arg), rest are kwargs
            assert calls[0].args[1] == "chunk_index"
            assert calls[0].kwargs["label"] == "Chunk"
            assert calls[0].kwargs["embedding_property"] == "embedding"
            assert calls[0].kwargs["similarity_fn"] == "euclidean"

            assert calls[1].args[1] == "entity_index"
            assert calls[1].kwargs["label"] == "Entity"

    def test_ensure_vector_index_skips_existing_indexes(self) -> None:
        """If indexes already exist, create_vector_index is not called."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        # Simulate SHOW INDEXES returning existing indexes
        mock_session.run.return_value = [MagicMock(), MagicMock()]
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        with patch.object(driver, "create_vector_index") as MockCreateIndex:
            driver._ensure_vector_index(mock_driver)

            MockCreateIndex.assert_not_called()

    def test_ensure_vector_index_handles_exception(self) -> None:
        """Exceptions during index creation don't crash the app."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.run.side_effect = Exception("connection lost")
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        # Should not raise — logs warning instead
        driver._ensure_vector_index(mock_driver)

    def test_ensure_vector_index_uses_provider_config_dimensions(self) -> None:
        """Uses embedding_dimension from ProviderConfig."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        # No existing indexes so it will call create_vector_index
        mock_session.run.return_value = []
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)

        with patch.object(driver, "Neo4jConfig") as MockNeo4jConfig, \
             patch.object(driver, "ProviderConfig") as MockProviderConfig, \
             patch.object(driver, "create_vector_index") as MockCreateIndex:
            mock_neo4j = MagicMock(spec=Neo4jConfig)
            mock_neo4j.database = "test"
            MockNeo4jConfig.from_env.return_value = mock_neo4j

            mock_provider = MagicMock()
            mock_provider.embedding_dimension = 2048
            MockProviderConfig.from_env.return_value = mock_provider

            driver._ensure_vector_index(mock_driver)

            # Called twice (chunk_index + entity_index), both with 2048
            assert MockCreateIndex.call_count == 2
            for call_args in MockCreateIndex.call_args_list:
                assert call_args.kwargs["dimensions"] == 2048
