"""Diagnostics support for the LibreSync integration."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from . import LibreSyncConfigEntry

TO_REDACT = {CONF_HOST}
# Raw frames the library could not decode: they may carry anything the
# firmware sends. Their counts and signatures stay.
TO_REDACT_CLIENT = {"unknown_frames"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: LibreSyncConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    The library redacts the host, the module's factory code and the track
    metadata from its own part. The UDN stays: it is a UUID the hub generates,
    not a serial, and it tells two hubs in one report apart.
    """
    return {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "unique_id": entry.unique_id,
        },
        "client": async_redact_data(entry.runtime_data.diagnostics(), TO_REDACT_CLIENT),
    }
