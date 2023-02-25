import random
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
import json
import os
import re
import requests


def get_public_key():  # 获取登录用的 RSA 公钥和时间戳
    print('Attempting to get the RSA public key for login.')
    attempts = 1
    url = 'https://www.yiban.cn/login'
    while (attempts <= 3):
        print('Number of attempts:', attempts)
        response = session.get(url, headers=headers)
        if (response.status_code != 200):
            print('Failed to request the login page. Response status code:', response.status_code)
            attempts += 1
            continue
        loginPage = BeautifulSoup(response.text, 'html.parser')
        ul = loginPage.find('ul', attrs={'class': 'login-pr clearfix'})
        if (ul == None):
            print('Public key is not found in the login page. Does Yiban get updated?')
            attempts += 1
            continue
        pubKey = ul.get('data-keys')
        keysTime = ul.get('data-keys-time')
        return pubKey, keysTime
    raise Exception('Failed to get RSA public key. Check the log for more information.')


def login(phone, password, pubKey, keysTime):  # 登录
    print('Attempting to login.')
    attempts = 1
    url = 'https://www.yiban.cn/login/doLoginAjax'
    # 对密码进行加密
    rsa = RSA.importKey(pubKey)
    cipher = PKCS1_v1_5.new(rsa)
    encrypted = base64.b64encode(cipher.encrypt(password.encode('utf-8'))).decode('ascii')
    # 请求登录
    while (attempts <= 3):
        header = {
            'Accept': 'application/json,text/javascript,*/*;q=0.01',
            'Accept-Encoding': 'gzip,deflate,br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Host': 'www.yiban.cn',
            'Origin': 'https://www.yiban.cn',
            'Referer': 'https://www.yiban.cn/login?go=https%3A%2F%2Fwww.yiban.cn%2F',
            'sec-ch-ua': '"Chromium";v="92","NotA;Brand";v="99","GoogleChrome";v="92"',
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                          'Chrome/96.0.4664.110 Safari/537.36 '
        }
        print('Number of attempts:', attempts)
        # time.sleep(8)  # 睡 5s，处理速度太快的话易班服务器会报错 711「pwd 长度必须在 6 至 20 之间」
        payload = {'account': str(phone), 'password': encrypted, 'keysTime': keysTime, 'captcha': None}
        response = session.post(url, data=payload, headers=header)
        if (response.status_code != 200):
            print('Failed to request login. Response status code:', response.status_code)
            attempts += 1
            continue
        body = response.text.encode('utf-8').decode('unicode_escape')
        try:
            result = json.loads(body)
        except json.JSONDecodeError:
            print('There are something wrong with Yiban login response. Does Yiban get updated? Response body:', body)
            attempts += 1
            continue
        if (result['code'] == 200):
            print(response.cookies.get_dict())
            print('Login successfully.')
            if (not actions):
                print('User ID:', result['data']['user_id'])
            return result['code'], result['data']['user_id']
        else:
            print('Failed to login. Response body:', body)
            attempts += 1
            continue
    raise Exception('Failed to login. Check the log for more information.')


def get_streak():  # 检查连续签到天数
    print('Attempting to get the streak.')
    url = 'https://www.yibanyun.cn/app/sign'
    regex = re.compile('var myday = (.*?);')
    response = session.get(url, headers=headers)
    print(response.text)
    if (response.status_code != 200):
        print('Failed to request the sign page. Response status code:', response.status_code)
        return
    signPage = BeautifulSoup(response.text, 'html.parser')
    js = signPage.find('script', attrs={'language': 'JavaScript'})
    if (js == None):
        print('Cannot get the streak. Does Yiban get updated?')
        return
    streak = regex.findall(js.text)[0]
    if (streak == None):
        print('Cannot get the streak. Does Yiban get updated?')
        return
    streak = int(streak.split('\'')[1])
    print('Streak:', streak, 'days.')
    return streak


# 验证码识别  
def base64_api(uname, pwd, image, typeid):
    # with open(img, 'rb') as f:
    #     base64_data = base64.b64encode(f.read())
    #     b64 = base64_data.decode()
    data = {"username": uname, "password": pwd, "typeid": typeid, "image": image}
    result = json.loads(requests.post("http://api.ttshitu.com/predict", json=data).text)
    if result['success']:
        return result["data"]
    else:
        # ！！！！！！！注意：返回 人工不足等 错误情况 请加逻辑处理防止脚本卡死 继续重新 识别
        return result["message"]
    return ""


# 打卡
def get_card():
    url = 'http://daka.yibangou.com'
    response = session.get(url, headers=headers)
    signPage = BeautifulSoup(response.text, 'html.parser')
    item = signPage.find('a', attrs={'class': 'menu home active'})
    index_url = item.get('href')
    return index_url


def get_card_index():
    s = get_card()
    url = 'http://daka.yibangou.com' + s
    response = session.get(url, headers=headers)
    signPage = BeautifulSoup(response.text, 'html.parser')
    js = signPage.findAll('script', attrs={'type': 'text/javascript'})
    s = str(js[1])
    finValue = re.compile(r'<img src="(.*?)"', re.S)
    value = re.findall(finValue, s)
    return value[0];


def get_yam():
    s = get_card_index();
    url = 'http://daka.yibangou.com' + s
    response = session.get(url, headers=headers)
    base64_image = base64.encodebytes(response.content).decode('UTF-8').replace("\n", "")
    # capt = ct.base64_api(base64_image)
    # 二进制转PIL
    # img = Image.open(BytesIO(response.content))
    # img.save("image/1.png")
    # img_path = "image/1.png"
    result = base64_api(uname='图鉴平台账号', pwd='密码', image=base64_image, typeid=1)
    return result


def reportError(id):
    data = {"id": id}
    result = json.loads(requests.post("http://api.ttshitu.com/reporterror.json", json=data).text)
    if result['success']:
        return "报错成功"
    else:
        return result["message"]
    return ""


# 开始打卡
def begin_card():
    result = get_yam()
    print("验证码识别：" + result['result'])
    url = 'http://daka.yibangou.com/index.php?m=wap&c=ajax&a=daka'
    header = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 yiban_iOS/5.0.12',
        'Host': 'daka.yibangou.com',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://daka.yibangou.com',
        'Connection': 'keep-alive',
    }
    params = {'yzm': result['result']}

    response = session.post(url, data=params, headers=header)
    body_dict = response.json()
    code = body_dict['code']
    print(code)
    if (code == 5):
        print("打卡成功")
        return
    elif (code == 4):
        print("已经打卡")
        return
    elif (code == 1):
        print("验证码错误")
        reportError(result['id'])
        begin_card()
    elif (code == 2):
        print("操作异常，不在打卡时间段")
        return

    else:
        reportError(result['id'])
        return

    # 选项签到方法


def my_sign():
    url = 'https://www.yiban.cn/ajax/checkin/checkin'
    header = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 yiban_iOS/5.0.12',
        # User-Agent 伪装成易班 iOS 客户端
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    response = session.get(url, headers=header)
    body_dict = response.json()
    code = body_dict['code']
    if code == 200:
        s = body_dict['data']['survey']
        finValue = re.compile('class=\"survey-option\" data-value="(.*?)" data-input="0"></i>', re.S)
        value = re.findall(finValue, s)
        # 随机
        a = random.randrange(0, len(value))
        return value[a]
    else:
        print(body_dict['message'])
        return 1
    # 勾选答案


def check():
    url = 'https://www.yiban.cn/public/images/checked-s.png'
    response = session.get(url, headers=headers)


# 签到
def my_sign_answer():
    optionid = my_sign()
    if optionid != 1:
        check()
        url = 'https://www.yiban.cn/ajax/checkin/answer'
        header = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 yiban_iOS/5.0.12',
            # User-Agent 伪装成易班 iOS 客户端
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        payload = {
            'optionid[]': optionid,
            'input': ''

        }

        response = session.post(url, data=payload, headers=header)
        body_dict = response.json()
        print(body_dict['data']['subMessage'])
    else:
        return


# json.loads()用于将str类型的数据转成dict。


def sign():  # 签到
    print('Attempting to sign in.')
    attempts = 1
    url = 'https://www.yibanyun.cn/app/sign/signin'
    while (attempts <= 3):
        print('Number of attempts:', attempts)
        response = session.post(url, headers=headers)
        if (response.status_code != 200):
            print('Failed to request sign in. Response code:', response.status_code)
            attempts += 1
            continue
            # decode(‘utf-8’) 把 UTF-8 转化为 Unicode 编码
            # encode(‘utf-8’) 把 Unicode 转化为 UTF-8 编码
        body = response.text.encode('utf8').decode('unicode_escape')
        try:
            result = json.loads(body)
        except json.JSONDecodeError:
            print('There are something wrong with Yiban sign in response. Does Yiban get updated? Response body:', body)
            attempts += 1
            continue
        if (result['status'] == 1):
            print('网薪签到成功')
            # get_streak() #暂时注销
            return result['status'], result['info']
        elif (result['status'] == 0 and result['info'] == '今天已签到过了'):
            print('Already signed today.')
            return result['status'], result['info']
        else:
            print('Cannot make sure whether signed in successfully. Will try again. Response body:', body)
            attempts += 1
            continue
    raise Exception('Failed to sign in. Check the log for more information.')


# 一个python文件通常有两种使用方法，第一是作为脚本直接执行，
# 第二是 import 到其他的 python 脚本中被调用（模块重用）执行。
# 因此 if __name__ == 'main': 的作用就是控制这两种情况执行代码的过程，
# 在 if __name__ == 'main': 下的代码只有在第一种情况下（即文件作为脚本直接执行）才会被执行，
# 而 import 到其他脚本中是不会被执行的。

#打卡授权
def outh():
    oauth_header = {
        'Host': 'oauth.yiban.cn',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 yiban_iOS/5.0.12',
        'Referer': 'https://oauth.yiban.cn/code/html?client_id=' + '7af698a43be206c0' + '&redirect_uri=http://f.yiban.cn/iapp642231',
    }
    oauth_param = {
                "client_id": "7af698a43be206c0",
                "redirect_uri": "http://f.yiban.cn/iapp642231",
                "state": "",
                "scope": "1,2,3,4,",
                "display": "html"
            }
    url = "https://f.yiban.cn/iframe/index?act=iapp642231"
    oauth_url = 'https://oauth.yiban.cn/code/usersure'
    r2 = session.post(oauth_url, data=oauth_param, headers=oauth_header)
    print("打卡授权:"+r2.json()['reUrl'])
    session.get(r2.json()['reUrl'], headers=headers)
    session.get(url, headers=headers)

# 签到授权
def outh_sign():
    oauth_header = {
        'Host': 'oauth.yiban.cn',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 yiban_iOS/5.0.12',
        'Referer': 'https://oauth.yiban.cn/code/html?client_id=' + '7af698a43be206c0' + '&redirect_uri=http://f.yiban.cn/iapp642231',
    }
    oauth_param = {
        "client_id": "9f70b0ffab9b0e9d",
        "redirect_uri": "http://f.yiban.cn/iapp587630",
        "state": "",
        "scope": "1,2,3,4,",
        "display": "html"
    }
    url = "https://f.yiban.cn/iframe/index?act=iapp587630"
    oauth_url = 'https://oauth.yiban.cn/code/usersure'
    r2 = session.post(oauth_url, data=oauth_param, headers=oauth_header)
    print("网薪签到授权:" + r2.json()['reUrl'])
    session.get(r2.json()['reUrl'], headers=headers)
    session.get(url, headers=headers)


if __name__ == '__main__':
    # 用户信息
    if (os.getenv('GITHUB_ACTIONS') == 'true'):
        actions = True
        phone = os.getenv('YIBAN_PHONE')
        password = os.getenv('YIBAN_PASSWORD')
    else:
        actions = False
        config = json.load(open('config.json', 'r'))
        phone = config['phone']
        password = config['password']

    # 杂项
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 yiban_iOS/5.0.12'}  # User-Agent 伪装成易班 iOS 客户端
    session = requests.session()
    pubKey, keysTime = get_public_key()  # 获取登录用的 RSA 公钥和时间戳
    login(phone, password, pubKey, keysTime)  # 登录
    # get_streak()  # 检查连续签到天数
    # 打卡授权
    outh()
    begin_card()  # 打卡
    # 签到授权
    outh_sign()
    sign()  # 签到
    my_sign_answer();  # 选项签到
