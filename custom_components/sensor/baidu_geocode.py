#! usr/bin/python
#coding=utf-8
"""
Support for baidu travel time sensors.此版本具备跟踪设备并显示到达家所需时间的功能
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.baidu_geocode/
"""
import logging
from homeassistant.const import (
    CONF_API_KEY, CONF_NAME, ATTR_ATTRIBUTION, CONF_ID
    )
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_ENTITY_ID, CONF_STATE, CONF_TYPE,
    EVENT_HOMEASSISTANT_START)
import json
import urllib
import urllib.request
import urllib.parse
_Log=logging.getLogger(__name__)
CONF_ENTITY_ID = 'entity_id'
CONF_ORIGIN_REGION = 'origin_region'
CONF_DESTINATION = 'destination'
CONF_DESTINATION_REGION = 'destination_region'
address = ''
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ENTITY_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_ORIGIN_REGION): cv.string,
    vol.Required(CONF_DESTINATION): cv.string,
    vol.Required(CONF_DESTINATION_REGION): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    entity_id = config.get(CONF_ENTITY_ID)
    sensor_name = config.get(CONF_NAME)
    api_key = config.get(CONF_API_KEY,None)
    destination = config.get(CONF_DESTINATION)
    origin_region = config.get(CONF_ORIGIN_REGION)
    destination_region = config.get(CONF_DESTINATION_REGION)
    if api_key == None:
        _Log.error('Pls enter api_key!')
        return False
    travelsensorname = sensor_name+'_travel_time'

    add_devices([baiduAddressSensor(sensor_name,hass,entity_id,api_key)])
    add_devices([showaddressSensor(sensor_name+'_address')])
    add_devices([baiduTravelSensor(travelsensorname,api_key,destination,origin_region,destination_region)])
class baiduTravelSensor(Entity):
    """Representation of a Sensor."""


    def __init__(self,travelsensorname,api_key,destination,origin_region,destination_region):
        self.attributes = {}
        self._state = None
        self._name = travelsensorname
        self.api_key = api_key
        self.origin_region = origin_region
        self.destination = destination
        self.destination_region = destination_region





    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attributes

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return "min"

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        geocoding = {'mode': 'driving',
                             'origin' : address,
                             'destination' : self.destination,
                             'origin_region': self.origin_region,
                             'destination_region': self.destination_region,
                             'output' : 'json',
                             'ak' : self.api_key,
                             }
        geocoding =  urllib.parse.urlencode(geocoding)
        ret = urllib.request.urlopen("%s?%s" % ("http://api.map.baidu.com/direction/v1", geocoding))
        if ret.status != 200:
            _Log.error('http get data Error StatusCode:%s' % ret.status)
            return
        res = ret.read().decode('utf-8')
        json_obj = json.loads(res)
        if not 'result' in json_obj:
            _Log.error('Json Status Error1!')
            return
        traffic = json_obj['result']['traffic_condition']
        timecost = json_obj['result']['taxi']['duration']
        timecost = str(int(timecost)//60)
        if traffic == 1:
            output = "畅通"
        elif traffic == 2:
            output = "缓行"
        elif traffic == 3:
            output = "拥堵"
        else:
            output = "无路况信息"
        self.attributes ={'路况':output}
        self._state = timecost

class showaddressSensor(Entity):
    def __init__(self,sensor_name):
        self._name = sensor_name
        self._state = None
        self.attributes = {}
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attributes



    def update(self):
        self._state = address
class baiduAddressSensor(Entity):
    """Representation of a Sensor."""


    def __init__(self,hass,sensor_name,entity_id,api_key):
        self.hass = hass
        self.api_key = api_key
        self._state = None
        self._name = sensor_name
        self.entity_id = entity_id
        self.attributes = {}






    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attributes



    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        tracker_state = self.hass.states.get(self.entity_id)
        self.attributes = tracker_state.attributes
        latitude = tracker_state.attributes.get('latitude')
        longitude = tracker_state.attributes.get('longitude')


        coords = str(longitude)+','+str(latitude)
        geocoding = {'coords': coords,
                     'from': '1',
        			 'to' : '5',
        		 	 'ak' : self.api_key,
        					 }

        geocoding =  urllib.parse.urlencode(geocoding)
        ret = urllib.request.urlopen("%s?%s" % ("http://api.map.baidu.com/geoconv/v1/", geocoding))
        if ret.status != 200:
            _Log.error('http get data Error StatusCode:%s' % ret.status)
            return
        res = ret.read().decode('utf-8')

        json_obj = json.loads(res)
        if not 'result' in json_obj:
            _Log.error('Json Status Error1!')
            return

        resultx= json_obj['result'][0]['x']
        resulty= json_obj['result'][0]['y']
        print(resultx,resulty)
        location = str(resulty)+','+str(resultx)
        toaddress = {
                     'location':location,
        			 'output':'json',
        			 'pois':'1',
        			 'ak':self.api_key}

        toaddress = urllib.parse.urlencode(toaddress)

        req = urllib.request.urlopen("%s?%s" % ("http://api.map.baidu.com/geocoder/v2/", toaddress))
        if req.status != 200:
            _Log.error('http get data Error StatusCode:%s' % req.status)
            return

        res2 = req.read().decode('utf-8')
        addjson_obj=json.loads(res2)
        if not 'result' in addjson_obj:
            _Log.error('Json Status Error1!')
            return

        global address

        address = addjson_obj['result']['formatted_address']
        adddict = {'address':address}
        dictMerged2=dict(self.attributes, **adddict)


        self.attributes=dictMerged2
        self._state = tracker_state.state
