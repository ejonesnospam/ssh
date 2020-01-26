"""
Support for SSH access.

For more details about this platform, please refer to the documentation at
https://github.com/custom-components/switch.ssh
"""

import base64
import paramiko
import logging
import voluptuous as vol
from datetime import timedelta
import json
import asyncio

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_HOST, CONF_USERNAME, CONF_PASSWORD,
    CONF_VALUE_TEMPLATE, CONF_PORT,
    STATE_UNKNOWN, CONF_UNIT_OF_MEASUREMENT)

__version__ = '0.2.2'

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'switch'

DEFAULT_NAME = 'SSH'
DEFAULT_SSH_PORT = 22
DEFAULT_INTERVAL = 30

CONF_KEY = 'key'
CONF_INTERVAL = 'interval'
CONF_COMMAND_ON = 'command_on'
CONF_COMMAND_OFF = 'command_off'
CONF_COMMAND_STATUS = 'command_status'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_KEY): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_SSH_PORT): cv.port,
    vol.Required(CONF_COMMAND_ON): cv.string,
    vol.Required(CONF_COMMAND_OFF): cv.string,
    vol.Required(CONF_COMMAND_STATUS): cv.string,
    vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
})

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    dev = []
    dev.append(SSHSwitch(hass, config))
    async_add_devices(dev, True)


class SSHSwitch(Entity):

    def __init__(self, hass, config):
        """Initialize the scanner."""
        self._name = config.get(CONF_NAME)
        self._host = config.get(CONF_HOST)
        self._username = config.get(CONF_USERNAME)
        self._password = config.get(CONF_PASSWORD)
        self._key = config.get(CONF_KEY)
        self._interval = config.get(CONF_INTERVAL)
        self._port = config.get(CONF_PORT)
        self._command_on = config.get(CONF_COMMAND_ON)
        self._command_off = config.get(CONF_COMMAND_OFF)
        self._command_status = config.get(CONF_COMMAND_STATUS)
        self._value_template = config.get(CONF_VALUE_TEMPLATE)
        self._ssh = None
        self._state = None
        self._connected = False
        self._attributes = {}

        if self._value_template is not None:
            self._value_template.hass = hass

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:folder-key-network'

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state == "on"

    @property
    def state_attributes(self):
        """Return the device state attributes."""
        return self._attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, **kwargs):
        from paramiko import ssh_exception

        try:
            if not self._connected:
                self._connect()
            """Exit if still not connected by now."""
            if not self._connected:
                return None
            stdin, stdout, stderr = self._ssh.exec_command(self._command_status)
            value = ""
            for line in stdout:
                value = line.strip('\n')

            if self._value_template is not None:
                self._state = self._value_template.render_with_possible_json_value(
                    value, STATE_UNKNOWN)
            else:
                self._state = value

            _LOGGER.debug(self._state)

        except Exception as err:
            _LOGGER.error("Update error: %s", str(err))
            self._disconnect()

    async def async_turn_on(self, **kwargs):
        """Instruct the switch to turn on."""
        self._state = "on"
        self._execute(self._command_on)

    async def async_turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        self._state = "off"
        self._execute(self._command_off)

    def _execute(self, command):
        """Execute remote command."""
        from paramiko import ssh_exception
        cmd = command.strip('\n')

        try:
            if not self._connected:
                self._connect()
            """Exit if still not connected by now."""
            if not self._connected:
                _LOGGER.error("Unable to establish connection.")
                return None

            """
            Option 1: 
            """
            stdin, stdout, stderr = self._ssh.exec_command(cmd)


            """
            Option 2:
            chan = self._ssh.invoke_shell()
            stdin = chan.makefile('wb')
            stdout = chan.makefile('r')
            stdin.write(cmd + '\n')
            chan.close()
            """

            for line in stdout:
               _LOGGER.debug("Raw Line Response: %s", str(line))

            """Ignore any response"""
            return None

        except Exception as err:
            _LOGGER.error("Unexpected SSH error: %s", str(err))
            self._disconnect()

    def _connect(self):
        """Connect to the SSH server."""
        from paramiko import RSAKey, SSHClient, ssh_exception
        from base64 import b64decode

        try:

            key = paramiko.RSAKey(data=base64.b64decode(self._key))
            client = paramiko.SSHClient()
            client.get_host_keys().add(self._host, 'ssh-rsa', key)
            client.connect(self._host, username=self._username, password=self._password)
            self._ssh = client
            self._connected = True

        except ssh_exception.BadHostKeyException as err:
            _LOGGER.error("Host Key Mismatch: %s", str(err))
            self._disconnect()

        except:
            _LOGGER.error("Connection refused. SSH enabled?")
            self._disconnect()

    def _disconnect(self):
        """Disconnect the current SSH connection."""
        try:
            self._ssh.close()
        except Exception:
            pass
        finally:
            self._ssh = None

        self._connected = False

