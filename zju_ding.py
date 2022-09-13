# -- coding:UTF-8 --
import requests
import re
import json
import time, datetime, os
# Exceptions 
class LoginError(Exception):
    """Login Exception"""
    pass
class RegexMatchError(Exception):
    """Regex Matching Exception"""
    pass
class DecodeError(Exception):
    """JSON Decode Exception"""
    pass
def dk(name, password):
    login_url = "https://zjuam.zju.edu.cn/cas/login?service=https%3A%2F%2Fhealthreport.zju.edu.cn%2Fa_zju%2Fapi%2Fsso%2Findex%3Fredirect%3Dhttps%253A%252F%252Fhealthreport.zju.edu.cn%252Fncov%252Fwap%252Fdefault%252Findex"
    base_url = "https://healthreport.zju.edu.cn/ncov/wap/default/index"
    save_url = "https://healthreport.zju.edu.cn/ncov/wap/default/save"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }
    sess = requests.Session()
    res = sess.get(login_url, headers=headers)
    execution = re.search('name="execution" value="(.*?)"', res.text).group(1)
    res = sess.get(url='https://zjuam.zju.edu.cn/cas/v2/getPubKey', headers=headers).json()
    n, e = res['modulus'], res['exponent']
    encrypt_password = _rsa_encrypt(password, e, n)
    data = {
            'username': name,
            'password': encrypt_password,
            'execution': execution,
            '_eventId': 'submit'
        }
    res = sess.post(url=login_url, data=data, headers=headers)
    if '统一身份认证' in res.content.decode():
        raise LoginError('登录失败，请核实账号密码重新登录')
    
    res = sess.get(base_url, headers=headers)
    html = res.content.decode()
    try:
        old_infos = re.findall(r'oldInfo: ({[^\n]+})', html)
        if len(old_infos) != 0:
            old_info = json.loads(old_infos[0])
        else:
            raise RegexMatchError("未发现缓存信息，请先至少手动成功打卡一次再运行脚本")
        new_info_tmp = json.loads(re.findall(r'def = ({[^\n]+})', html)[0])
        new_id = new_info_tmp['id']
        name = re.findall(r'realname: "([^\"]+)",', html)[0]
        number = re.findall(r"number: '([^\']+)',", html)[0]
    except IndexError as err:
        raise RegexMatchError('Relative info not found in html with regex: ' + str(err))
    except json.decoder.JSONDecodeError as err:
        raise DecodeError('JSON decode error: ' + str(err))
    
    new_info = old_info.copy()
    new_info['id'] = new_id
    new_info['name'] = name
    new_info['number'] = number
    new_info["date"] = get_date()
    new_info["created"] = round(time.time())
    # form change
    new_info['jrdqtlqk[]'] = 0
    new_info['jrdqjcqk[]'] = 0
    new_info['sfsqhzjkk'] = 1  # 是否申领杭州健康码
    new_info['sqhzjkkys'] = 1  # 杭州健康吗颜色，1:绿色 2:红色 3:黄色
    new_info['sfqrxxss'] = 1  # 是否确认信息属实
    new_info['jcqzrq'] = ""
    new_info['gwszdd'] = ""
    new_info['szgjcs'] = ""
    info = new_info
    res = sess.post(save_url, data=info, headers=headers)
    res_txt = json.loads(res.text)
    if str(res_txt['e']) == '0':
        print("打卡成功")
    elif str(res_txt['e']) == '1':
        print(res_txt['m'])
    else:
        print("打卡失败！")


def _rsa_encrypt(password_str, e_str, M_str):
        password_bytes = bytes(password_str, 'ascii')
        password_int = int.from_bytes(password_bytes, 'big')
        e_int = int(e_str, 16)
        M_int = int(M_str, 16)
        result_int = pow(password_int, e_int, M_int)
        return hex(result_int)[2:].rjust(128, '0')
def get_date():
    """Get current date."""
    today = datetime.date.today()
    return "%4d%02d%02d" % (today.year, today.month, today.day)

if __name__ == "__main__":
    #need to config
    user_name = "22160173" #填写自己的学号
    user_password = "xuan.15613001609" #填写自己的统一身份认证的密码
    res = dk(user_name, user_password)
