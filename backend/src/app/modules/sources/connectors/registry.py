"""Connector registry for source kinds."""

from src.app.modules.sources.protocols import SourceConnector


class SourceConnectorRegistry:
    """Registry for mapping source kinds to connectors."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._connectors: dict[str, SourceConnector] = {}

    def register(self, kind: str, connector: SourceConnector) -> None:
        """Register a connector for a source kind.

        Args:
            kind: Source kind identifier (e.g., 'csv', 'xlsx').
            connector: Connector instance implementing SourceConnector protocol.

        Raises:
            ValueError: If kind is already registered.
        """
        if kind in self._connectors:
            raise ValueError(f"Connector for kind '{kind}' is already registered")
        self._connectors[kind] = connector

    def get(self, kind: str) -> SourceConnector:
        """Get connector for a source kind.

        Args:
            kind: Source kind identifier.

        Returns:
            SourceConnector: The registered connector.

        Raises:
            ValueError: If kind is not registered.
        """
        if kind not in self._connectors:
            raise ValueError(
                f"Unknown source kind: '{kind}'. "
                f"Registered kinds: {', '.join(sorted(self._connectors.keys()))}"
            )
        return self._connectors[kind]

    def list_kinds(self) -> list[str]:
        """List all registered source kinds.

        Returns:
            list[str]: Sorted list of registered kind identifiers.
        """
        return sorted(self._connectors.keys())

    def all(self) -> dict[str, SourceConnector]:
        """Get all registered connectors.

        Returns:
            dict[str, SourceConnector]: Mapping of kind to connector.
        """
        return dict(self._connectors)
