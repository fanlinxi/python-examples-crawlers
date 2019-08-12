# !/usr/bin/python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time
import pymysql
import schedule
import datetime

# 谷歌版本7.4
chromedriver_path = "./chromedriver.exe"

# 登录 url
Login_Url = 'https://auth.alipay.com/login/index.htm?goto=https%3A%2F%2Fwww.alipay.com%2F'
# 账单 url
Bill_Url = 'https://consumeprod.alipay.com/record/standard.htm'

"""
执行SQL语句
"""
def db_information(sql):
    return db_operation("127.0.0.0", "mydb", "mydb", "mydb", sql, 3306, "utf8")

"""
连接数据库
host        数据库IP
db          数据库名称
user        数据库用户名称
passwd      数据库用户密码
sql         需要执行的SQL
port        端口号
charset     编码
"""
def db_operation(host, db, user, passwd, sql, port, charset):
    coon = pymysql.connect(host=host,
                           port=port,
                           user=user,
                           passwd=passwd,
                           db=db,
                           charset=charset
                           )
    cur = coon.cursor()
    cur.execute(sql)
    if sql.strip()[:6].upper() == 'SELECT':
        res = cur.fetchall()
    else:
        coon.commit()
        res = '成功'
    cur.close()
    coon.close()
    return res

"""
打开网页
登录支付宝
进入账单页
账单数据入库
"""
class Alipay_Bill_Info(object):

    """
    初始化数据&浏览器
    """
    def __init__(self,username, password):
        # 初始化账号密码
        self.username = username
        self.password = password

        # 初始化浏览器
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2}) # 不加载图片,加快访问速度
        options.add_experimental_option('excludeSwitches', ['enable-automation']) # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium
        options.add_argument('--headless') # 设置无头模式
        options.add_argument('--no-sandbox') # 解决DevToolsActivePort文件不存在的报错
        options.add_argument('--disable-gpu') # 谷歌文档提到需要加上这个属性来规避bug
        options.add_argument('--hide-scrollbars') #隐藏滚动条, 应对一些特殊页面

        self.browser = webdriver.Chrome(executable_path=chromedriver_path, options=options)
        self.wait = WebDriverWait(self.browser, 10) #超时时长为10s

    """
    以恒定的速度输入账号密码
    self 类对象
    ele input输入框
    str 输入值
    """
    def wait_input(self, ele, str):
        for i in str:
            ele.send_keys(i)
            time.sleep(0.5)

    """
    主要的逻辑方法
    self 类对象
    """
    def get_data(self):
        # 变量赋值
        sel = self.browser
        sel.maximize_window()

        # 打开网页
        sel.get(Login_Url)
        sel.implicitly_wait(3)
        time.sleep(1)

        # 找到账号输入框,输入账号
        sel.find_element_by_xpath('//*[@data-status="show_login"]').click()
        usernameInput = sel.find_element_by_id('J-input-user')
        # 清空输入框内容
        usernameInput.clear()
        print('正在输入账号.....')
        self.wait_input(usernameInput, self.username)
        time.sleep(1)

        # 找到密码输入框,输入密码
        passwordInput = sel.find_element_by_id('password_rsainput')
        # 清空输入框内容
        passwordInput.clear()
        print('正在输入密码....')
        self.wait_input(passwordInput, self.password)
        time.sleep(1)

        # 找到登录按钮并点击登录
        print('正在点击登录按钮....')
        butten = sel.find_element_by_id('J-login-btn')
        butten.click()

        print("正在登录支付宝 {}".format(sel.current_url))

        # 跳转到账单页面
        print('正在跳转到账单页面....')
        sel.get(Bill_Url)
        sel.implicitly_wait(3)
        time.sleep(2)

        try:
            """
            获取最新10条的支付宝账单数据
            注有一个问题，只能获取最新10条的数据
            又因为Python技术不到家，所以折中处理
            每半天执行一次脚本文件，添加最新的十条数据到数据库中
            循环添加前进行判断是否已经添加过该条数据如果添加过那么终止循环
            """
            queryRecord_money = "" # 数据库中取出来的最新一条Python脚本添加的数据的金额
            queryRecord_title = "" # 数据库中取出来的最新一条Python脚本添加的数据的标题
            queryMake_date = "" # 数据库中取出来的最新一条Python脚本添加的数据的时间
            queryData = db_information("SELECT * FROM life.record where isManual = 0 ORDER BY make_date DESC LIMIT 1")

            # 如果查询记录数为1，取出最新一条Python脚本添加的数据(此操作防止重复添加以及无数据取值异常)
            if len(queryData) == 1:
                queryRecord_money = queryData[0][3]
                queryRecord_title = queryData[0][5]
                queryMake_date = queryData[0][8]

            # 循环10次 获取10条数据
            for i in range(10):
                # 获取当前行的值
                i = i + 1
                billData = sel.find_element_by_xpath('//*[@id="J-item-' + str(i) + '"]').text
                # billData = '今天\n19:53\n太太好粥(常营店)外卖订单\n饿了么 | 流水号 2019...725 - 14.48\n交易成功\n详情 ' # 范例

                # 分割当条账单数据
                eachSplit = billData.split("\n")

                # 获取每个字段的数据
                user_id = 1 # 用户id
                record_describe = "支付宝账单" # 描述
                record_money = eachSplit[3].split(" ")[len(eachSplit[3].split(" ")) - 1] # 金额
                record_month = datetime.datetime.now().month # 月时间

                # 如果月份为1到9那么转换格式为 01 02 这种
                if len(str(record_month)) == 1:
                    record_month = "0" + str(record_month)
                record_title = eachSplit[2] # 标题
                record_type = 0 # 类型(支出0 收入1)
                record_year = datetime.datetime.now().year # 年时间
                make_date = "{}-{}-{} {}".format(str(record_year), str(record_month), str(datetime.datetime.now().day), str(eachSplit[1])) # 详细时间
                isManual = "0" # 是否为Python脚本添加数据

                # 比对时间金额标题一致，说明此数据已添加过，此数据及以下数据不进行添加
                if queryRecord_money == record_money and queryRecord_title == record_title and queryMake_date == make_date:
                    break

                # 拼接SQL语句
                addSql = """INSERT INTO life.record (id, user_id, record_describe, record_money, record_month, record_title, record_type, record_year, make_date, update_date, isManual) VALUES (null, {}, "{}", {}, "{}", "{}", {}, "{}", "{}", null,{})""".format(str(user_id), str(record_describe), str(record_money), str(record_month), str(record_title), str(record_type), str(record_year), str(make_date), str(isManual))

                # 数据入库
                addSqlInformation = db_information(addSql)

                # 输出添加数据结果
                print("本条数据内容标题为：{} 数据产生时间为：{} 添加结果为{}".format(record_title,make_date,addSqlInformation))
        except Exception as e:
            # 输出错误信息关闭浏览器，并退出方法
            print("登录失败,错误信息：{}".format(e))
            sel.close()
            return

        # 关闭浏览器
        sel.close()


"""
执行爬取账单入库的方法
"""
def job():
    # 登录用户名和密码
    username = ''
    password = ''
    get = Alipay_Bill_Info(username,password)
    get.get_data()


# 主方法
if __name__ == '__main__':

    # 每天中午1点执行一次
    schedule.every().day.at('13:00').do(job)
    # 每天晚上11.30点执行一次
    schedule.every().day.at('23:30').do(job)

    while True:
        schedule.run_pending()