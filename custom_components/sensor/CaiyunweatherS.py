import logging
from homeassistant.const import (
     CONF_NAME, ATTR_ATTRIBUTION, CONF_ID
    )
import voluptuous as vol
from datetime import timedelta
from homeassistant.const import (
    CONF_NAME, CONF_MONITORED_CONDITIONS, ATTR_ATTRIBUTION,)
from homeassistant.const import TEMP_CELSIUS ,CONF_LATITUDE, CONF_LONGITUDE,CONF_API_KEY
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS)
import requests
import os
import json
import time
_Log=logging.getLogger(__name__)

ATTR_FORECASTPATH = 'forecastpath'
ATTR_REALTIMEPATH = 'realtimepath'
CONF_REALTIME = 'realtime'
CONF_PRECIPITATION = 'precipitation'
CONF_HOURLY = 'hourly'
CONF_MINUTELY = 'minutely'
CONF_DAILY = 'daily'
CONF_DAY = 'day'

REALTIME_TYPES = {
    'temperature': ['temperature', '°C','mdi:thermometer'],
    'skycon': ['skycon', None,None],
    'cloudrate': ['cloudrate', '%','mdi:weather-partlycloudy'],
    'aqi': ['AQI', None,'mdi:cloud-outline'],
    'humidity': ['humidity', '%','mdi:water-percent'],
    'pm25': ['pm25', 'μg/m3','mdi:blur'],

}
PRECIPITATION_TYPE = {
    'nearest_precipitation_distance': ['distance', 'km','mdi:near-me'],
    'nearest_precipitation_intensity': ['intensity','mm','mdi:weather-pouring'],
    'local_precipitation_intensity': ['intensity','mm','mdi:weather-pouring'],
    'local_datasource': ['datasource',None,'mdi:database'],
    'wind_direction': ['direction','°','mdi:compass'],
    'wind_speed': ['speed','Km/h','mdi:weather-windy'],
}
HOURLY_TYPE = {
    'skycon': ['skycon', None,None],
    'cloudrate': ['cloudrate', '%','mdi:weather-partlycloudy'],
    'aqi': ['AQI', None,'mdi:cloud-outline'],
    'humidity': ['humidity', '%','mdi:water-percent'],
    'pm25': ['pm25', 'μg/m3','mdi:blur'],
    'precipitation': ['precipitation', 'mm','mdi:weather-rainy'],
    'wind': ['speed','Km/h','mdi:weather-windy'],
    'temperature': ['temperature', '°C','mdi:thermometer'],
}
MINUTELY_TYPE = {
    'description':['description', None,'mdi:cloud-print-outline'],
    'probability_0':['probability' ,'%','mdi:weather-pouring'],
    'probability_1':['probability' ,'%','mdi:weather-pouring'],
    'probability_2':['probability' ,'%','mdi:weather-pouring'],
    'probability_3':['probability' ,'%','mdi:weather-pouring'],
    'precipitation_2h':['precipitation_2h' ,'mm','mdi:weather-rainy'],
    'precipitation':['precipitation' ,'mm','mdi:weather-rainy'],
}

DAILY_TYPE = {
    'coldRisk': ['desc',None,'mdi:hospital'],
    'temperature_max' :['max','°C','mdi:thermometer'],
    'temperature_avg': ['avg','°C','mdi:thermometer'],
    'temperature_min': ['min','°C','mdi:thermometer'],
    'skycon': ['skycon', None,None],
    'cloudrate_max': ['max', '%','mdi:weather-partlycloudy'],
    'cloudrate_avg': ['avg', '%','mdi:weather-partlycloudy'],
    'cloudrate_min': ['min', '%','mdi:weather-partlycloudy'],
    'aqi_max': ['max', None,'mdi:cloud-outline'],
    'aqi_avg': ['avg', None,'mdi:cloud-outline'],
    'aqi_min': ['min', None,'mdi:cloud-outline'],
    'humidity_max': ['max', '%','mdi:water-percent'],
    'humidity_avg': ['avg', '%','mdi:water-percent'],
    'humidity_min': ['min', '%','mdi:water-percent'],
    'sunset':['sunset',None,'mdi:weather-sunset-down'],
    'sunrise':['sunrise',None,'mdi:weather-sunset-up'],
    'ultraviolet':['ultraviolet',None,'mdi:umbrella'],
    'pm25_max': ['max', 'μg/m3','mdi:blur'],
    'pm25_avg': ['avg', 'μg/m3','mdi:blur'],
    'pm25_min': ['min', 'μg/m3','mdi:blur'],
    'dressing':['desc',None,'mdi:tshirt-crew'],
    'carWashing':['carWashing',None,'mdi:car'],
    'precipitation_max' : ['max','mm','mdi:weather-rainy'],
    'precipitation_avg': ['avg','mm','mdi:weather-rainy'],
    'precipitation_min': ['min','mm','mdi:weather-rainy'],

}
DAY_TYPE = {
    'day1':['day1','unit','icon'],
    'day2':['day2','unit','icon'],
    'day3':['day3','unit','icon'],
    'day4':['day4','unit','icon'],
}

MODULE_SCHEMA = vol.Schema({
    vol.Required(CONF_REALTIME,default=[]):vol.All(cv.ensure_list,[vol.In(REALTIME_TYPES)]),
    vol.Required(CONF_PRECIPITATION,default=[]):vol.All(cv.ensure_list,[vol.In(PRECIPITATION_TYPE)]),
    vol.Required(CONF_HOURLY,default=[]):vol.All(cv.ensure_list,[vol.In(HOURLY_TYPE)]),
    vol.Required(CONF_MINUTELY,default=[]):vol.All(cv.ensure_list,[vol.In(MINUTELY_TYPE)]),
    vol.Required(CONF_DAILY,default=[]):vol.All(cv.ensure_list,[vol.In(DAILY_TYPE)]),
    vol.Required(CONF_DAY,default=[]):vol.All(cv.ensure_list,[vol.In(DAY_TYPE)]),
    vol.Required(ATTR_REALTIMEPATH): cv.string,
    vol.Required(ATTR_FORECASTPATH): cv.string,
})
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_MONITORED_CONDITIONS): MODULE_SCHEMA,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    sensor_name = config.get(CONF_NAME)
    monitored_conditions = config[CONF_MONITORED_CONDITIONS]
    if ATTR_FORECASTPATH in monitored_conditions:
        forecast_path = monitored_conditions['forecastpath']
    else:
        _Log.error('No forecast_path')
        return
    if ATTR_REALTIMEPATH in monitored_conditions:
        realtime_path = monitored_conditions['realtimepath']
    else:
        _Log.error('No realtime_path')
        return



    dev = []
    if  CONF_REALTIME in monitored_conditions:
        realtimeSensor = monitored_conditions['realtime']
        if isinstance(realtimeSensor, list):
            if len(realtimeSensor) == 0:
                sensor_name = REALTIME_TYPES['temperature'][0]
                measurement =  REALTIME_TYPES['temperature'][1]
                icon = REALTIME_TYPES['temperature'][2]
                dev.append(CaiyunSensor(CONF_REALTIME, 'temperature', sensor_name,measurement,icon,forecast_path,realtime_path))
            for sensor in realtimeSensor:
                sensor_name = REALTIME_TYPES[sensor][0]
                measurement = REALTIME_TYPES[sensor][1]
                icon = REALTIME_TYPES[sensor][2]
                dev.append(CaiyunSensor(CONF_REALTIME, sensor, sensor_name,measurement,icon,forecast_path,realtime_path))
    if  CONF_PRECIPITATION in monitored_conditions:
        precipitationSensor = monitored_conditions['precipitation']
        if isinstance(precipitationSensor, list):
            if len(precipitationSensor) == 0:
                sensor_name = PRECIPITATION_TYPE['nearest_precipitation_distance'][0]
                measurement =  PRECIPITATION_TYPE['nearest_precipitation_distance'][1]
                icon =  PRECIPITATION_TYPE['nearest_precipitation_distance'][2]
                dev.append(CaiyunSensor(CONF_PRECIPITATION, 'nearest_precipitation_distance', sensor_name,measurement,icon,forecast_path,realtime_path))
            for sensor in precipitationSensor:
                sensor_name = PRECIPITATION_TYPE[sensor][0]
                measurement = PRECIPITATION_TYPE[sensor][1]
                icon =  PRECIPITATION_TYPE[sensor][2]
                dev.append(CaiyunSensor(CONF_PRECIPITATION, sensor, sensor_name,measurement,icon,forecast_path,realtime_path))

    if  CONF_HOURLY in monitored_conditions:
        hourlySensor = monitored_conditions['hourly']
        if isinstance(hourlySensor, list):
            if len(hourlySensor) == 0:
                sensor_name = HOURLY_TYPE['description'][0]
                measurement =  HOURLY_TYPE['description'][1]
                icon =  HOURLY_TYPE['description'][2]
                dev.append(CaiyunSensor(CONF_HOURLY, 'description', sensor_name,measurement,icon,forecast_path,realtime_path))
            for sensor in hourlySensor:
                sensor_name = HOURLY_TYPE[sensor][0]
                measurement = HOURLY_TYPE[sensor][1]
                icon =  HOURLY_TYPE[sensor][2]
                dev.append(CaiyunSensor(CONF_HOURLY, sensor, sensor_name,measurement,icon,forecast_path,realtime_path))
    if  CONF_MINUTELY in monitored_conditions:
        minutelySensor = monitored_conditions['minutely']
        if isinstance(minutelySensor, list):
            if len(minutelySensor) == 0:
                sensor_name = MINUTELY_TYPE['description'][0]
                measurement =  MINUTELY_TYPE['description'][1]
                icon =  MINUTELY_TYPE['description'][2]
                dev.append(CaiyunSensor(CONF_MINUTELY, 'description', sensor_name,measurement,icon,forecast_path,realtime_path))
            for sensor in minutelySensor:
                sensor_name = MINUTELY_TYPE[sensor][0]
                if sensor_name == 'precipitation_2h':
                    for i in range(0, 120):
                        sensor_name = MINUTELY_TYPE['precipitation_2h'][0]+'_'+str(i)
                        measurement =  MINUTELY_TYPE['precipitation_2h'][1]
                        icon =  MINUTELY_TYPE['precipitation_2h'][2]
                        dev.append(CaiyunSensor(CONF_MINUTELY, 'precipitation_2h'+'_'+str(i), sensor_name,measurement,icon,forecast_path,realtime_path))
                elif sensor_name == 'precipitation':
                    for i in range(0, 60):
                        sensor_name = MINUTELY_TYPE['precipitation'][0]+'_'+str(i)
                        measurement =  MINUTELY_TYPE['precipitation'][1]
                        icon =  MINUTELY_TYPE['precipitation'][2]
                        dev.append(CaiyunSensor(CONF_MINUTELY, 'precipitation'+'_'+str(i), sensor_name,measurement,icon,forecast_path,realtime_path))
                else:
                    measurement = MINUTELY_TYPE[sensor][1]
                    icon =  MINUTELY_TYPE[sensor][2]
                    dev.append(CaiyunSensor(CONF_MINUTELY, sensor, sensor_name,measurement,icon,forecast_path,realtime_path))

    if  CONF_DAILY in monitored_conditions:
        dailySensor = monitored_conditions['daily']
        if isinstance(dailySensor, list):
            if len(dailySensor) == 0:
                sensor_name = DAILY_TYPE['coldRisk'][0]
                measurement =  DAILY_TYPE['coldRisk'][1]
                icon =  DAILY_TYPE['coldRisk'][2]
                dev.append(CaiyunSensor(CONF_DAILY, 'coldRisk', sensor_name,measurement,icon,forecast_path,realtime_path))
            for sensor in dailySensor:
                sensor_name = DAILY_TYPE[sensor][0]
                measurement = DAILY_TYPE[sensor][1]
                icon = DAILY_TYPE[sensor][2]
                dev.append(CaiyunSensor(CONF_DAILY, sensor, sensor_name,measurement,icon,forecast_path,realtime_path))
    if  CONF_DAY in monitored_conditions:
        daySensor = monitored_conditions['day']
        if isinstance(daySensor, list):
            if len(daySensor) == 0:
                for sensor in dailySensor:
                    sensor_name = DAY_TYPE['day1'][0]+DAILY_TYPE[sensor][0]
                    measurement = DAY_TYPE['day1'][0]+DAILY_TYPE[sensor][1]
                    icon = DAY_TYPE[daySensor][0]+DAILY_TYPE[sensor][2]
                    dev.append(CaiyunSensor( DAY_TYPE['day1'][0], sensor, sensor_name,measurement,icon,forecast_path,realtime_path))
            for day in daySensor:
                for sensor in dailySensor:
                    sensor_name = DAY_TYPE[day][0]+DAILY_TYPE[sensor][0]
                    measurement = DAILY_TYPE[sensor][1]
                    icon = DAILY_TYPE[sensor][2]
                    dev.append(CaiyunSensor(DAY_TYPE[day][0], sensor, sensor_name,measurement,icon,forecast_path,realtime_path))
    dev.append(CaiyunSensor('realtime_update', 'realtime_update', 'realtime_update_time',None,'mdi:clock',forecast_path,realtime_path))
    dev.append(CaiyunSensor('forecast_update', 'forecast_update', 'forecast_update_time',None,'mdi:clock',forecast_path,realtime_path))
    add_devices(dev,True)

class CaiyunSensor(Entity):
    """Representation of a Sensor."""


    def __init__(self,sensor_Type,sensor,sensor_name,measurement,icon,forecast_path,realtime_path):

        self._sensor_Type = sensor_Type


        self._sensor = sensor
        self.attributes = {}

        self._state = None
        self._name = sensor_name
        self.data = None
        self.measurement = measurement
        self.forecast_path = forecast_path
        self.realtime_path = realtime_path

        self._icon = icon


    @property
    def name(self):
        """Return the name of the sensor."""
        return 'CaiYun' + '_'  + self._sensor_Type + '_' + self._sensor

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon


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
        return self.measurement

    def get_daily(self,num):
        if self._sensor ==  'coldRisk':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['coldRisk'][num]['desc']
        if self._sensor ==  'temperature_max':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['temperature'][num]['max']
        if self._sensor ==  'temperature_avg':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['temperature'][num]['avg']
        if self._sensor ==  'temperature_min':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['temperature'][num]['min']
        if self._sensor ==  'skycon':
            self.data_forecast = self.data_forecast['result']['daily']
            if self.data_forecast ['skycon'][num]['value'] == 'CLEAR_DAY':
                self._state = '晴天'
            elif self.data_forecast ['skycon'][num]['value'] == 'CLEAR_NIGHT':
                self._state = '晴夜'
            elif self.data_forecast ['skycon'][num]['value'] == 'PARTLY_CLOUDY_DAY':
                self._state = '多云'
            elif self.data_forecast ['skycon'][num]['value'] == 'PARTLY_CLOUDY_NIGHT':
                self._state = '多云'
            elif self.data_forecast ['skycon'][num]['value'] == 'CLOUDY':
                self._state = '阴'
            elif self.data_forecast ['skycon'][num]['value'] == 'RAIN':
                self._state = '雨'
            elif self.data_forecast ['skycon'][num]['value'] == 'SNOW':
                self._state = '雪'
            elif self.data_forecast ['skycon'][num]['value'] == 'WIND':
                self._state = '风'
            elif self.data_forecast ['skycon'][num]['value'] == 'FOG':
                self._state = '雾'
            else:
                self._state = '无数据'
        if self._sensor ==  'cloudrate_max':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = int(self.data_forecast ['cloudrate'][num]['max']*100)
        if self._sensor ==  'cloudrate_avg':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = int(self.data_forecast ['cloudrate'][num]['avg']*100)
        if self._sensor ==  'cloudrate_min':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = int(self.data_forecast ['cloudrate'][num]['min'])*100
        if self._sensor ==  'aqi_max':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['aqi'][num]['max']
        if self._sensor ==  'aqi_avg':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['aqi'][num]['avg']
        if self._sensor ==  'aqi_min':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['aqi'][num]['min']
        if self._sensor ==  'humidity_max':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = int(self.data_forecast ['humidity'][num]['max']*100)
        if self._sensor ==  'humidity_avg':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = int(self.data_forecast ['humidity'][num]['avg']*100)
        if self._sensor ==  'humidity_min':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = int(self.data_forecast ['humidity'][num]['min']*100)
        if self._sensor ==  'sunset':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['astro'][num]['sunset']['time']
        if self._sensor ==  'sunrise':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['astro'][num]['sunrise']['time']
        if self._sensor ==  'ultraviolet':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['ultraviolet'][num]['desc']
        if self._sensor ==  'pm25_max':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['pm25'][num]['max']
        if self._sensor ==  'pm25_avg':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['pm25'][num]['avg']
        if self._sensor ==  'pm25_min':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['pm25'][num]['min']
        if self._sensor ==  'dressing':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['dressing'][num]['desc']
        if self._sensor ==  'carWashing':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['carWashing'][num]['desc']
        if self._sensor ==  'precipitation_max':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['precipitation'][num]['max']
        if self._sensor ==  'precipitation_avg':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['precipitation'][num]['avg']
        if self._sensor ==  'precipitation_min':
            self.data_forecast = self.data_forecast['result']['daily']
            self._state = self.data_forecast ['precipitation'][num]['min']



    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        realtime_file_path = self.realtime_path
        try:
            with open(realtime_file_path, 'r', encoding='utf-8') as file_data:
                realtime_data = json.load(file_data)

        except (IndexError, FileNotFoundError, IsADirectoryError,
                UnboundLocalError):
            _Log.warning("File or data not present at the moment: %s",
                            os.path.basename(realtime_file_path))
            return

        self.data_currently = realtime_data
        if self._sensor_Type == 'realtime_update':
            realupdate_time = time.localtime(self.data_currently['server_time'])
            self._state = time.strftime('%Y-%m-%d %H:%M:%S',realupdate_time)
        if not 'result' in self.data_currently:
            _Log.error('Json Status Error1!')
            return
        if self._sensor_Type == CONF_REALTIME:
            if self._sensor ==  'skycon':
                self.data_currently = self.data_currently['result']
                if self.data_currently ['skycon'] == 'CLEAR_DAY':
                    self._state = '晴天'
                elif self.data_currently ['skycon'] == 'CLEAR_NIGHT':
                    self._state = '晴夜'
                elif self.data_currently ['skycon'] == 'PARTLY_CLOUDY_DAY':
                    self._state = '多云'
                elif self.data_currently ['skycon'] == 'PARTLY_CLOUDY_NIGHT':
                    self._state = '多云'
                elif self.data_currently ['skycon'] == 'CLOUDY':
                    self._state = '阴'
                elif self.data_currently ['skycon'] == 'RAIN':
                    self._state = '雨'
                elif self.data_currently ['skycon'] == 'SNOW':
                    self._state = '雪'
                elif self.data_currently ['skycon'] == 'WIND':
                    self._state = '风'
                elif self.data_currently ['skycon'] == 'FOG':
                    self._state = '雾'
                else:
                    self._state = '无数据'
            elif self._sensor == 'cloudrate':
                self._state = self.data_currently['result']['cloudrate']*100
            elif self._sensor == 'humidity':
                self._state = self.data_currently['result']['humidity']*100
            else:
                self.data_currently = self.data_currently['result']
                self._state = self.data_currently [self._sensor]

        if self._sensor_Type == CONF_PRECIPITATION:
            if self._sensor ==  'nearest_precipitation_distance':
                self.data_currently = self.data_currently['result']['precipitation']['nearest']
                self._state = self.data_currently ['distance']
            if self._sensor ==  'nearest_precipitation_intensity':
                self.data_currently = self.data_currently['result']['precipitation']['nearest']
                self._state = self.data_currently ['intensity']
            if self._sensor ==  'local_precipitation_intensity':
                self.data_currently = self.data_currently['result']['precipitation']['local']
                self._state = self.data_currently ['intensity']
            if self._sensor ==  'local_datasource':
                self.data_currently = self.data_currently['result']['precipitation']['local']
                self._state = self.data_currently ['datasource']
            if self._sensor ==  'wind_direction':
                self.data_currently = self.data_currently['result']['wind']
                self._state = self.data_currently ['direction']
            if self._sensor ==  'wind_speed':
                self.data_currently = self.data_currently['result']['wind']
                self._state = self.data_currently ['speed']
        forecast_file_path = self.forecast_path
        try:
            with open(forecast_file_path, 'r', encoding='utf-8') as file_data:
                forecast_data = json.load(file_data)

        except (IndexError, FileNotFoundError, IsADirectoryError,
                UnboundLocalError):
            _Log.warning("File or data not present at the moment: %s",
                            os.path.basename(forecast_file_path))
            return


        self.data_forecast = forecast_data
        if not 'result' in self.data_forecast:
            _Log.error('Json Status Error1!')
            return
        if self._sensor_Type == 'forecast_update':
            self._state = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.data_forecast['server_time']))
        if self._sensor_Type == CONF_HOURLY:
            if self._sensor ==  'description':
                self.data_forecast = self.data_forecast['result']['hourly']
                self._state = self.data_forecast ['description']
            if self._sensor ==  'skycon':
                self.data_forecast = self.data_forecast['result']['hourly']
                if self.data_forecast ['skycon'][0]['value'] == 'CLEAR_DAY':
                    self._state = '晴天'
                elif self.data_forecast ['skycon'][0]['value'] == 'CLEAR_NIGHT':
                    self._state = '晴夜'
                elif self.data_forecast ['skycon'][0]['value'] == 'PARTLY_CLOUDY_DAY':
                    self._state = '多云'
                elif self.data_forecast ['skycon'][0]['value'] == 'PARTLY_CLOUDY_NIGHT':
                    self._state = '多云'
                elif self.data_forecast ['skycon'][0]['value'] == 'CLOUDY':
                    self._state = '阴'
                elif self.data_forecast ['skycon'][0]['value'] == 'RAIN':
                    self._state = '雨'
                elif self.data_forecast ['skycon'][0]['value'] == 'SNOW':
                    self._state = '雪'
                elif self.data_forecast ['skycon'][0]['value'] == 'WIND':
                    self._state = '风'
                elif self.data_forecast ['skycon'][0]['value'] == 'FOG':
                    self._state = '雾'
                else:
                    self._state = '无数据'
            if self._sensor ==  'cloudrate':
                self.data_forecast = self.data_forecast['result']['hourly']
                self._state = int(self.data_forecast ['cloudrate'][0]['value']*100)
                add_cloudrate_data = {}
                for i in range(47,-1,-1):
                    cloudrate_data = {self.data_forecast ['cloudrate'][i]['datetime']:int(self.data_forecast ['cloudrate'][i]['value']*100)}
                    add_cloudrate_data = dict(cloudrate_data, **add_cloudrate_data)
                self.attributes = add_cloudrate_data
            if self._sensor ==  'aqi':
                self.data_forecast = self.data_forecast['result']['hourly']
                self._state = self.data_forecast ['aqi'][0]['value']
                add_aqi_data = {}
                for i in range(47,-1,-1):
                    aqi_data = {self.data_forecast ['aqi'][i]['datetime']:self.data_forecast ['aqi'][i]['value']}
                    add_aqi_data = dict(aqi_data, **add_aqi_data)
                self.attributes = add_aqi_data
            if self._sensor ==  'humidity':
                self.data_forecast = self.data_forecast['result']['hourly']
                self._state = int(self.data_forecast ['humidity'][0]['value']*100)
                add_humidity_data = {}
                for i in range(47,-1,-1):
                    humidity_data = {self.data_forecast ['humidity'][i]['datetime']:int(self.data_forecast ['humidity'][i]['value']*100)}
                    add_humidity_data = dict(humidity_data, **add_humidity_data)
                self.attributes = add_humidity_data

            if self._sensor ==  'pm25':
                self.data_forecast = self.data_forecast['result']['hourly']
                self._state = self.data_forecast ['pm25'][0]['value']
                add_pm25_data = {}
                for i in range(47,-1,-1):
                    pm25_data = {self.data_forecast ['pm25'][i]['datetime']:self.data_forecast ['pm25'][i]['value']}
                    add_pm25_data = dict(pm25_data, **add_pm25_data)
                self.attributes = add_pm25_data
            if self._sensor ==  'precipitation':
                self.data_forecast = self.data_forecast['result']['hourly']
                self._state = self.data_forecast ['precipitation'][0]['value']
                add_prec_data = {}
                for i in range(47,-1,-1):
                    prec_data = {self.data_forecast ['precipitation'][i]['datetime']:self.data_forecast ['precipitation'][i]['value']}
                    add_prec_data = dict(prec_data, **add_prec_data)
                self.attributes = add_prec_data

            if self._sensor ==  'wind':
                self.data_forecast = self.data_forecast['result']['hourly']
                self._state = self.data_forecast ['wind'][0]['speed']
                add_wind_data = {}
                for i in range(47,-1,-1):
                    wind_data = {self.data_forecast ['wind'][i]['datetime']:self.data_forecast ['wind'][i]['speed']}
                    add_wind_data = dict(wind_data, **add_wind_data)
                self.attributes = add_wind_data
            if self._sensor ==  'temperature':
                self.data_forecast = self.data_forecast['result']['hourly']
                self._state = self.data_forecast ['temperature'][0]['value']
                add_temp_data = {}
                for i in range(47,-1,-1):
                    temp_data = {self.data_forecast ['temperature'][i]['datetime']:self.data_forecast ['temperature'][i]['value']}
                    add_temp_data = dict(temp_data, **add_temp_data)
                self.attributes = add_temp_data

        if self._sensor_Type == CONF_MINUTELY:
            if self._sensor ==  'description':
                self.data_forecast = self.data_forecast['result']['minutely']
                self._state = self.data_forecast ['description']
            if self._sensor ==  'probability_0':
                self.data_forecast = self.data_forecast['result']['minutely']['probability']
                self._state = round(self.data_forecast [0]*100,2)
            if self._sensor ==  'probability_1':
                self.data_forecast = self.data_forecast['result']['minutely']['probability']
                self._state = round(self.data_forecast [1]*100,2)
            if self._sensor ==  'probability_2':
                self.data_forecast = self.data_forecast['result']['minutely']['probability']
                self._state = round(self.data_forecast [2]*100,2)
            if self._sensor ==  'probability_3':
                self.data_forecast = self.data_forecast['result']['minutely']['probability']
                self._state = round(self.data_forecast [3]*100,2)
            for i in range(0,120):
                p2h = 'precipitation_2h'+'_'+str(i)
                if self._sensor ==  p2h:
                    self.data_forecast = self.data_forecast['result']['minutely']['precipitation_2h']
                    self._state = self.data_forecast[i]
            for i in range(0,60):
                ph = 'precipitation'+'_'+str(i)
                if self._sensor ==  ph:
                    self.data_forecast = self.data_forecast['result']['minutely']['precipitation']
                    self._state = self.data_forecast[i]





        if self._sensor_Type == CONF_DAILY:
            self.get_daily(0)
        if self._sensor_Type == 'day1':
            self.get_daily(1)
        if self._sensor_Type == 'day2':
            self.get_daily(2)
        if self._sensor_Type == 'day3':
            self.get_daily(3)
        if self._sensor_Type == 'day4':
            self.get_daily(4)
