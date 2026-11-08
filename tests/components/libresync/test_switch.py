"""Tests for the LibreSync switches."""

from unittest.mock import MagicMock, patch

from aiolibresync import NotConnectedError
import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from .conftest import STATE, push


@pytest.fixture(autouse=True)
async def setup(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Set up the integration with the switches alone."""
    with patch("homeassistant.components.libresync.PLATFORMS", [Platform.SWITCH]):
        await setup_integration(hass, mock_config_entry)


async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the switches and their state."""
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize(
    ("entity_id", "method"),
    [
        ("switch.stereo_room_correction", "async_set_room_correction"),
        ("switch.stereo_manual_eq", "async_set_manual_eq"),
    ],
)
@pytest.mark.parametrize(
    ("service", "value"), [(SERVICE_TURN_ON, True), (SERVICE_TURN_OFF, False)]
)
async def test_turn_on_off(
    hass: HomeAssistant,
    mock_client: MagicMock,
    entity_id: str,
    method: str,
    service: str,
    value: bool,
) -> None:
    """Test each switch calls its own setter."""
    await hass.services.async_call(
        SWITCH_DOMAIN, service, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    getattr(mock_client, method).assert_awaited_once_with(value)


async def test_state_follows_the_hub(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test the switches follow pushed state, unknown until reported."""
    push(mock_client, STATE.evolve(room_correction=False, manual_eq=True))
    await hass.async_block_till_done()
    assert hass.states.get("switch.stereo_room_correction").state == STATE_OFF
    assert hass.states.get("switch.stereo_manual_eq").state == STATE_ON

    push(mock_client, STATE.evolve(room_correction=None))
    await hass.async_block_till_done()
    assert hass.states.get("switch.stereo_room_correction").state == STATE_UNKNOWN


async def test_command_error(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test a failed command is reported."""
    mock_client.async_set_room_correction.side_effect = NotConnectedError("down")
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.stereo_room_correction"},
            blocking=True,
        )
    assert err.value.translation_key == "not_connected"
