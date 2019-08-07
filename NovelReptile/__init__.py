#!/usr/bin/python
# -*- coding:utf-8 -*-

import requests #用来抓取网页的html源码
import random   #取随机数
from bs4 import BeautifulSoup #用于代替正则式 取源码中相应标签中的内容
import time #时间相关操作
import re

"""
获取html文档内容
"""
def get_content(url,params):
    #设置headers是为了模拟浏览器访问 否则的话可能会被拒绝 可通过浏览器获取
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15'
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        # 'Accept-Encoding': 'gzip, deflate, br',
        # 'Accept-Language': 'zh-CN,zh;q=0.9',
        # 'Cache-Control': 'max-age=0',
        # 'Connection': 'keep-alive',
        # 'Host': 'sou.xanbhx.com',
        # 'Upgrade-Insecure-Requests': '1',
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
    }

    #设置一个超时时间 取随机数 是为了防止网站被认定为爬虫
    #timeout = random.choice(range(80, 180))

    while True:
        try:
            #req = requests.get(url=url, headers=header, timeout=timeout)
            requests.packages.urllib3.disable_warnings()
            req = requests.get(url=url, headers=header, params=params,verify=False)
            req.encoding='utf-8'
            break
        except Exception as e:
            print('3',e)
            time.sleep(random.choice(range(8, 15)))
    return req.text

class downloader(object):
    def __init__(self):
        self.server = 'https://www.qu.la/' #小说主页地址
        self.target = 'https://www.qu.la/book/24868/' #某本小说主页地址
        self.names = [] #章节名
        self.urls = []  #章节链接
        self.nums = 0   #章节数
        self.novelName = []   #小说名称
        self.novelAuthor = [] #小说作者名称

    """
    获取下载的章节目录
    """
    def get_download_catalogue(self,url):
        html = get_content(url, [])
        bf = BeautifulSoup(html, 'html.parser')
        texts = bf.find_all('div', {'id': 'list'})
        novel = bf.find_all('div', {'id': 'info'})
        self.novelName = novel[0].contents[1].text
        self.novelAuthor = novel[0].contents[3].text.replace('作', '').replace('者', '').replace('&nbsp', '').replace('：', '').replace(' ', '')
        div = texts[0]
        a_s = div.find_all('a')
        #判断章节数是否大于12，如果大于12则做特殊处理(从第一章开始)
        if len(a_s) >= 12:
            a_s = a_s[12:]
        self.nums = len(a_s)
        for each in a_s:
            self.names.append(each.string)
            self.urls.append(self.target + each.get('href'))

    """
    获取下载的具体章节
    """
    def get_download_content(self, url):
        html = get_content(url)
        bf = BeautifulSoup(html, 'html.parser')
        texts = bf.find_all('div', {'id': 'content'})
        text = texts[0].text.replace('&nbsp', '')
        text = text.replace('<br>', '')
        text = text.replace('"', '')
        return text

    """
    将文章写入文件
    """
    def writer(self,name,path,text):
        write_flag = True
        with open(path, 'a', encoding='utf-8') as f:
            f.write(name + '\n')
            f.writelines(text)
            f.write('\n')

class queryNovel(object):
    def __init__(self):
        self.novelServer = 'https://sou.xanbhx.com/search' #查询小说的链接
        self.novelUrl = [] #目录地址
        self.novelName = [] #作品名称

    """
    获取搜索内容
    """
    def get_Novels_content(self,NovelName):
        params = {'siteid': 'qula', 'q': NovelName}
        html = get_content(self.novelServer,params)
        bf = BeautifulSoup(html, 'html.parser')
        search_list = bf.find_all('div', {'class': 'search-list'})
        uls = search_list[0].ul
        for index, each in enumerate(uls):
            if each != "\n":
                novelName = each.contents[2].text.replace('\r', '').replace('\n', '').replace(' ', '')
                if novelName == NovelName:
                    self.novelUrl = each.contents[2].a.get('href')
                    self.novelName = each.contents[2].text.replace('\r', '').replace('\n', '').replace(' ', '')
                    break


if __name__ == '__main__':
    # beginticks = time.time()
    # print ("下载开始时间为：" + time.strftime("%Y{y}%m{m}%d{d} %H{h}%M{m1}%S{s}",time.localtime()).format(y="年",m="月",d="日",h="时",m1="分",s="秒"))
    # dl = downloader()
    # dl.get_download_catalogue(dl.target)
    # for i in range(dl.nums):
    #     dl.writer(dl.names[i], dl.novelName + ".txt", dl.get_download_content(dl.urls[i]))
    #     print("当前下载章节：" + dl.names[i] + ",当前下载进度：%.2f%%"% float((i+1)/dl.nums * 100) + '\r')
    # endticks = time.time()
    # print ("下载结束时间为=>" + time.strftime("%Y{y}%m{m}%d{d} %H{h}%M{m1}%S{s}",time.localtime()).format(y="年",m="月",d="日",h="时",m1="分",s="秒"))
    # print ("总耗时：{}{}{}{}{}{}{}{}".format(int((endticks-beginticks)/(3600*24)),"天",int(((endticks-beginticks)%(3600*24))/3600),"时",int(((endticks-beginticks)%60)/60),"分",int(endticks-beginticks),"秒"))
    # print('下载完成！')

    while(True):
        NovelName = input("请输入要下载的小说名称：")
        queryNovel = queryNovel(NovelName)
        queryNovel.get_Novels_content(NovelName)
        if len(queryNovel.novelUrl) == 0:
            print("查询结果为空，下载失败")
        else:
            a = 13