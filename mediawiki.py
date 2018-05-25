#!/usr/bin/env python

from ansible.module_utils.basic import AnsibleModule
import ast
import yaml
import json
import requests
import os
import sys
from base64 import b64encode

class rest_exception(Exception):
    pass


class wiki_rest_client():
    def __init__(self, hostname, prefix, init_path, username, password, ssl_verify=True, token=True, basicauth=False):
        self.XSRFTOKEN='' # the actual token
        self.client = requests.session()
        self.hostname = hostname
        self.prefix = prefix
        userAndPass = "%s:%s" % (username, password)
        if sys.version_info[0] < 3:
            userAndPass = bytes(userAndPass) # python2
        else:
            userAndPass = bytes(userAndPass, 'UTF-8') # python3
        userAndPass = b64encode(userAndPass).decode("ascii")
        self.userAndPass = userAndPass
        self.ssl_verify = ssl_verify
        self.token = token
        self.basicauth = basicauth
        # if basicauth = False, Login to mediawiki, else BASIC Auth as Header
        if self.basicauth:
            # get login token
            URL = "https://%s%s%s" % (self.hostname, self.prefix, '?action=query&meta=tokens&type=login&format=json')
            response = self.client.get(URL, verify=self.ssl_verify)
            if response.status_code != 200:
                raise rest_exception(response.status_code, response.reason)
            self.logintoken = response.json()["query"]["tokens"]["logintoken"]
            # login
            URL = "https://%s%s" % (self.hostname, self.prefix)
            self.payload = dict()
            self.payload["format"] = "json"
            self.payload["action"] = "login"
            self.payload["lgname"] = username
            self.payload["lgpassword"] = password
            self.payload["lgtoken"] = self.logintoken
            response = self.client.post(URL, data=self.payload, verify=self.ssl_verify)
            if response.status_code != 200:
                raise rest_exception(response.status_code, response.reason)
            if response.json()['login']['result'] != 'Success':
                raise RuntimeError(response.json()['login']['reason'])
        # edit token:
        if self.token:
            if self.basicauth == True:
                headers = { 'Authorization' : 'Basic %s' %  self.userAndPass }
            else:
                headers = ''
            URL = "https://%s%s%s" % (self.hostname, self.prefix, init_path)
            response = self.client.get(URL, headers=headers, verify=self.ssl_verify)
            if response.status_code != 200:
                raise rest_exception(response.status_code, response.reason)
            self.XSRFTOKEN = response.json()["query"]["tokens"]["csrftoken"]

    def call(self, method, path, payload):
        if method == 'post':
            method_function = self.client.post
        else:
            method_function = self.client.get
        if self.basicauth == True:
            headers = {
                'Authorization' : 'Basic %s' %  self.userAndPass,
                }
        else:
            headers = ''
        if self.token:
            if method == 'post':
                payload["token"] = self.XSRFTOKEN
                payload['format'] = "json"
                URL = "https://%s%s%s" % (self.hostname, self.prefix, path)
            else:
                URL = "https://%s%s%s%s" % (self.hostname, self.prefix, path, "&format=json")
        response = method_function(URL, data=payload, headers=headers, verify=self.ssl_verify)
        return response

# ansible-facade
class wiki_rest_facade(object):
    def __init__(self, module):
        self.module = module
        self.connection = module.params['connection']
        self.wiki_rest_client = wiki_rest_client(
            self.connection.get('server', 'intra.qsu.office.noris.de'),
            self.connection.get('rest_path', '/wiki/api.php'),
            self.connection.get('token_path', '?action=query&meta=tokens&format=json'),
            self.connection.get('username', ''),
            module.params['password'],
            ssl_verify = self.connection.get('ssl_verify', True),
            token = self.connection.get('token', True),
            basicauth = self.connection.get('basicauth', False),
        )

    def call(self):
        payload = self.module.params['payload']
        payload_obj = ast.literal_eval(payload)
        response = self.wiki_rest_client.call(
            self.module.params['method'],
            self.module.params['path'],
            payload_obj,
        )
        return response

def main():
    module = AnsibleModule(
        argument_spec = dict(
            connection = dict(type='dict', required=True),
            password   = dict(required=True, no_log=True),
            method     = dict(default='get', choices=['get', 'post']),
            path       = dict(required=True),
            payload    = dict(default=dict()),
        )
    )
    client = wiki_rest_facade(module)
    response = client.call()
    result = dict(
        status_code = response.status_code,
        reason = response.reason,
    )
    if response.content:
        result['content'] = json.loads(response.content.decode())
    if result['content'].get('error'):
        msg = result['content']['error']['code']
        msg += ", "
        msg += result['content']['error']['info']
        module.fail_json(msg=msg)
    module.exit_json(changed=True, result=result)

if __name__ == '__main__':
    main()
