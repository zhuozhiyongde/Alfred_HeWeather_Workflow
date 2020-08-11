#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @Time    :   2020/08/10 15:49:04
# @Author  :   Leon/Arthals
# @File    :   HeWeather.py
# @Contact :   zhuozhiyongde@126.com
# @Software:   Visual Studio Code

import sys
import os
from datetime import date, datetime, timedelta
from workflow import Workflow3
reload(sys)
sys.setdefaultencoding('utf8')


def query_weather(wf, query_location=''):
    import requests

    api_key = os.getenv('api_key')
    if query_location != '':
        location = query_location
        adm = ''
    else:
        location = os.getenv('location')
        adm = os.getenv('adm')

    error_dic = {
        '200': '请求成功',
        '204': '请求成功，但你查询的地区暂时没有你需要的数据。',
        '400': '请求错误，可能包含错误的请求参数或缺少必选的请求参数。',
        '401': '认证失败，可能使用了错误的KEY、数字签名错误、KEY的类型错误（如使用SDK的KEY去访问Web API）。',
        '402': '超过访问次数或余额不足以支持继续访问服务，你可以充值、升级访问量或等待访问量重置。',
        '403': '无访问权限，可能是绑定的PackageName、BundleID、域名IP地址不一致，或者是需要额外付费的数据。',
        '404': '查询的数据或地区不存在。',
        '429': '超过限定的QPM（每分钟访问次数），请参考QPM说明',
        '500': '无响应或超时，接口服务异常请联系我们'
    }

    if api_key == '':
        wf.add_item(title=u'APIKey未设置',
                    subtitle=u'请设置api_key的环境变量',
                    quicklookurl=u'https://dev.heweather.com/')
        return

    # 获取城市ID
    geo_url = 'https://geoapi.heweather.net/v2/city/lookup?'
    r = requests.get(geo_url,
                     params={
                         'location': location,
                         'adm': adm,
                         'key': api_key
                     })
    geo_info = r.json()
    if geo_info['status'] != '200':
        failure_title = '地理位置请求异常,错误状态码：' + geo_info['status']
        failure_sub_title = error_dic[geo_info['status']]
        wf.add_item(failure_title, failure_sub_title)
        return
    geo_num = geo_info['location'][0]['id']
    geo_name = geo_info['location'][0]['name']
    geo_adm1 = geo_info['location'][0]['adm1']
    geo_adm2 = geo_info['location'][0]['adm2']
    geo_country = geo_info['location'][0]['country']
    if geo_adm1 == geo_adm2:
        API_title = u'【和风天气 ·{} · {}市】'.format(geo_name, geo_adm1)
        API_sub_title = u'  Code by Leon/Arthals，API by HeWeather，各项具体内容可以选中条目同时按住⇧预览'
        wf.add_item(API_title, API_sub_title)
    if geo_adm1 != geo_adm2:
        API_title = u'【和风天气 · {} · {}省 · {}市】'.format(geo_name, geo_adm1,
                                                      geo_adm2)
        API_sub_title = u'  Code by Leon/Arthals，API by HeWeather'
        wf.add_item(API_title, API_sub_title)

    # 获取数据
    base_url = 'https://devapi.heweather.net/v7/{want_type}/{want_time}?'

    # 判断是否为中国境内，如果不是不请求灾害预警和AQI数据
    if geo_country == '中国':
        # 获取灾害预警
        warn_url = base_url.format(want_type='warning', want_time='now')
        r = requests.get(warn_url,
                         params={
                             'location': geo_num,
                             'key': api_key
                         })
        warn_info = r.json()
        if warn_info['code'] != '200':
            failure_title = '灾害预警请求异常,错误状态码：' + warn_info['code']
            failure_sub_title = error_dic[warn_info['code']]
            wf.add_item(failure_title, failure_sub_title)
            return
        if warn_info['warning']:
            warning_list = []
            warn_link = warn_info['fxLink']
            for i in range(len(warn_info['warning'])):
                if warn_info['warning'][i]['status'] == "active":
                    warn_info_title = warn_info['warning'][i][
                        'typeName'] + warn_info['warning'][i]['level'] + '预警'
                    warning_list.append(warn_info_title)
            if len(warning_list) == 0:
                pass
            elif len(warning_list) == 1:
                warn_title = u'【{}】{}'.format(geo_name, warning_list[0])
                pubTime_list = warn_info['updateTime'].split('+')
                pubTime = str(
                    datetime.strptime(
                        pubTime_list[0],
                        "%Y-%m-%dT%H:%M")) + ' UTC+' + pubTime_list[1]
                warn_sub_title = u'  ↻ {}   蓝色<黄色<橙色<红色   具体内容请按住⇧预览'.format(
                    pubTime)
            else:
                warning_all = '&'.join(warning_list)
                warn_title = u'【{}】{}'.format(geo_name, warning_all)
                pubTime_list = warn_info['updateTime'].split('+')
                pubTime = str(
                    datetime.strptime(
                        pubTime_list[0],
                        "%Y-%m-%dT%H:%M")) + ' UTC+' + pubTime_list[1]
                warn_sub_title = u'  ↻ {}   蓝色<黄色<橙色<红色   具体内容请按住⇧预览'.format(
                    pubTime)
            warn_icon_path = './res/icon-warn/warn.png'
            wf.add_item(warn_title,
                        warn_sub_title,
                        icon=warn_icon_path,
                        quicklookurl=warn_link)

        # 获取 AQI
        aqi_url = base_url.format(want_type='air', want_time='now')
        r = requests.get(aqi_url, params={'location': geo_num, 'key': api_key})
        aqi_info = r.json()
        if aqi_info['code'] != '200':
            failure_title = 'AQI请求异常,错误状态码：' + aqi_info['code']
            failure_sub_title = error_dic[aqi_info['code']]
            wf.add_item(failure_title, failure_sub_title)
            return
        aqi_link = aqi_info['fxLink']
        aqi_num = int(aqi_info['now']['aqi'])
        aqi_state = aqi_info['now']['category']
        if 0 <= int(aqi_num) <= 50:
            aqi_state_en = '1'
        elif 50 < int(aqi_num) <= 100:
            aqi_state_en = '2'
        elif 100 < int(aqi_num) <= 150:
            aqi_state_en = '3'
        elif 150 < int(aqi_num) <= 200:
            aqi_state_en = '4'
        elif 200 < int(aqi_num) <= 300:
            aqi_state_en = '5'
        else:
            aqi_state_en = '6'
        aqi_icon_path = './res/icon-aqi/{}.png'.format(aqi_state_en)
        pubTime_list = aqi_info['updateTime'].split('+')
        pubTime = str(datetime.strptime(
            pubTime_list[0], "%Y-%m-%dT%H:%M")) + ' UTC+' + pubTime_list[1]
        aqi_title = u'【{}】当前AQI {}，{}'.format(geo_name, aqi_num, aqi_state)
        aqi_sub_title = u'  ↻ {}'.format(pubTime)
        wf.add_item(aqi_title,
                    aqi_sub_title,
                    icon=aqi_icon_path,
                    quicklookurl=aqi_link)

    # 获取实时天气
    url = base_url.format(want_type='weather', want_time='now')
    r = requests.get(url, params={'location': geo_num, 'key': api_key})

    weather_info = r.json()

    if weather_info['code'] != '200':
        wf.add_item('实时天气请求异常', '请求错误：' + weather_info['code'])
        # log.error(weather_info)
        return
    weather_link = weather_info['fxLink']
    # 更新时间
    update_time_list = weather_info['updateTime'].split('+')
    update_time = str(datetime.strptime(
        update_time_list[0], "%Y-%m-%dT%H:%M")) + ' UTC+' + update_time_list[1]
    # 温度
    weather_tmp = weather_info['now']['temp']
    # 体感温度
    weather_feel = weather_info['now']['feelsLike']
    # 实况风
    weather_windDir = weather_info['now']['windDir']
    weather_windScale = weather_info['now']['windScale']
    # 天气对应图标
    weather_icon = weather_info['now']['icon']
    # 天气描述
    weather_txt = weather_info['now']['text']
    # 降水量
    weather_precip = weather_info['now']['precip']

    now_time = datetime.strftime(datetime.now(), "%H:%M")
    title = u'【{}】{}，{}'.format(geo_name, now_time, weather_txt)
    sub_title = u'  ☉{}℃（{}℃）    ☁ {}{}级    ☂ {}mm    ↻ {}'.format(
        weather_tmp, weather_feel, weather_windDir, weather_windScale,
        weather_precip, update_time)
    icon_path = './res/icon-heweather/{}.png'.format(weather_icon)
    wf.add_item(title, sub_title, icon=icon_path, quicklookurl=weather_link)

    # '☉☀☂𐑺☾'
    # 逐小时预报-API有问题，暂时不写了

    # 未来3日天气状况
    url = base_url.format(want_type='weather', want_time='3d')
    r = requests.get(url, params={'location': geo_num, 'key': api_key})

    weather_info = r.json()

    if weather_info['code'] != '200':
        failure_title = '未来天气请求异常,错误状态码：' + weather_info['code']
        failure_sub_title = error_dic[weather_info['code']]
        wf.add_item(failure_title, failure_sub_title)
        return

    weather_link = weather_info['fxLink']
    # 更新时间
    update_time = weather_info['updateTime']
    # 温度
    date_trans = ['今天', '明天', '后天']
    for index in range(3):
        index = index + date_valid(
            weather_info['daily'][0]['fxDate'].split('-')[2])
        if index == -1:
            continue
        weather_future = weather_info['daily'][index]
        # 最高温度和最低温度
        tmp_max = weather_future['tempMax']
        tmp_min = weather_future['tempMin']
        # 白天和夜晚
        future_txt_day = weather_future['textDay']
        weather_icon = weather_future['iconDay']
        future_txt_night = weather_future['textNight']
        sunrise = weather_future['sunrise']
        sunset = weather_future['sunset']
        precip = weather_future['precip']
        uvindex = weather_future['uvIndex']
        if 0 <= int(uvindex) <= 2:
            uvindex_info = uvindex + '(较低,无需防晒)'
        elif 3 <= int(uvindex) <= 5:
            uvindex_info = uvindex + '(中等,适当防晒)'
        elif 6 <= int(uvindex) <= 7:
            uvindex_info = uvindex + '(较高,务必防晒)'
        elif 8 <= int(uvindex) <= 10:
            uvindex_info = uvindex + '(甚高,避免外出)'
        elif int(uvindex) >= 11:
            uvindex_info = uvindex + '(极高,不要外出)'
        title = u'【{}】{}白天{}，夜间{}'.format(geo_name,
                                          wf.decode(date_trans[index]),
                                          future_txt_day, future_txt_night)
        time_date, time_week = get_date(index)
        sub_title = '   ↓{}℃    ↑{}℃    ☀{}    ☾{}    ☂{}mm    ☼{}   {}   {}   {}'.format(
            tmp_min, tmp_max, sunrise, sunset, precip, uvindex_info,
            date_trans[index], time_date, time_week)
        # 天气图标
        icon_path = './res/icon-heweather/{}.png'.format(weather_icon)
        wf.add_item(title,
                    sub_title,
                    icon=icon_path,
                    quicklookurl=weather_link)


def date_valid(num):
    validnum = int(num)
    day = datetime.now() + timedelta(days=-1)
    date_num = int(day.strftime('%d'))
    if validnum == date_num:
        return -1
    if validnum != date_num:
        return 0


def get_date(offset=0):
    """
     获取某一天的日期信息.
     args: timedelta 往后查询的天数，默认为0是查询今天
     return: {日期}, {星期}
    """
    week = {
        'Mon': '星期一',
        'Tue': '星期二',
        'Wed': '星期三',
        'Thu': '星期四',
        'Fri': '星期五',
        'Sat': '星期六',
        'Sun': '星期日'
    }
    day = date.today()
    if offset != 0:
        day = datetime.now() + timedelta(days=offset)
    return day.strftime('%m月%d日'), week[day.strftime('%a')]


def main(wf):
    query_location = ""
    if len(wf.args) and wf.args[0] != '':
        query_location = wf.args[0]
    query_weather(wf, query_location)
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    # log = wf.logger
    sys.exit(wf.run(main))
