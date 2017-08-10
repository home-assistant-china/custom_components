"""
weChat notification service.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/wechat/
"""
import logging
from homeassistant.const import (
    EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP)
REQUIREMENTS = ['wxpy==0.3.9.8','pillow']
import xml.etree.ElementTree as ET

import requests
import voluptuous as vol

from homeassistant.components.notify import (
    ATTR_TARGET,ATTR_DATA,ATTR_TITLE, ATTR_TITLE_DEFAULT, PLATFORM_SCHEMA, BaseNotificationService)

import homeassistant.helpers.config_validation as cv

from wxpy import *
_Log=logging.getLogger(__name__)
ATTR_IMAGE = "image"
ATTR_FILE = "file"
ATTR_VIDEO = "video"




def get_service(hass, config, discovery_info=None):
    """Get the weChat notification service."""

    bot = Bot(cache_path='/home/homeassistant/.homeassistant/wxpy.pkl',console_qr=True)

    # 机器人账号自身
    myself = bot.self

    # 向文件传输助手发送消息
    _LOGGER = logging.getLogger(__name__)


    return weChatService(bot)





class weChatService(BaseNotificationService):
    """Implement the notification service for weChat."""

    def __init__(self,bot):
        """Initialize the service."""
        self.bot = bot



    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        _Log.info("At least 1 target is required")

        data = kwargs.get(ATTR_DATA)
        targets = kwargs.get(ATTR_TARGET)
        if not targets:
            if not data:
                self.bot.file_helper.send(message)

            elif 'image' in data:
                image = data.get(ATTR_IMAGE,None)
                self.bot.file_helper.send_image(image)
            elif 'file' in data:
                file = data.get(ATTR_FILE,None)
                self.bot.file_helper.send_file(file)
            elif 'video' in data:
                video = data.get(ATTR_VIDEO,None)
                self.bot.file_helper.send_video(video)

            else:
                _Log.error('No message or No data!!')

                return
        else:
            for target in targets:
                try:
                    friend = self.bot.friends().search(target)[0]
                    if not data:
                        friend.send(message)
                    elif 'image' in data:
                        image = data.get(ATTR_IMAGE,None)
                        friend.send_image(image)
                    elif 'file' in data:
                        file = data.get(ATTR_FILE,None)
                        friend.send_file(file)
                    elif 'video' in data:
                        video = data.get(ATTR_VIDEO,None)
                        friend.send_video(video)
                    else:
                        _Log.error('No message or No data!!')

                except:
                    _Log.error('No message or No data or Target error!')
