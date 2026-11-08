"""Audio binary sensor for the LibreSync integration."""

from typing import override

from aiolibresync import DeviceState, LibreSyncClient, PlayState

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LibreSyncConfigEntry
from .entity import LibreSyncEntity

# Read-only and pushed.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LibreSyncConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the audio binary sensor."""
    assert entry.unique_id is not None
    async_add_entities(
        [LibreSyncAudio(entry.runtime_data, entry.unique_id, entry.title)]
    )


class LibreSyncAudio(LibreSyncEntity, BinarySensorEntity):
    """Whether sound is coming out of the hub, on any source."""

    _attr_translation_key = "audio"
    _attr_device_class = BinarySensorDeviceClass.SOUND
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    # The media player shows the same through its playback state.
    _attr_entity_registry_enabled_default = False

    def __init__(self, client: LibreSyncClient, unique_id: str, name: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(client, unique_id, name)
        self._attr_unique_id = f"{unique_id}_audio"

    @override
    def _shown(self, state: DeviceState) -> object:
        """Return the audio state."""
        return state.audio_state

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the hub reports audio playing; paused is silence."""
        audio = self.snapshot.audio_state
        return audio is PlayState.PLAYING if audio is not None else None
