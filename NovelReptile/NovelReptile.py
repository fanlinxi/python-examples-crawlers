# !/usr/bin/python
#  -*- coding:utf-8 -*-
import requests # 用来抓取网页的html源码
import random   # 取随机数
from bs4 import BeautifulSoup # 用于代替正则式 取源码中相应标签中的内容
import time # 时间相关操作

reqCount = 0 # 程序访问页面总请求数量

"""
获取html文档内容
url     访问路径
params  请求参数
"""
def get_content(url,params):
    # 设置headers是为了模拟浏览器访问 否则的话可能会被拒绝 可通过浏览器获取
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15'
    }

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
            req = requests.get(url=url, headers=header, params=params,verify=False, timeout=timeout)
            # 设置页面编码
            req.encoding='utf-8'

            # 计算程序访问页面总程序数量
            global reqCount
            cou = reqCount
            reqCount = cou + 1
            break
        except Exception as e:
            # 输出请求失败信息
            print('页面获取失败=>',e)
            # 等待片刻重新请求
            time.sleep(random.choice(range(8, 15)))
    # 返回HTML文本
    return req.text

"""
小说目录地址
获取所有章节地址
解析文章内容
写入本地文件
"""
class downloader(object):
    """
    初始化对象
    """
    def __init__(self):
        self.target = [] # 某本小说主页地址
        self.names = [] # 章节名
        self.urls = []  # 章节链接
        self.nums = 0   # 章节数
        self.novelName = []   # 小说名称
        self.novelAuthor = [] # 小说作者名称

    """
    获取下载的章节目录
    self    类对象
    url     访问路径
    """
    def get_download_catalogue(self,url,novelName):
        self.target = url
        self.novelName = novelName
        # 获取HTML文本
        html = get_content(url, [])
        bf = BeautifulSoup(html, 'html.parser')
        # 获取章节list元素
        texts = bf.find_all('div', {'id': 'list'})
        # 解析元素
        div = texts[0]
        a_s = div.find_all('a')
        # 判断章节数是否大于12，如果大于12则做特殊处理(从第一章开始)
        if len(a_s) >= 12:
            a_s = a_s[12:]
        # a_s = a_s[0:5] # 测试使用，只取前五章
        # 目录总数量
        self.nums = len(a_s)
        # 循环获取章节名称&访问链接并放入对象中
        for each in a_s:
            self.names.append(each.string)
            self.urls.append(self.target + each.get('href'))

    """
    获取下载的具体章节
    self    类对象
    url     访问路径
    """
    def get_download_content(self, url):
        # 获取HTML文本
        html = get_content(url,[])
        bf = BeautifulSoup(html, 'html.parser')
        # 获取文章主题元素
        texts = bf.find_all('div', {'id': 'content'})
        # 删除无用数据
        text = texts[0].text.replace('&nbsp', '')
        text = text.replace('<br>', '')
        text = text.replace('"', '')
        text = text.replace('　　　　    ', '\n')
        # 返回解析完毕的文章内容
        return text

    """
    将文章写入文件
    self    类对象
    name    章节名称
    path    本地文件路径
    text    需要写入的文件内容
    """
    def writer(self,name,path,text):
        with open(path, 'a', encoding='utf-8') as f:
            f.write(name + '\n')
            f.writelines(text)
            f.write('\n')

"""
根据小说名称获取搜索内容
"""
class queryNovel(object):
    # 初始化对象
    def __init__(self):
        self.server = 'https://www.qu.la/' # 小说主页地址(笔趣阁)
        self.novelServer = 'https://sou.xanbhx.com/search' # 查询小说的链接
        self.novelClassify = [] # 作品分类
        self.novelUrl = [] # 目录地址
        self.novelName = [] # 作品名称
        self.novelNewChapterName = [] # 最新章节
        self.novelAuthor = [] # 作者
        self.novelUpdateTime = [] # 更新时间
        self.novelState = [] # 状态

    """
    获取搜索内容
    self    类对象
    url     需要搜索的小说名称
    """
    def get_Novels_content(self,NovelName):
        # 初始化参数
        params = {'siteid': 'qula', 'q': NovelName}
        # 获取HTML文本
        html = get_content(self.novelServer,params)
        bf = BeautifulSoup(html, 'html.parser')
        # 获取搜索内容search-list元素
        search_list = bf.find_all('div', {'class': 'search-list'})
        # 解析元素
        uls = search_list[0].ul
        for index, each in enumerate(uls):
            if each != "\n":
                self.novelClassify.append(each.contents[0].text.replace('\r', '').replace('\n', '').replace(' ', '')) # 作品分类
                # 索引大于1说明数据非表头解析链接放入对象中
                if index > 1:
                    self.novelUrl.append(each.contents[2].a.get('href')) # 目录地址
                self.novelName.append(each.contents[2].text.replace('\r', '').replace('\n', '').replace(' ', '')) # 作品名称
                self.novelNewChapterName.append(each.contents[4].text.replace('\r', '').replace('\n', '').replace(' ', '')) # 最新章节
                self.novelAuthor.append(each.contents[6].text.replace('\r', '').replace('\n', '').replace(' ', '')) # 作者
                self.novelUpdateTime.append(each.contents[10].text.replace('\r', '').replace('\n', '').replace(' ', '')) # 更新时间
                self.novelState.append(each.contents[12].text.replace('\r', '').replace('\n', '').replace(' ', '')) # 状态


# 主方法
if __name__ == '__main__':
    while True:
        # 获取键盘输入的小说名称
        NovelName = input("请输入要下载的小说名称：")
        #  NovelName = "圣墟"
        # 初始化对象
        ql = queryNovel()

        # 查找小说搜索内容
        queryNovel.get_Novels_content(ql,NovelName)
        # 记录数为0提示查询结果为空，否则继续
        if len(ql.novelUrl) == 0:
            print("查询结果为空，下载失败")
        else:
            # 输出查询记录数
            print("查询记录数为：{}".format(len(ql.novelUrl) - 1))

            # 搜索内容集合索引
            count = 0
            while True:
                count+=1
                # 防止索引越界
                if count <= (len(ql.novelName)-1):
                    # 判断是否为表头数据
                    if count == 1:
                        NIndex = "小说索引"
                    else:
                        NIndex = count -1
                    # 输出搜索内容
                    print("{}        {}        {}        {}        {}        {}        {}".format(NIndex,ql.novelClassify[count-1],ql.novelName[count-1],ql.novelNewChapterName[count-1],ql.novelAuthor[count-1],ql.novelUpdateTime[count-1],ql.novelState[count-1]))
                else:
                    break
            # 获取键盘输入的小说索引
            NovelIndex = input("请输入要下载的小说索引：")
            try:
                # 判断索引防止索引越界
                while (int(NovelIndex) >= (len(ql.novelName) - 1)) or (int(NovelIndex) < 0):
                    NovelIndex = input("请输入要下载的小说索引：")

                # 开始下载时间
                beginticks = time.time()
                print("下载开始时间为：" + time.strftime("%Y{y}%m{m}%d{d} %H{h}%M{m1}%S{s}",time.localtime()).format(y="年",m="月",d="日",h="时",m1="分",s="秒"))

                # 初始化下载对象
                dl = downloader()

                # 获取所有目录URL
                dl.get_download_catalogue(ql.novelUrl[int(NovelIndex) -1],ql.novelName[int(NovelIndex)])
                # 循环目录url并解析文章内容写入文件
                for i in range(dl.nums):
                    dl.writer(dl.names[i], dl.novelName + ".txt", dl.get_download_content(dl.urls[i]))
                    print("当前下载章节：" + dl.names[i] + ",当前下载进度：%.2f%%"% float((i+1)/dl.nums * 100) + '\r')

                # 下载结束时间
                endticks = time.time()
                print("下载结束时间为=>" + time.strftime("%Y{y}%m{m}%d{d} %H{h}%M{m1}%S{s}",time.localtime()).format(y="年",m="月",d="日",h="时",m1="分",s="秒"))
                # 总耗时
                print("总耗时：{}{}{}{}{}{}{}{}".format(int((endticks-beginticks)/(3600*24)),"天",int(((endticks-beginticks)%(3600*24))/3600),"时",int(((endticks-beginticks))/60),"分",int((endticks-beginticks)%60),"秒"))
                print('下载完成！本次程序访问页面总请求数量为 ' + str(reqCount))
                # 退出程序
                exit()
            except Exception as e:
                # 输出异常信息
                print('程序异常，终止程序，异常信息=>',e)
                # 退出程序
                exit()