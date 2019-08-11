from selenium import webdriver
import datetime
import pymysql
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# chrome_driver = "C:\Python37\Lib\site-packages\selenium\webdriver\chrome\chromedriver.exe"
chromedriver_path = "E:\chromedriver.exe"
# browser = webdriver.Chrome(executable_path=chrome_driver)

# 登录 url
Login_Url = 'https://auth.alipay.com/login/index.htm?goto=https%3A%2F%2Fwww.alipay.com%2F'
# 账单 url
Bill_Url = 'https://consumeprod.alipay.com/record/standard.htm'

"""
执行SQL语句
"""
def db_information(sql):
    return db_operation("106.13.51.1", "life", "life", "wuxi2312@@@", sql, 3306, "utf8")

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
        res = 'ok'
    cur.close()
    coon.close()
    return res

class Alipay_Bill_Info(object):

    def __init__(self,user, passwd):
        self.user = user
        self.passwd = passwd

        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2}) # 不加载图片,加快访问速度
        options.add_experimental_option('excludeSwitches', ['enable-automation']) # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium

        self.browser = webdriver.Chrome(executable_path=chromedriver_path, options=options)
        self.wait = WebDriverWait(self.browser, 10) #超时时长为10s

    def wait_input(self, ele, str):
        for i in str:
            ele.send_keys(i)
            time.sleep(0.5)

    def get_data(self):

        # 打开网页
        self.browser.get(Login_Url)
        # 初始化浏览器对象
        # sel = webdriver.Chrome()
        sel = self.browser
        sel.maximize_window()
        sel.get(Login_Url)
        sel.implicitly_wait(3)
        time.sleep(1)
        # 找到用户名字输入框
        sel.find_element_by_xpath('//*[@data-status="show_login"]').click()
        uname = sel.find_element_by_id('J-input-user')
        uname.clear()
        print('正在输入账号.....')
        self.wait_input(uname, self.user)
        time.sleep(1)
        # 找到密码输入框
        upass = sel.find_element_by_id('password_rsainput')
        upass.clear()
        print('正在输入密码....')
        self.wait_input(upass, self.passwd)
        # 找到登录按钮
        time.sleep(1)
        butten = sel.find_element_by_id('J-login-btn')
        butten.click()

        # sel.save_screenshot('2.png')
        print(sel.current_url)
        # 跳转到账单页面
        print('正在跳转页面....')
        sel.get(Bill_Url)
        sel.implicitly_wait(3)
        time.sleep(2)
        try:
            """
            注有一个问题，只能获取最新10条的数据
            又因为Python技术不到家，所以折中处理
            每半天执行一次脚本文件，添加最新的十条数据到数据库中
            循环添加前进行判断是否已经添加过该条数据如果添加过那么终止循环
            """
            queryData = db_information("SELECT * FROM life.record where isManual = 0 ORDER BY make_date DESC LIMIT 1")
            queryRecord_money = queryData[0][3]
            queryRecord_title = queryData[0][5]
            queryMake_date = queryData[0][8]

            # 获取并循环今日的支付宝账单数据
            for i in range(10):
                i = i + 1
                billData = sel.find_element_by_xpath('//*[@id="J-item-' + str(i) + '"]').text
                # billData = '今天\n19:53\n太太好粥(常营店)外卖订单\n饿了么 | 流水号 2019...725 - 14.48\n交易成功\n详情 '
                # 分割当条账单数据
                eachSplit = billData.split("\n")

                # 获取每个字段的数据
                user_id = 1 # 用户id
                record_describe = "支付宝账单" # 描述
                record_money = eachSplit[3].split(" ")[len(eachSplit[3].split(" ")) - 1] # 金额
                record_month = datetime.datetime.now().month # 月时间
                if len(str(record_month)) == 1:
                    record_month = "0" + str(record_month)
                record_title = eachSplit[2] # 标题
                record_type = 0 # 类型(支出0 收入1)
                record_year = datetime.datetime.now().year # 年时间
                make_date = "{}-{}-{} {}".format(str(record_year), str(record_month), str(datetime.datetime.now().day), str(eachSplit[1])) # 详细时间
                isManual = "0"
                # 拼接SQL语句
                addSql = """INSERT INTO life.record (id, user_id, record_describe, record_money, record_month, record_title, record_type, record_year, make_date, update_date, isManual) VALUES (null, {}, "{}", {}, "{}", "{}", {}, "{}", "{}", null,{})""".format(str(user_id), str(record_describe), str(record_money), str(record_month), str(record_title), str(record_type), str(record_year), str(make_date), str(isManual))
                # asf = db_information(addSql)
                a = 1
        except:
            print("登录出错！")
            sel.close()
            return
        sel.close()


# 主方法
if __name__ == '__main__':
    # 登录用户名和密码
    USERNMAE = ''
    PASSWD = ''

    # print("---------------请求时间" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "---------------------")
    get = Alipay_Bill_Info(USERNMAE,PASSWD)
    get.get_data()
    exit()
    # time.sleep(60*10)