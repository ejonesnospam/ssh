"""The ssh integration."""

import logging

import voluptuous as vol

from homeassistant.helpers import discovery
from homeassistant.const import CONF_DEVICE
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ssh"

SSH_PLATFORMS = ["switch", "sensor"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Optional(CONF_DEVICE, default=DEFAULT_DEVICE): cv.string}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up the ssh switch platform."""

    for platform in SSH_PLATFORMS:
        discovery.load_platform(
            hass, platform, DOMAIN, {"device": config[DOMAIN][CONF_DEVICE]}, config
        )

    return True
