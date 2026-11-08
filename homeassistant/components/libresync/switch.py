"""Switches for the LibreSync integration."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, override

from aiolibresync import DeviceState, LibreSyncClient

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LibreSyncConfigEntry
from .entity import LibreSyncEntity, handle_errors

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class LibreSyncSwitchEntityDescription(SwitchEntityDescription):
    """Describes a LibreSync switch."""

    value_fn: Callable[[DeviceState], bool | None]
    set_fn: Callable[[LibreSyncClient, bool], Awaitable[None]]


SWITCHES: tuple[LibreSyncSwitchEntityDescription, ...] = (
    LibreSyncSwitchEntityDescription(
        key="room_correction",
        translation_key="room_correction",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: state.room_correction,
        set_fn=lambda client, on: client.async_set_room_correction(on),
    ),
    # Independent of room correction: both can be on at once.
    LibreSyncSwitchEntityDescription(
        key="manual_eq",
        translation_key="manual_eq",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda state: state.manual_eq,
        set_fn=lambda client, on: client.async_set_manual_eq(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LibreSyncConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switches."""
    assert entry.unique_id is not None
    async_add_entities(
        LibreSyncSwitch(entry.runtime_data, entry.unique_id, entry.title, description)
        for description in SWITCHES
    )


class LibreSyncSwitch(LibreSyncEntity, SwitchEntity):
    """A setting of the hub that is on or off."""

    entity_description: LibreSyncSwitchEntityDescription

    def __init__(
        self,
        client: LibreSyncClient,
        unique_id: str,
        name: str,
        description: LibreSyncSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(client, unique_id, name)
        self.entity_description = description
        self._attr_unique_id = f"{unique_id}_{description.key}"

    @override
    def _shown(self, state: DeviceState) -> object:
        """Return the setting."""
        return self.entity_description.value_fn(state)

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state, None until the hub has reported it."""
        return self.entity_description.value_fn(self.snapshot)

    @handle_errors
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the setting on."""
        await self.entity_description.set_fn(self._client, True)

    @handle_errors
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the setting off."""
        await self.entity_description.set_fn(self._client, False)
