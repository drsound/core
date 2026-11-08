"""EQ preset select for the LibreSync integration."""

from typing import override

from aiolibresync import DeviceState, LibreSyncClient

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LibreSyncConfigEntry
from .entity import LibreSyncEntity, handle_errors

PARALLEL_UPDATES = 1

# The hub has three presets, built in the vendor's app. It also reports 0, the
# app's editor slot, while the app's EQ editor is open: shown as unknown.
PRESETS = ["1", "2", "3"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LibreSyncConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the EQ preset select."""
    assert entry.unique_id is not None
    async_add_entities(
        [LibreSyncEqPreset(entry.runtime_data, entry.unique_id, entry.title)]
    )


class LibreSyncEqPreset(LibreSyncEntity, SelectEntity):
    """The EQ preset in use."""

    _attr_translation_key = "eq_preset"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, client: LibreSyncClient, unique_id: str, name: str) -> None:
        """Initialize the select."""
        super().__init__(client, unique_id, name)
        self._attr_unique_id = f"{unique_id}_eq_preset"

    _attr_options = PRESETS

    @override
    def _shown(self, state: DeviceState) -> object:
        """Return the preset."""
        return state.eq_preset

    @property
    @override
    def current_option(self) -> str | None:
        """Return the preset in use, None while the app's editor is open."""
        preset = self.snapshot.eq_preset
        if preset is not None and str(preset) in PRESETS:
            return str(preset)
        return None

    @handle_errors
    @override
    async def async_select_option(self, option: str) -> None:
        """Select a preset."""
        await self._client.async_select_eq_preset(int(option))
