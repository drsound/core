"""Base entity for the LibreSync integration."""

from collections.abc import Awaitable, Callable, Coroutine
from functools import wraps
from typing import Any, override

from aiolibresync import (
    ConfirmationTimeout,
    DeviceState,
    LibreSyncClient,
    NotConnectedError,
)

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MANUFACTURER


def handle_errors[**P](
    func: Callable[P, Awaitable[None]],
) -> Callable[P, Coroutine[Any, Any, None]]:
    """Turn the library's command failures into translated errors."""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            await func(*args, **kwargs)
        except NotConnectedError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="not_connected"
            ) from err
        except ConfirmationTimeout as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="not_confirmed"
            ) from err

    return wrapper


class LibreSyncEntity(Entity):
    """An entity fed by the client's pushed state."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, client: LibreSyncClient, unique_id: str, name: str) -> None:
        """Initialize the entity."""
        self._client = client
        # Availability and what the entity shows, as last written.
        self._written_shown: tuple[bool, object] | None = None
        # No model here: setup keeps it on the device as it arrives, and a
        # None here would overwrite it.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer=MANUFACTURER,
            name=name,
        )

    @property
    def snapshot(self) -> DeviceState:
        """Return the client's current state."""
        return self._client.state

    @property
    @override
    def available(self) -> bool:
        """Return whether both control ports are connected.

        This is deliberately not the hub's power state: the hub answers on
        both ports while switched off.
        """
        return self.snapshot.available

    def _shown(self, state: DeviceState) -> object:
        """Return what the entity shows of the state.

        The state is written only when this or the availability changes: the
        hub pushes the playback position every second while playing.
        """
        return state

    @override
    async def async_added_to_hass(self) -> None:
        """Subscribe to state pushed by the client."""
        await super().async_added_to_hass()
        self._written_shown = (self.snapshot.available, self._shown(self.snapshot))
        self.async_on_remove(self._client.subscribe(self._handle_state))

    @callback
    def _handle_state(self, state: DeviceState) -> None:
        """Write the new state, if what the entity shows changed."""
        shown = (state.available, self._shown(state))
        if shown == self._written_shown:
            return
        self._written_shown = shown
        self.async_write_ha_state()
