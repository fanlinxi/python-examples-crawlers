# !/usr/bin/python
# -*- coding: utf-8 -*-

import re
import shutil
from scrapy import Selector
from requests import get
from os import makedirs
from os.path import exists
from contextlib import closing
import requests     # 用来抓取网页的html源码
import os       # 文件相关操作
import random   # 取随机数
import time     # 时间相关操作


# 设置headers是为了模拟浏览器访问 否则的话可能会被拒绝 可通过浏览器获取
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'max-age=0',
    'if-modified-since': 'Wed, 31 Jul 2019 06:55:40 GMT',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
}

"""
获取html文档内容
url     访问路径
params  请求参数
"""
def get_content(url, params):

    # 设置一个超时时间 取随机数 是为了防止网站被认定为爬虫
    timeout = random.choice(range(80, 180))

    # 开始获取HTML页面，获取失败会等待片刻重新获取
    while True:
        try:
            # 忽略不校验SSL证书(verify=False)带来的警告
            requests.packages.urllib3.disable_warnings()
            # requests库获取HTML页面
            """
            url         网页地址
            headers     请求头
            params      请求参数
            verify      是否不校验SSL证书
            timeout     超时时间
            """
            req = requests.get(url=url, headers=headers, params=params,verify=False, timeout=timeout)
            # 设置页面编码
            req.encoding = 'utf-8'

            break
        except Exception as e:
            # 输出请求失败信息
            print('页面获取失败：',e)
            # 等待片刻重新请求
            time.sleep(random.choice(range(8, 15)))
    # 返回HTML文本
    return req.text


"""
文件下载器
file_url            文件下载URL
file_full_name      文件名称
now_photo_count     当前下载数量
all_photo_count     下载总数量
"""
def down_load(file_url, file_full_name, now_photo_count, all_photo_count):
    # 判断文件是否存在，已存在不进行下载操作(判断依据文件名称)
    if os.path.exists(file_full_name) is False:
        try:
            #  开始下载图片
            with closing(get(file_url, headers=headers, stream=True)) as response:
                chunk_size = 1024  # 单次请求最大值
                content_size = int(response.headers['content-length'])  # 文件总大小
                data_count = 0  # 当前已传输的大小
                # 写入文件
                with open(file_full_name, "wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        # 判断下载进度
                        done_block = int((data_count / content_size) * 50)
                        data_count = data_count + len(data)
                        now_jd = (data_count / content_size) * 100
                        # 输出下载进度
                        print("\r %s：[%s%s] %d%% %d/%d" % (file_full_name, done_block * '█', ' ' * (50 - 1 - done_block), now_jd, now_photo_count, all_photo_count), end=" ")
        except Exception as e:
            # 由于某些文件链接请求头中没有content-length属性，所以会进入catch操作，不输出下载进度，但会写入文件
            r = requests.get(file_url)
            with open(file_full_name, "wb") as code:
                code.write(r.content)

"""
下载视频
"""
class VideoDownLoader(object):

    """
    初始化信息
    self    类对象
    url     需要下载的视频地址
    """
    def __init__(self, url):
        self.api = 'https://jx.618g.com' # 主站地址
        self.get_url = 'https://jx.618g.com/?url=' + url # 拼接视频播放URL
        self.title = "" # 视频名称
        self.ts_list = [] # ts列表
        self.parse_url = "" # 获取解析视频地址
        self.m3u8_url = "" # m3u8地址

    """
    通过视频播放URL获取并解析HTML 获取到解析视频地址(期间获取视频名称)
    """
    def parse_page(self):
        # 获取视频播放页HTML
        html = get_content(video_down.get_url, [])

        print('目标信息正在解析........')

        # 解析HTML
        selector = Selector(text=html)
        self.title = selector.xpath("//head/title/text()").extract_first()  # 获取标题(电影名称)

        if self.title is None:
            return False

        print("解析成功 视频名称：{}".format(self.title))

        self.parse_url = selector.xpath("//div[@id='a1']/iframe/@src").extract_first()  # 获取解析视频地址

        return True


    """
    解析m3u8文件获取ts文件
    """
    def get_ts(self):
        try:
            # 获取m3u8 HTML
            html = get_content((self.api + self.parse_url), [])

            print('获取m3u8地址成功，准备提取信息')

            # 解析HTML 获取m3u8地址内容
            m3u8_content = re.findall("vid = '(.*)';", html) # 匹配拥有所有.ts字段内容的url

            m3u8_list = m3u8_content[0].split("/")

            # 分割m3u8地址获取到无参数的地址
            m3u8_url = ""
            for index, each in enumerate(m3u8_list):
                if index == (len(m3u8_list) - 1):
                    break
                m3u8_url += each + "/"

            self.m3u8_url = m3u8_url

            # 获取到包含ts地址的内容并解析放入 self.ts_list
            ts_content = get_content(m3u8_content[0], [])

            print('获取ts文件成功，准备开始下载')

            ts_list = ts_content.split("#EXTINF:")

            for index, each in enumerate(ts_list[1:]):
                self.ts_list.append(self.m3u8_url + each.split("\n")[1])

            # self.ts_list = self.ts_list[1:5] # 只取前五个ts文件用于测试
        except Exception as e:
            print('ts缓存文件请求错误，错误信息{}', e)

    """
    下载ts文件
    """
    def pool(self):
        print('经计算需要下载%d个文件' % len(self.ts_list))
        print('正在下载...所需时间较长，请耐心等待..')

        #  创建一个文件夹存放我们下载的电影
        if not exists('./' + str(self.title)):
            makedirs('./' + str(self.title))

        # 循环缓存文件进行下载
        for index, each in enumerate(self.ts_list):
            #  准备下载的电影名称,不包含扩展名
            file_name_only = str(index)

            #  准备保存到本地的完整路径(./电影名称/循环次数.ts)
            file_full_name = './' + self.title + '/' + file_name_only + ".ts"

            #  开始下载电影
            down_load(each, file_full_name, (index + 1), len(self.ts_list))

        print('所有ts文件下载完成')

    """
    转录ts文件为MP4
    """
    def ts_to_mp4(self):
        print('ts文件正在进行转录mp4......')

        # 合并ts文件到mp4的命令
        string = 'copy /b ' + self.title+'\*.ts ' + self.title + '.mp4'  # copy /b 命令

        # 执行命令
        os.system(string)

        # 转录后的文件名及扩展名
        filename = self.title + '.mp4'

        # 转录完毕删除多余文件
        if os.path.isfile(filename):
            print('转换完成，祝您观影愉快')
            shutil.rmtree(self.title)

# 主方法
if __name__ == '__main__':
    print("数据源为618G免费解析 网址：https://jx.618g.com 源代码网址：https://github.com/fanlinxi/python-examples-crawlers")
    # 获取键盘输入的小说名称
    url = input("请输入要下载的视频地址：")

    beginticks = time.time()

    # 初始化对象
    video_down = VideoDownLoader(url)

    # 获取解析视频地址
    if video_down.parse_page():

        # 得到一个包含ts文件的列表
        video_down.get_ts()

        # 下载ts文件
        video_down.pool()

        # 转录ts文件为MP4
        video_down.ts_to_mp4()
        endticks = time.time()
        print("下载视频总耗时：{}{}{}{}{}{}{}{}".format(int((endticks-beginticks)/(3600*24)),"天",int(((endticks-beginticks)%(3600*24))/3600),"时",int((endticks-beginticks)/60),"分",int((endticks-beginticks)%60),"秒"))
    else:
        print("视频获取失败，本站无该资源")

    time.sleep(5)
    # 退出程序
    exit()