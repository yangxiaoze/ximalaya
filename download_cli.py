#!/usr/bin/env python3

import requests
import json
import execjs
import hashlib
import time
import random
import os
import sys
import logging

#create a logger
logger = logging.getLogger('mylogger')
handler = logging.FileHandler('download_cli.log')
logger.addHandler(handler)
token = open('cookie.txt','r').read()
page_size = 30

# running mode: either count_specific or count_skip
# count_specific has priority
count_specific = 0
count_skip = 0

albumid = '20390423'
album = '细说欧洲列国'

def xm_md5():
    url = 'https://www.ximalaya.com/revision/time'
    headrer = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
        'Host': 'www.ximalaya.com',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    try:
        html = requests.get(url, headers = headrer)
        nowTime = str(round(time.time()*1000))
        sign = str(hashlib.md5("himalaya-{}".format(html.text).encode()).hexdigest()) + "({})".format(str(round(random.random()*100))) + html.text + "({})".format(str(round(random.random()*100))) + nowTime
    except:
        print('Sign 出现错误')
        return 1
    return sign

def getData(albumId):
    url = 'https://www.ximalaya.com/revision/album/v1/getTracksList?albumId={}&pageNum={}'.format(albumId, 1)
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
        'xm-sign': xm_md5()
    }
    response = requests.get(url, headers = headers)
    json_data =  json.loads(response.text)
    if json_data:
        TotalCount = json_data['data']['trackTotalCount']
        TotalPageNumbs = int(TotalCount)//page_size + 1
        print('下载 [' + album + '] Total Pages: ' + str(TotalPageNumbs))
        count = 0
        break_out_flag = False
        for n in range(1, TotalPageNumbs + 1):
            if count_specific > 0:
                if count_specific > n * page_size:
                    print("{}..{}".format(count + 1, count + page_size))
                    count += page_size
                    continue
                elif n * page_size - count_specific > page_size:
                    break
            elif count_skip > 0:
                if count_skip > n * page_size:
                    print("{}..{}".format(count + 1, count + page_size))
                    count += page_size
                    continue

            url = 'https://www.ximalaya.com/revision/album/v1/getTracksList?albumId={}&pageNum={}'.format(albumId, n)
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
                'xm-sign': xm_md5()
            }
            response = requests.get(url, headers = headers)
            json_data = json.loads(response.text)
            tracks = json_data['data']['tracks']
            for x in tracks:
                count += 1
                if (count_specific > 0 and count == count_specific) \
                or (count_specific <= 0 and count > count_skip):
                    title = x['title']
                    trackId = x['trackId']
                    ret = getPlayerUrl(title, trackId, count)
                    if ret != 0:
                        return ret
                    if count_specific > 0:
                        break_out_flag = True
                else:
                    print(count)
            
            if break_out_flag:
                break

    else:
        print('Download 出现错误')
        return 1

def getPlayerUrl(title, trackId, count):
    global token
    url = 'https://mpay.ximalaya.com/mobile/track/pay/{}?device=pc&isBackend=true&_={}'.format(trackId,str(round(time.time()*1000)))
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
                'xm-sign': xm_md5(),
                'cookie': token}
    response = requests.get(url, headers = headers)
    data = eval(response.text.replace('\n','').replace('true', "'true'"))
    with open ('get_player_url.js', 'r') as f:
        js_code = f.read()
    try:
        m4aurl = execjs.compile(js_code).call('get_player_url', data)
        download(title, m4aurl, count)
        #print(title, m4aurl)
        return 0
    except:
        print('get_player_url 出现错误: ' + data['msg'])
        return data['ret']

def download(name, m4aurl, count):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36'
    }
    # path = os.getcwd()
    file_name = album + '/' + name + '.m4a'
    f = requests.get(m4aurl, headers=headers)
    with open(file_name, 'wb') as code:
        code.write(f.content)
    logger.warning("[{} {}] {}: {}".format(album, count, m4aurl, name))
    print('Successfully Download ' + str(count) + ': ' + name)

if __name__ == "__main__":
    arguments = len(sys.argv) - 1
    if arguments > 0:
        albumid = sys.argv[1]
    
    if arguments > 1:
        album = sys.argv[2]
    os.makedirs(album, exist_ok=True)

    getData(albumid)
