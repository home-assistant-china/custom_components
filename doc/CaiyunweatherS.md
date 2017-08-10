
彩云天气Shttps://bbs.hassbian.com/thread-784-1-1.html是彩云天气的终极形态
之前发布了[教程]分钟级天气预报【彩云天气】组件更新Beta2 https://bbs.hassbian.com/thread-686-1-1.html
存在几个痛点：
不能按照你的要求更新天气数据，只能通过扫描时间调整获取数据的频率。
固定获取home的经纬度【因为我懒得写这个变量】，少了预测某人设备头顶上下雨几率的可能【我也看不懂这是啥意思】。
扫描时间设得过小，apikey消耗过快。设得过大，又失去了实时预测的作用。【总之一个字：穷】


彩云天气S完美解决了以上痛点。

简单介绍下原理：
将天气数据（json格式）的采集独立分离出来，使用下载文件的方式获取数据。CaiyunweatherS.py只负责处理本地下载好的数据。
下载数据用的是Downloader2服务，【因官方提供的不支持自定文件名】https://home-assistant.io/components/downloader/  修改出支持自定文件名的Downloader2
调用Downloader2服务下载天气数据json文件的时候可以传递经纬度 apikey等变量。


使用方法：
下载文件解压放入相应文件夹。
在caiyunweathers.yaml里找到以下代码【第76行】

script:
  download_caiyundata:
    sequence:
      - service: downloader2.download_file
        data_template:
          url: https://api.caiyunapp.com/v2/这里填你的彩云apikey/{{states.zone.home.attributes.longitude}},{{states.zone.home.attributes.latitude}}/forecast
          filename: forecast.json
      - delay: 00:00:03
      - service: downloader2.download_file
        data_template:
          url: https://api.caiyunapp.com/v2/这里填你的彩云apikey/{{states.zone.home.attributes.longitude}},{{states.zone.home.attributes.latitude}}/forecast
          filename: realtime.json

{{states.zone.home.attributes.longitude}}应该要设置了zone才有，没有的话直接填写你所在地经纬度也行。
url: https://api.caiyunapp.com/v2/这里填你的彩云apikey/113.234,22.123/forecast

downloader2:
  download_dir: downloads

download_dir是下载文件夹的路径，需要自己去新建 ，这里是/home/homeassistant/.homeassistant/downloads [树莓派hassbian]
第一次使用会因为downloads/文件夹下面没有 forecast.json realtime.json这两个文件，你的天气界面会一片unknown。更新下天气数据就会正常。【更新按钮在即时天气第一栏】
更新天气就用脚本更新，可自行设置变量来调用，可写自动化来更新。【这部分教程就不写了】。

更新内容：
增加120分钟【precipitation_2h】，每分钟的降雨量预测。增加60分钟【precipitation】，逐分钟的降雨量预测。
增加按天的预测【今天起、共五天day1-day4】
这些参数根据个人要求自行选择，【高能预警，这些都用上会超过1k个传感器】
CaiyunweatherS.py本身不会下载天气数据，因此移除apikey、经纬度等相关参数。使用的时候不再需要填apikey。apikey填在你downloader2下载网址里面。

minutely:
        - description
        - probability_0
        - probability_1
        - probability_2
        - probability_3
        - precipitation_2h
        -



day:
        - day1
        - day2
        - day3
        - day4

注意事项：
1、sensor内置扫描时间30秒一次，下载文件更新天气数据需要一定时间，写脚本及自动化的时候注意加delay【没更新天气数据发了过去很尴尬】
2、为了适应按需调用，特意增加了下载json的服务器时间。发送实时天气的时候顺便发送这个时间值，可以知道天气数据的实时性。