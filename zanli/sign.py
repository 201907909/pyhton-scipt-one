# 版本1.0,修复数字验证异常问题， 多个投票问卷进行签到,请求头的校验,随机停留时间
import json
import re
import random
import time
import requests
from bs4 import BeautifulSoup

# 全局消息(日志)
content = ''


# 获取登录参数
def get_login_params():
    url = "https://www.zanli.com/user/login"
    payload = {}
    print(headers)
    response = session.get(url=url, headers=headers, data=payload, verify=False)
    signPage = BeautifulSoup(response.text, 'html.parser')
    # token获取
    token_input = signPage.find('input', {'id': 'login__token'})
    value = token_input['value']
    login_token = value
    return login_token


# 获取未投票问卷集合
def get_list(response):
    signPage = BeautifulSoup(response.text, 'html.parser')
    html = signPage.findAll('div', attrs={'id': 'voteList'})
    s = str(html)
    finValue = re.compile(r'<a class="btn vote-btn" href="(.*?)" type="button">去投票</a>', re.S)
    surveys_dicts = re.findall(finValue, s)  # 未投票的问卷集合
    return surveys_dicts


# 请求登录
def login(account, password, login_token):
    global content
    data = {
        'login[account]': account,  # 填写账号
        'login[password]': password,  # 密码
        'login[remember_me]': 1,  # 记住密码
        'login[fingerprint]': '',  # 浏览器指纹
        'login[_token]': login_token
    }

    url = "https://www.zanli.com/user/login"
    response = session.post(url, data=data, headers=headers, verify=False)
    if (response.status_code == 200):
        print("登录成功")
        content += "登录成功\n"
        return response
    else:
        print("登录失败")
        content += "登录失败\n"


# 问卷的投票(详情)
def vote_surveys(csrf_token, survery, number):
    global content
    # 正则表达式拿问卷的id
    x = re.findall("[0-9][0-9][0-9][0-9]", str(survery))
    url = 'https://www.zanli.com/vote/vote'
    data = {
        'csrf_token': csrf_token,
        'id': x,
        'answer_number': number,
    }
    resp = session.post(url, data=data, headers=headers)
    if (resp.status_code == 200):
        print("今天的问卷投票完成了")
        content += "今天的问卷投票完成了\n"
    else:
        print("出现投票异常")
        content += "出现投票异常\n"


def survey_detail(surveys_dicts):
    global content
    if (len(surveys_dicts) == 0):
        print("所有问卷投票，都已经填写了")
        content += "所有问卷投票，都已经填写了\n"
    else:
        for survery in surveys_dicts:
            url = "https://www.zanli.com" + survery
            resp = session.get(url, headers=headers)
            signPage = BeautifulSoup(resp.text, 'html.parser')
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
            vote_surveys(csrf_token, survery, number)


# 签到签到5天，自动获得1张抽奖券。到签到页面
def checkin():
    global content
    url = 'https://www.zanli.com/event/checkin'
    resp = session.get(url, headers=headers)
    url1 = 'https://www.zanli.com/event/checkin/update'
    resp1 = session.post(url1, headers=headers)
    signPage = BeautifulSoup(resp1.text, 'html.parser')
    html1 = signPage.findAll('h2', attrs={'class': 'res'})
    html12 = str(html1)
    # 输出签到状态
    soup = BeautifulSoup(html12, 'html.parser')
    print(soup.h2.string)
    content += soup.h2.string + "\n"


def push_message(content):
   # 推送token(微信公众号通知)
    push_plus_token = ''
    token = push_plus_token  # 在pushpush网站中可以找到
    title = '攒粒运行日志'  # 改成你要的标题内容
    content = str(content)  # 改成你要的正文内容
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": token,
        "title": title,
        "content": content
    }
    body = json.dumps(data).encode(encoding='utf-8')
    header = {'Content-Type': 'application/json'}
    response = requests.post(url, data=body, headers=header)
    print(response.json())


if __name__ == '__main__':
    account = ''
    password = ''
    headers = {
        'User-Agent': '',
        'Accept': '*/*',
        'Host': 'www.zanli.com',
        'Connection': 'keep-alive'
    }

    # 没有安装证书。每次请求都会有下面的ss警告，看到不是很舒服。（忽略警告）
    requests.packages.urllib3.disable_warnings()
    session = requests.session()
    try:
        # 获取登录的token
        login_token = get_login_params()
        # 登录
        response = login(account, password, login_token)
        # 获取问卷集合
        surveys_dicts = get_list(response)
        # 随机睡眠，模仿人的操作
        time.sleep(random.randrange(1, 20))
        # 问卷的投票详情和投票
        survey_detail(surveys_dicts)
        # 随机睡眠，模仿人的操作
        time.sleep(random.randrange(10, 20))
        # 投票的集合
        checkin()
        # 推送日志
        # push_message(content)
    except Exception as e:
        print(e)
        push_message("出现了异常:" + str(e))

