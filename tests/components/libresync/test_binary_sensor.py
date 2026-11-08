"""Tests for the LibreSync audio binary sensor."""

from unittest.mock import MagicMock, patch

from aiolibresync import PlayState
import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from .conftest import STATE, push

ENTITY_ID = "binary_sensor.stereo_audio"


@pytest.fixture(autouse=True)
async def setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    entity_registry_enabled_by_default: None,
) -> None:
    """Set up the integration with the binary sensor alone, enabled."""
    with patch(
        "homeassistant.components.libresync.PLATFORMS", [Platform.BINARY_SENSOR]
    ):
        await setup_integration(hass, mock_config_entry)


async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the binary sensor and its state."""
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize(
    ("audio_state", "expected"),
    [
        (PlayState.PLAYING, STATE_ON),
        (PlayState.PAUSED, STATE_OFF),
        (PlayState.LOADING, STATE_OFF),
        (PlayState.IDLE, STATE_OFF),
        (None, STATE_UNKNOWN),
    ],
)
async def test_state(
    hass: HomeAssistant,
    mock_client: MagicMock,
    audio_state: PlayState | None,
    expected: str,
) -> None:
    """Test only playing counts as sound."""
    push(mock_client, STATE.evolve(audio_state=audio_state))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == expected


async def test_written_only_on_change(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test a push that changes only what the sensor does not show is not written."""
    written = hass.states.get(ENTITY_ID).last_reported
    push(mock_client, STATE.evolve(position_ms=12000))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).last_reported == written

    push(mock_client, STATE.evolve(available=False))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "unavailable"
