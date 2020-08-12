#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @Time    :   2020/08/10 15:49:04
# @Update  :   2020/08/12 01:10:54
# @Author  :   Leon/Arthals
# @File    :   HeWeather.py
# @Contact :   zhuozhiyongde@126.com
# @Software:   Visual Studio Code

import sys
import os
from datetime import datetime, timedelta
from workflow import Workflow3
reload(sys)
sys.setdefaultencoding('utf8')


# ☉☀☂𐑺☾
# 定义查询天气函数
def query_weather(wf, query_location='', query_adm=''):
    import requests

    # 获取APIKey
    api_key = os.getenv('api_key')
    # 判断是否含有一级、二级参数，如果有，获取输入参数；如果没有，获取环境参数
    if query_location != '':
        location = query_location
        if query_adm == '':
            adm = ''
        elif query_adm != '':
            adm = query_adm
    else:
        location = os.getenv('location')
        adm = os.getenv('adm')

    # 状态码字典，用于提示错误信息
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

    # 判断APIKey是否未设置
    if api_key == '':
        wf.add_item(title=u'APIKey未设置',
                    subtitle=u'请设置api_key的环境变量',
                    quicklookurl=u'https://dev.heweather.com/')
        return

    # 获取城市ID
    geo_url = 'https://geoapi.heweather.net/v2/city/lookup?'
    # 提前获取一下预设区域的时区，保证后期时间校正正确
    r = requests.get(geo_url,
                     params={
                         'location': os.getenv('location'),
                         'adm': os.getenv('adm'),
                         'key': api_key
                     })
    geo_info = r.json()
    local_utc = geo_info['location'][0]['utcOffset']

    r = requests.get(geo_url,
                     params={
                         'location': location,
                         'adm': adm,
                         'key': api_key
                     })
    geo_info = r.json()

    # 判断是否正常返回数据
    if geo_info['status'] != '200':
        failure_title = '地理位置请求异常,错误状态码：' + geo_info['status']
        failure_sub_title = error_dic[geo_info['status']]
        wf.add_item(failure_title, failure_sub_title)
        return

    # 保存城市信息变量
    geo_num = geo_info['location'][0]['id']  # 城市ID，数字识别码
    geo_name = geo_info['location'][0]['name']  # 城市名称
    geo_adm1 = geo_info['location'][0]['adm1']  # 城市一级区划（省级）
    geo_adm2 = geo_info['location'][0]['adm2']  # 城市二级区划（市级）
    geo_country = geo_info['location'][0]['country']  # 城市所在国家

    # 判断是否为中国所属，如果不处于中国境内，输出信息中加入国家信息
    if geo_country == '中国':
        geo_c1 = ''
    else:
        geo_c1 = '· {} '.format(geo_country)

    # 判断是否是直辖市
    if geo_adm1 == geo_adm2:
        geo_a1 = ''
    else:
        geo_a1 = '· {} '.format(geo_adm1)

    # 判断是否具体到了具体区县
    if geo_name == geo_adm2:
        geo_a2 = ''
    else:
        geo_a2 = '· {} '.format(geo_adm2)
    API_title = u'【和风天气 · {}{}{}{}】'.format(geo_name, geo_c1, geo_a1, geo_a2)
    API_sub_title = u'  Code by Leon/Arthals，API by HeWeather，各项具体内容可以选中条目同时按住⇧\
预览'

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

        # 判断是否正常返回数据
        if warn_info['code'] != '200':
            failure_title = '灾害预警请求异常,错误状态码：' + warn_info['code']
            failure_sub_title = error_dic[warn_info['code']]
            wf.add_item(failure_title, failure_sub_title)
            return

        # 判断预警信息是否为空，如果不是则执行格式化输出
        if warn_info['warning']:
            warning_list = []
            warn_link = warn_info['fxLink']  # 灾害预警自适应网页
            # 获取全部预警信息，加入warning_list
            for i in range(len(warn_info['warning'])):
                if warn_info['warning'][i]['status'] == 'active':
                    warn_info_title = warn_info['warning'][i][
                        'typeName'] + warn_info['warning'][i]['level'] + '预警'
                    warning_list.append(warn_info_title)

            # 列表去重
            warning_list = list(set(warning_list))
            # 如果只有一条预警，直接输出
            if len(warning_list) == 1:
                warn_title = u'【{}】{}'.format(geo_name, warning_list[0])
            # 如果有两条及以上的预警，以'&'分隔后输出
            else:
                warning_all = '&'.join(warning_list)
                warn_title = u'【{}】{}'.format(geo_name, warning_all)
            # 对时间进行切片操作，格式化输出
            warn_pubTime_list = []
            warn_pubTime_list.append(warn_info['updateTime'][:-6])
            warn_pubTime_list.append(warn_info['updateTime'][-6:])
            pubTime = str(
                datetime.strptime(
                    warn_pubTime_list[0],
                    '%Y-%m-%dT%H:%M')) + ' UTC' + warn_pubTime_list[1]
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

        # 判断是否正常返回数据
        if aqi_info['code'] != '200':
            failure_title = 'AQI请求异常,错误状态码：' + aqi_info['code']
            failure_sub_title = error_dic[aqi_info['code']]
            wf.add_item(failure_title, failure_sub_title)
            return

        # 保存AQI信息
        aqi_link = aqi_info['fxLink']  # AQI自适应网页
        aqi_num = int(aqi_info['now']['aqi'])  # AQI程度描述
        aqi_state = aqi_info['now']['category']  # AQI程度描述

        # 获取AQI程度对应等级，以调整icon路径，副标题提示
        if 0 <= int(aqi_num) <= 50:
            aqi_state_en = '1'
            aqi_sub_sug = '空气质量令人满意，基本无空气污染'
        elif 50 < int(aqi_num) <= 100:
            aqi_state_en = '2'
            aqi_sub_sug = '空气质量可接受，但某些污染物可能对极少数异常敏感人群健康有较弱影响'
        elif 100 < int(aqi_num) <= 150:
            aqi_state_en = '3'
            aqi_sub_sug = '易感人群症状有轻度加剧，健康人群出现刺激症状'
        elif 150 < int(aqi_num) <= 200:
            aqi_state_en = '4'
            aqi_sub_sug = '进一步加剧易感人群症状，可能对健康人群心脏、呼吸系统有影响'
        elif 200 < int(aqi_num) <= 300:
            aqi_state_en = '5'
            aqi_sub_sug = '心脏病和肺病患者症状显著加剧，运动耐受力降低，健康人群普遍出现症状'
        else:
            aqi_state_en = '6'
            aqi_sub_sug = '健康人群运动耐受力降低，有明显强烈症状，提前出现某些疾病'
        aqi_icon_path = './res/icon-aqi/{}.png'.format(aqi_state_en)

        # 对时间进行切片操作，格式化输出
        aqi_pubTime_list = []
        aqi_pubTime_list.append(aqi_info['updateTime'][:-6])
        aqi_pubTime_list.append(aqi_info['updateTime'][-6:])
        pubTime = str(
            datetime.strptime(aqi_pubTime_list[0],
                              '%Y-%m-%dT%H:%M')) + ' UTC' + aqi_pubTime_list[1]
        aqi_title = u'【{}】当前AQI {}，{}'.format(geo_name, aqi_num, aqi_state)
        aqi_sub_title = u'  ↻ {}    描述：{}'.format(pubTime, aqi_sub_sug)
        wf.add_item(aqi_title,
                    aqi_sub_title,
                    icon=aqi_icon_path,
                    quicklookurl=aqi_link)

    # 获取实时天气
    url = base_url.format(want_type='weather', want_time='now')
    r = requests.get(url, params={'location': geo_num, 'key': api_key})
    weather_info = r.json()

    # 判断是否正常返回数据
    if weather_info['code'] != '200':
        wf.add_item('实时天气请求异常', '请求错误：' + weather_info['code'])
        # log.error(weather_info)
        return

    weather_link = weather_info['fxLink']  # 天气信息自适应网页
    # 对更新时间进行切片操作，格式化输出
    update_time_list = []
    update_time_list.append(weather_info['updateTime'][:-6])
    update_time_list.append(weather_info['updateTime'][-6:])
    update_time = str(datetime.strptime(
        update_time_list[0], '%Y-%m-%dT%H:%M')) + ' UTC' + update_time_list[1]

    weather_tmp = weather_info['now']['temp']  # 温度
    weather_feel = weather_info['now']['feelsLike']  # 体感温度
    weather_windDir = weather_info['now']['windDir']  # 实况风向
    weather_windScale = weather_info['now']['windScale']  # 实况风级
    weather_icon = weather_info['now']['icon']  # 天气对应图标
    weather_txt = weather_info['now']['text']  # 天气描述
    weather_precip = weather_info['now']['precip']  # 实况降水量

    # 判断查询位置是否在中国境内，如果不在则比较时间，调整输出时间为当地时间
    if geo_country != '中国':
        timezone1 = update_time_list[1].split(':')
        local_utc_list = local_utc.split(':')
        hour_delta = int(timezone1[0]) - int(local_utc_list[0])
        min_delta = int(timezone1[1]) - int(local_utc_list[1])
        location_time = datetime.now() + timedelta(hours=hour_delta,
                                                   minutes=min_delta)
        location_time_str = datetime.strftime(location_time, '%m月%d日 %H:%M')
        title = u'【{}】{}，{}'.format(geo_name, location_time_str, weather_txt)
    else:
        # 获取当前时间
        now_time = datetime.strftime(datetime.now(), '%H:%M')
        title = u'【{}】{}，{}'.format(geo_name, now_time, weather_txt)

    sub_title = u'  ☉{}℃（{}℃）    ☁ {}{}级    ☂ {}mm    ↻ {}'.format(
        weather_tmp, weather_feel, weather_windDir, weather_windScale,
        weather_precip, update_time)
    icon_path = './res/icon-heweather/{}.png'.format(weather_icon)
    wf.add_item(title, sub_title, icon=icon_path, quicklookurl=weather_link)

    # 获取未来3日天气状况
    url = base_url.format(want_type='weather', want_time='3d')
    r = requests.get(url, params={'location': geo_num, 'key': api_key})
    weather_info = r.json()

    # 判断是否正常返回数据
    if weather_info['code'] != '200':
        failure_title = '未来天气请求异常,错误状态码：' + weather_info['code']
        failure_sub_title = error_dic[weather_info['code']]
        wf.add_item(failure_title, failure_sub_title)
        return

    weather_link = weather_info['fxLink']  # 天气信息自适应网页
    update_time = weather_info['updateTime']  # 更新时间
    date_trans = ['今天', '明天', '后天']  # 最近时间翻译

    # 获取三日具体信息
    for index in range(3):
        # 通过date_valiid()函数判别信息是否滞后，如果滞后执行修正
        # 如果不在中国境内，与当地时间进行比较
        if geo_country != '中国':
            index = index + date_valid(
                weather_info['daily'][0]['fxDate'].split('-')[2],
                location_time)
        else:
            index = index + date_valid(
                weather_info['daily'][0]['fxDate'].split('-')[2])

        # 忽略昨天的信息
        if index == -1:
            continue

        weather_future = weather_info['daily'][index]  # 每天信息字典
        tmp_max = weather_future['tempMax']  # 最高温度
        tmp_min = weather_future['tempMin']  # 最低温度
        future_txt_day = weather_future['textDay']  # 白天文字描述
        weather_icon = weather_future['iconDay']  # 输出icon使用白天icon
        future_txt_night = weather_future['textNight']  # 夜晚文字描述
        sunrise = weather_future['sunrise']  # 日出
        sunset = weather_future['sunset']  # 日落
        precip = weather_future['precip']  # 降水
        uvindex = weather_future['uvIndex']  # 紫外线指数

        # 判断紫外线指数强度，调整输出提示
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
        if geo_country != '中国':
            time_date, time_week = get_date(index, location_time)
        else:
            time_date, time_week = get_date(index)
        sub_title = '   ↓{}℃    ↑{}℃    ☀{}    ☾{}    ☂{}mm    ☼{}   {}   {}   \
{}'.format(tmp_min, tmp_max, sunrise, sunset, precip, uvindex_info,
           date_trans[index], time_date, time_week)
        # 天气图标
        icon_path = './res/icon-heweather/{}.png'.format(weather_icon)
        wf.add_item(title,
                    sub_title,
                    icon=icon_path,
                    quicklookurl=weather_link)


# 定义日期对比函数，确定3日预测是否滞后
def date_valid(num, location_time=''):
    validnum = int(num)
    if location_time:
        day = location_time + timedelta(days=-1)
    else:
        day = datetime.now() + timedelta(days=-1)
    date_num = int(day.strftime('%d'))
    if validnum == date_num:
        return -1
    if validnum != date_num:
        return 0


# 定义日期获取函数
def get_date(offset, location_time=''):
    '''
     获取某一天的日期信息.
     args: timedelta 往后查询的天数，默认为0是查询今天
     return: {日期}, {星期}
    '''
    week = {
        'Mon': '星期一',
        'Tue': '星期二',
        'Wed': '星期三',
        'Thu': '星期四',
        'Fri': '星期五',
        'Sat': '星期六',
        'Sun': '星期日'
    }
    if location_time:
        day = location_time
    else:
        day = datetime.today()
    if offset != 0:
        day = datetime.now() + timedelta(days=offset)
    return day.strftime('%m月%d日'), week[day.strftime('%a')]


# 主执行函数
def main(wf):
    query_location = ''
    query_adm = ''
    if len(wf.args) and wf.args[0] != '':
        if ' ' in wf.args[0]:
            query_location = wf.args[0].split('\\ ')[0]
            query_adm = wf.args[0].split('\\ ')[1]
        else:
            query_location = wf.args[0]
            query_adm = ''
    query_weather(wf, query_location, query_adm)
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    # log = wf.logger
    sys.exit(wf.run(main))
