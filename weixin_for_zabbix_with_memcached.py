#-*- coding:utf-8 -*-
__author__ = 'cyrus.sun'

import os
import sys
import time
import json
import requests
import memcache

'''
参考文档：
    http://wuhf2015.blog.51cto.com/8213008/1688614

微信消息类型及数据格式
    http://qydev.weixin.qq.com/wiki/index.php?title=%E6%B6%88%E6%81%AF%E7%B1%BB%E5%9E%8B%E5%8F%8A%E6%95%B0%E6%8D%AE%E6%A0%BC%E5%BC%8F
    {
       "touser": "UserID1|UserID2|UserID3",
       "toparty": " PartyID1 | PartyID2 ",
       "totag": " TagID1 | TagID2 ",
       "msgtype": "text",
       "agentid": 1,
       "text": {
           "content": "Holiday Request For Pony(http://xxxxx)"
       },
       "safe":"0"
    }
    参数	    必须	   说明
    touser	否	成员ID列表（消息接收者，多个接收者用‘|’分隔，最多支持1000个）。特殊情况：指定为@all，则向关注该企业应用的全部成员发送
    toparty	否	部门ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
    totag	否	标签ID列表，多个接收者用‘|’分隔。当touser为@all时忽略本参数
    msgtype	是	消息类型，此时固定为：text （支持消息型应用跟主页型应用）
    agentid	是	企业应用的id，整型。可在应用的设置页面查看
    content	是	消息内容，最长不超过2048个字节，注意：主页型应用推送的文本消息在微信端最多只显示20个字（包含中英文）
    safe	否	表示是否是保密消息，0表示否，1表示是，默认0
    说明：
        当消息中有toparty是全发送到部门全体人员，脚本中省掉了这个参数
        totag标签ID这里没什么用，具体用途可以GOOGLE
        content中有中文字符时，需要json.dumps(data,ensure_ascii=False)
        其它的参数根据实际情况指定，agentid
    另外：
        access_token有效期是7200s，过期要重新取，所以脚本中有缓存access_token 7200s
        此脚本是用来发送zabbix消息的，所以在发送时将subject和text合并在一起发送，其它用途可根据实际情况修改
'''

class WeChatMsg(object):
    def __init__(self,username,content):
        self.memcached_server = '127.0.0.1:11211' #这里是memcached服务器地址和端口，注意修改
        self.client = memcache.Client([self.memcached_server])
        self.get_token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        self.send_msg_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
        self.get_token_content = {
                            'corpid': 'xxxx',
                            'corpsecret': 'xxxxx'
                            }  #这里指定管理员账号和密钥,注意修改
        self.main_text_content = {
                           'touser': username,
                           'msgtype': 'text',
                           'agentid': 1,   #这里是应用ID，注意修改
                           'text': {
                                'content': content,
                                }
                            }

    def _request_new_token(self):
        req = requests.get(url=self.get_token_url,params=self.get_token_content)
        access_token = json.loads(req.content)['access_token']
        return access_token

    def _cache_token(self,access_token):
        self.client.set('access_token',access_token,time=7200)

    def get_token(self):
        access_token = self.client.get('access_token')
        if access_token is None:
            access_token = self._request_new_token()
            self._cache_token(access_token)
            return access_token
        else:
            return access_token

    def send_msg(self):
        url = '{0}?access_token={1}'.format(self.send_msg_url,self.get_token())
        data = self.main_text_content
        print data
        req = requests.post(url=url,data=json.dumps(data,ensure_ascii=False))
        return req.status_code,req.content

if __name__ == '__main__':
    if len(sys.argv) == 4:
        username,subject,text = sys.argv[1:]
        content = '{0}\n{1}'.format(subject,text)
        wesener = WeChatMsg(username,content)
        status_code,text = wesener.send_msg()
        print status_code,text
    else:
        msg = 'Usage:\n     {0}  "username" "subject" "text"'.format(sys.argv[0])
        print msg
        sys.exit()
