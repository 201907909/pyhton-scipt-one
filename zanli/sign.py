import json
import random
import re
import requests
from bs4 import BeautifulSoup

# 全局消息
content = ''


# 推送消息
def push_message(content):
    # # 推送token
    push_plus_token = ''
    token = push_plus_token  # 在pushpush网站中可以找到(要填的)
    title = '运行日志'  # 改成你要的标题内容
    content = str(content)  # 改成你要的正文内容
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": token,
        "title": title,
        "content": content
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=body, headers=headers)


# 获取登录的token
def get_login_token():  # 获取登录用的 RSA 公钥和时间戳
    print("开始获取登录用的参数")
    global content
    content += '开始获取登录用的参数\n'
    data = {
        'login[account]': '',  # 账号
        'login[password]': '',  # 密码
        'login[remember_me]': 1,  # 记住密码
        'login[fingerprint]': '',要填的登录的指纹，浏览器找到
        'login[_token]': ''

    }

    url = "https://www.zanli.com/user/login"
    resp = session.post(url, data=data)
    signPage = BeautifulSoup(resp.text, 'html.parser')

    # token获取
    input = signPage.find('input', attrs={'id': 'login__token'})
    s = str(input)
    # 注意转义符
    finValue = re.compile(r'<input id="login__token" name="login\[_token\]" type="hidden" value="(.*?)"', re.S)
    value = re.findall(finValue, s)
    login_token = value[0]
    print("login_token:" + login_token)
    content += "login_token:" + login_token + "\n"

    # 浏览器指纹获取
    input = signPage.find('input', attrs={'id': 'login_fingerprint'})
    s = str(input)
    # 注意转义符
    finValue = re.compile(r'<input id="login_fingerprint" name="login\[fingerprint\]" type="hidden" value="(.*?)"',
                          re.S)
    value = re.findall(finValue, s)
    login_fingerprint = value[0]
    print("login_fingerprint:" + login_fingerprint)
    content += "login_fingerprint:" + login_fingerprint + "\n"
    return login_token, login_fingerprint


# 投票
def vote(csrf_token, id, answer_number):
    global content
    # 正则表达式拿问卷的id
    x = re.findall("[0-9][0-9][0-9][0-9]", str(id))
    url = 'https://www.zanli.com/vote/vote'
    data = {
        'csrf_token': csrf_token,
        'id': x,
        'answer_number': answer_number,
    }
    resp = session.post(url, data=data)
    if (resp.status_code == 200):
        print("今天的一个问卷完成了")
        content += "今天的一个问卷完成了\n"
    else:
        print("出现签到异常")
        content += "出现签到异常\n"


# 去投票详情
def go_vote(value):
    # 现在只是对一个问卷，进行完成，以后会考虑加for循环
    url = "https://www.zanli.com" + value[0]
    resp = session.get(url)
    signPage = BeautifulSoup(resp.text, 'html.parser')
    # print(signPage)
    csrf = signPage.find('input', attrs={'name': 'csrf_token'})
    s = str(csrf)
    # 注意转义符
    finValue = re.compile(r'<input name="csrf_token" type="hidden" value="(.*?)"',
                          re.S)
    csrf_token = re.findall(finValue, s)[0]
    # 选择内容
    ul = signPage.findAll('input', attrs={'name': 'answer_number'})
    number_list = []
    for x in ul:
        number_list.append(x.get('value'))
        # 随机
    a = random.randrange(0, len(number_list))
    number = number_list[a]
    vote(csrf_token, value, number)


# PC 端登录，获取未投票的问卷

def chrome_login(account, password, login_token, login_fingerprint):
    global content
    data = {
        'login[account]': account,  # 填写账号
        'login[password]': password,  # 密码
        'login[remember_me]': 1,  # 记住密码
        'login[fingerprint]': login_fingerprint,
        'login[_token]': login_token
    }

    url = "https://www.zanli.com/user/login"
    resp = session.post(url, data=data)
    signPage = BeautifulSoup(resp.text, 'html.parser')
    html = signPage.findAll('div', attrs={'id': 'voteList'})
    s = str(html)
    finValue = re.compile(r'<a class="btn vote-btn" href="(.*?)" type="button">去投票</a>', re.S)
    value = re.findall(finValue, s)  # 未投票的问卷集合

    # 去签到
    checkin()
    if (len(value) == 0):
        print("所有问卷投票，都已经填写了")
        content += '所有问卷投票，都已经填写了\n'
    else:
        # 去投票
        go_vote(value)


# 签到5天，自动获得1张抽奖券。到签到页面
def checkin():
    global content
    url = 'https://www.zanli.com/event/checkin'
    resp = session.get(url)
    signPage = BeautifulSoup(resp.text, 'html.parser')
    html = signPage.findAll('form', attrs={'method': 'post'})
    # print(signPage)
    url1 = 'https://www.zanli.com/event/checkin/update'
    # 签到
    resp1 = session.post(url1)
    # print(resp1.text)
    signPage = BeautifulSoup(resp1.text, 'html.parser')
    html1 = signPage.findAll('h2', attrs={'class': 'res'})
    html12 = str(html1)
    # 输出签到状态
    soup = BeautifulSoup(html12, 'html.parser')
    print(soup.h2.string)
    temp = str(soup.h2.string)
    content += temp + "\n"


if __name__ == '__main__':
  # 账号
    account = ''
  # 密码
    password = ''
    # 推送token（用的是PushPlus）
    push_plus_token = ''
    session = requests.session()
    try:
        # 获取登录的token
        login_token, login_fingerprint = get_login_token()
        chrome_login(account, password, login_token, login_fingerprint)
        push_message(content)
    except Exception as e:
        print(e)
        push_message("出现了异常:" + str(e))
