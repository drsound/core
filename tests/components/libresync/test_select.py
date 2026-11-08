"""Tests for the LibreSync EQ preset select."""

from unittest.mock import MagicMock, patch

from aiolibresync import ConfirmationTimeout
import pytest
from pytest_homeassistant.common import MockConfigEntry, snapshot_platform
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from .conftest import STATE, push

ENTITY_ID = "select.stereo_eq_preset"


@pytest.fixture(autouse=True)
async def setup(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Set up the integration with the select alone."""
    with patch("homeassistant.components.libresync.PLATFORMS", [Platform.SELECT]):
        await setup_integration(hass, mock_config_entry)


async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the select and its state."""
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


async def test_select_preset(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test a preset is selected by its number."""
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_OPTION: "3"},
        blocking=True,
    )
    mock_client.async_select_eq_preset.assert_awaited_once_with(3)


@pytest.mark.parametrize("preset", [None, 0, 7])
async def test_unknown_preset(
    hass: HomeAssistant, mock_client: MagicMock, preset: int | None
) -> None:
    """Test a preset not reported, the app's editor, or out of range, is unknown."""
    push(mock_client, STATE.evolve(eq_preset=preset))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN


async def test_command_error(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Test an unconfirmed selection is reported."""
    mock_client.async_select_eq_preset.side_effect = ConfirmationTimeout("late")
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_OPTION: "1"},
            blocking=True,
        )
    assert err.value.translation_key == "not_confirmed"
