#  -*- coding:utf-8 -*-
from requests import get
from os import makedirs
from os.path import exists
from contextlib import closing
import requests     # 用来抓取网页的html源码
import random   # 取随机数
from bs4 import BeautifulSoup   # 用于代替正则式 取源码中相应标签中的内容
import time     # 时间相关操作
import os       # 文件相关操作

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
            req.encoding = 'gb2312'
            break
        except Exception as e:
            # 输出请求失败信息
            print('页面获取失败=>',e)
            # 等待片刻重新请求
            time.sleep(random.choice(range(8, 15)))
    # 返回HTML文本
    return req.text


"""
文件下载器
file_url            图片下载URL
file_full_name      图片名称
now_photo_count     当前下载数量
all_photo_count     下载总数量
"""
def Down_load(file_url, file_full_name, now_photo_count, all_photo_count):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'if-modified-since': 'Wed, 31 Jul 2019 06:55:40 GMT',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
    }
    # 判断文件是否存在，已存在不进行下载操作(判断依据文件名称)
    if os.path.exists(file_full_name) is False:
        #  开始下载图片
        with closing(get(file_url, headers=headers, stream=True)) as response:
            chunk_size = 1024  # 单次请求最大值
            try:
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
                # 由于某些图片链接请求头中没有content-length属性，所以会进入catch操作，不输出下载进度
                print("\n 当前文件总大小获取失败,本次下载不输出下载进度信息,URL=>" + file_url)
                # 写入文件
                with open(file_full_name, "wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)

class queryPicture(object):
    """
    初始化对象
    """
    def __init__(self):
        self.target = "http://desk.zol.com.cn" # 主站地址
        self.taoTuPicUrls = []  # 拼接套图URL地址
        self.taoTuPicInUrls = "http://desk.zol.com.cn/bizhi/"  # 拼接套图内所有图片URL地址
        # self.picUrl = "http://desk.zol.com.cn/showpic/" # 具体图片拼接URL地址
        self.nums = [] # 分类下壁纸中数量(单位：套)
        self.ulassifyUrls = []  # 分类下所有分页的URL
        self.picUrls = []  # 所有图片URL
        self.PictureClassify = "fengjing"  # 图片分类
        self.PictureSize = "2560x1440"  # 图片尺寸

    """
    获取每个分类所有分页的URL
    """
    def get_classify_urls(self):
        # 拼接分类页面URL
        url = self.target + "/" + self.PictureClassify + "/" + self.PictureSize + "/"
        # 获取HTML文本
        html = get_content(url, [])
        # 解析HTML
        bf = BeautifulSoup(html, 'html.parser')
        texts = bf.find_all('span', {'class': 'allPic'})
        # 获取套图数量
        taoTuNums = int(texts[0].contents[1].text)
        # 计算分页数量
        pages = round(taoTuNums/21)
        # 循环获取套图分页URL
        for i in range(pages):
            self.ulassifyUrls.append(url + str(i+1) + ".html")

    """
    获取每个套图的URL
    """
    def get_taotu_urls(self):
        for index, each in enumerate(self.ulassifyUrls):
            # 获取HTML文本
            html = get_content(each, [])
            # 解析HTML
            bf = BeautifulSoup(html, 'html.parser')
            texts = bf.find_all('li', {'class': 'photo-list-padding'})
            # 循环获取每个套图URL地址
            for each in texts:
                try:
                    self.taoTuPicUrls.append(self.target + each.contents[0].get('href'))
                except Exception as e:
                    # 某些元素的a元素为第二个元素，所以有这个catch操作
                    self.taoTuPicUrls.append(self.target + each.contents[1].get('href'))

    """
    获取每张图片的URL
    """
    def get_picture_urls(self):
        # 循环所有套图URL获取该套图下所有图片URL
        self.nums = len(self.taoTuPicUrls)
        for index, each in enumerate(self.taoTuPicUrls[0:1]): # 只取第一个套图，用于测试
        # for index, each in enumerate(self.taoTuPicUrls):
            # 获取HTML文本
            html = get_content(each, [])
            # 解析HTML
            bf = BeautifulSoup(html, 'html.parser')
            texts = bf.find_all('ul', {'id': 'showImg'})
            # 获取该套图下的所有图片URL
            for ind, eac in enumerate(texts[0].contents):
                ea = eac.contents[1].get('href')
                eachSplit = ea.split("/")
                pictureHtmlUrl = self.taoTuPicInUrls + eachSplit[(len(eachSplit) -1)]
                # 获取HTML文本
                htm = get_content(pictureHtmlUrl, [])
                b = BeautifulSoup(htm, 'html.parser')
                ts = b.find_all('a', {'id': self.PictureSize})
                if len(ts) > 0:
                    picUrl = self.target + ts[0].get('href')
                    self.picUrls.append(picUrl)

    """
    获取每个图片的下载地址
    """
    def get_picture_downloader(self):
        #  所有图片张数
        all_photo_count = len(self.picUrls)

        #  开始下载并保存壁纸
        for index, pictureUrl in enumerate(self.picUrls):
            # 获取HTML文本
            html = get_content(pictureUrl, [])
            # 解析HTML
            bf = BeautifulSoup(html, 'html.parser')
            texts = bf.find_all('img')
            pictureUrl = texts[0].get('src')

            #  创建一个文件夹存放我们下载的图片
            if not exists('./' + str(self.PictureClassify)):
                makedirs('./' + str(self.PictureClassify))

            #  准备下载的图片名称,不包含扩展名
            file_name_only = pictureUrl.split('/')
            file_name_only = file_name_only[len(file_name_only) - 1]

            #  准备保存到本地的完整路径(./分类文件/图片名称)
            file_full_name = './' + self.PictureClassify + '/' + file_name_only

            #  开始下载图片
            Down_load(pictureUrl, file_full_name, (index + 1), all_photo_count)


"""
   主方法
"""
if __name__ == '__main__':
    # # 初始化对象
    qp = queryPicture()
    # 获取所有图片下载URL开始时间
    beginticks = time.time()
    print("获取 " + qp.PictureClassify + " 所有图片下载URL开始时间为：" + time.strftime("%Y{y}%m{m}%d{d} %H{h}%M{m1}%S{s}",time.localtime()).format(y="年",m="月",d="日",h="时",m1="分",s="秒"))

    # 获取每个分类所有分页的URL
    qp.get_classify_urls()
    # 获取每个套图的URL
    qp.get_taotu_urls()
    # 获取每张图片的URL
    qp.get_picture_urls()

    # 获取所有图片下载URL结束时间
    endticks = time.time()
    print("获取 " + qp.PictureClassify + " 分类下所有图片下载URL结束时间为：" + time.strftime("%Y{y}%m{m}%d{d} %H{h}%M{m1}%S{s}",time.localtime()).format(y="年",m="月",d="日",h="时",m1="分",s="秒"))
    #总耗时
    print("获取 " + qp.PictureClassify + " 分类下所有图片下载URL总耗时：{}{}{}{}{}{}{}{}".format(int((endticks-beginticks)/(3600*24)),"天",int(((endticks-beginticks)%(3600*24))/3600),"时",int(((endticks-beginticks))/60),"分",int((endticks-beginticks)%60),"秒"))

    # 图片开始下载时间
    beginticks = time.time()
    print("即将开始下载 " + qp.PictureClassify + " 分类下所有图片,该分类下图片总数为=>" + str(len(qp.picUrls)))
    print(qp.PictureClassify + " 分类下所有图片开始下载时间为：" + time.strftime("%Y{y}%m{m}%d{d} %H{h}%M{m1}%S{s}",time.localtime()).format(y="年",m="月",d="日",h="时",m1="分",s="秒"))

    # 开始下载图片
    qp.get_picture_downloader()

    # 图片结束下载时间
    endticks = time.time()
    print(qp.PictureClassify + " 分类下所有图片结束下载时间为=>" + time.strftime("%Y{y}%m{m}%d{d} %H{h}%M{m1}%S{s}",time.localtime()).format(y="年",m="月",d="日",h="时",m1="分",s="秒"))
    #总耗时
    print("图片结束下载时间总耗时：{}{}{}{}{}{}{}{}".format(int((endticks-beginticks)/(3600*24)),"天",int(((endticks-beginticks)%(3600*24))/3600),"时",int(((endticks-beginticks))/60),"分",int((endticks-beginticks)%60),"秒"))
    num_files = 0 # 路径下文件数量(包括文件夹)
    for fn in os.listdir('./' + qp.PictureClassify):
        num_files += 1
    print("分类：" + qp.PictureClassify + " 下所有图片下载结束,本次下载图片总数量为=>{}".format(num_files))
