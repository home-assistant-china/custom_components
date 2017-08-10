"""
从文件读取快递单号，通过快递100查询快递路由信息
https://home-assistant.io/components/expreess_check
"""
import os
import asyncio
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
     CONF_NAME)
from homeassistant.helpers.entity import Entity
import requests
import json
_LOGGER = logging.getLogger(__name__)

CONF_FILE_PATH = 'file_path'

DEFAULT_NAME = 'Express_check'

ICON = 'mdi:package-variant-closed'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_FILE_PATH): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,


})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the file sensor."""
    file_path = config.get(CONF_FILE_PATH)
    name = config.get(CONF_NAME)





    async_add_devices(
        [FileSensor(name, file_path)], True)


class FileSensor(Entity):
    """Implementation of a file sensor."""

    def __init__(self, name, file_path):
        """Initialize the file sensor."""
        self._name = name
        self._file_path = file_path
        self.data = None
        self.attributes = {}


        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attributes



    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Get the latest entry from a file and updates the state."""
        try:
            with open(self._file_path, 'r', encoding='utf-8') as file_data:
                expressdata = json.load(file_data)

        except (IndexError, FileNotFoundError, IsADirectoryError,
                UnboundLocalError):
            _LOGGER.warning("File or data not present at the moment: %s",
                            os.path.basename(self._file_path))
            return



        if not 'type' in expressdata:
            _LOGGER.error('No type in express_check.ini')
            return
        expresstype = expressdata['type']
        if not 'postid' in expressdata:
            _LOGGER.error('No postid in express_check.ini')
            return
        expresspostid = expressdata['postid']
        self.attributes = {'快递公司':expresstype,'快递单号':expresspostid}

        resp = requests.get("http://www.kuaidi100.com/query?type=%s&postid=%s" % (expresstype,expresspostid))
        if resp.status_code != 200:
            _LOGGER.error('http get data Error StatusCode:%s' % resp.status_code)
            return
        self.data = resp.json()
        if self.data['message']=='快递公司参数异常：单号不存在或者已经过期':
            _LOGGER.warning('Express company parameter exception: odd number does not exist or has expired')
            self._state = '快递公司参数异常：单号不存在或者已经过期'
            return
        elif self.data['message']=='参数错误':
            _LOGGER.warning('Parameter error')
            self._state = '参数错误'
            return
        elif self.data['message']=='服务器错误':
            _LOGGER.warning('Server error')
            self._state = '服务器错误'
            return
        elif self.data['message']=='ok':
            if not 'data' in self.data:
                _LOGGER.warning('Not data in json!')
                return
            if not 'context' in self.data['data'][0]:
                _LOGGER.warning('Not context in data!')
                return
            self._state = self.data['data'][0]['context']
        else:
            _LOGGER.warning('Unknown error')
            self._state = '未知错误'
