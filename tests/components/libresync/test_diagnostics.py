"""Tests for the LibreSync diagnostics."""

from unittest.mock import MagicMock

from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.diagnostics import get_diagnostics_for_config_entry
from pytest_homeassistant.typing import ClientSessionGenerator
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant

from . import setup_integration

# The shape of `LibreSyncClient.diagnostics()`, already redacted by the library.
CLIENT_DIAGNOSTICS = {
    "host": "<redacted>",
    "connected": {"control": True, "media": True},
    "state": {
        "available": True,
        "power": True,
        "volume": 28,
        "serial": "<redacted>",
        "now_playing": {"title": "<redacted>", "app": "TIDAL"},
    },
    "counters": {"control_unknown": 0, "media_unknown": 1},
    "unknown_frames": {"control": [], "media": ["aa55 0001"]},
    "unknown_signatures": {"control": {}, "media": {"aa55": 1}},
}


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the diagnostics hide the address and raw frames, and keep the UDN."""
    mock_client.diagnostics.return_value = CLIENT_DIAGNOSTICS
    await setup_integration(hass, mock_config_entry)

    assert (
        await get_diagnostics_for_config_entry(hass, hass_client, mock_config_entry)
        == snapshot
    )
