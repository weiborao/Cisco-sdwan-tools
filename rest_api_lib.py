# -*- coding: utf-8 -*-

'''
vManage Rest API library from
https://github.com/ljm625/
with some changes.
'''

import json
import requests
import sdwan_env
import os
import time
import logging

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
logging.debug('Start of program')

here = os.path.abspath(os.path.dirname(__file__))

class rest_api(object):
    instance=None
    def __init__(self, vmanage_ip, username, password,port = 443,tenant=None, tenant_id=None):
        self.vmanage_ip = vmanage_ip
        self.port = port
        self.session = {}
        self.token=None
        self.tenant=tenant
        self.tenant_id=tenant_id
        self.VSessionId=None
        self.login(self.vmanage_ip, port, username, password)

    def get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers["X-XSRF-TOKEN"]=self.token
        if self.VSessionId:
            headers["VSessionId"]=self.VSessionId
        return headers

    def login(self, vmanage_ip, port, username, password):
        """Login to vmanage"""
        base_url_str = 'https://%s:%s' % (vmanage_ip,port)

        login_action = '/j_security_check'

        # Format data for loginForm
        login_data = {'j_username': username, 'j_password': password}

        # Url for posting login data
        login_url = base_url_str + login_action

        # url = base_url_str + login_url

        sess = requests.session()
        # If the vmanage has a certificate signed by a trusted authority change verify to True
        login_response = sess.post(url=login_url, data=login_data, verify=False,headers={"Content-Type":"application/x-www-form-urlencoded"})
        # if self.tenant:
        #     sess.headers.update({'vsession_id':self.tenant})

        if login_response.status_code>=300:
            # print(
            # "Login Failed")
            raise BaseException("ERROR : The username/password is not correct.")
        if '<html>' in login_response.text:
            raise BaseException("ERROR : Login Failed.")

        self.session = sess
        # Get xsrf_token for 19.2 and later versions
        response = self.session.get(base_url_str+ "/dataservice/client/token", verify=False)
        if response.status_code==200:
            self.token = response.text

    def list_tenant(self):
        self.VSessionId=None
        resp = self.get_request("tenant")
        data = resp.json()
        print(data)

    def set_tenant(self, tenant):
        self.VSessionId=None
        resp = self.get_request("tenant")
        data = resp.json()
        tenant_id =None
        if data.get("data") and len(data.get("data"))>0:
            for item in data["data"]:
                if str(item["name"])==str(tenant):
                    tenant_id = item["tenantId"]
        if tenant_id:
            resp = self.post_request("tenant/{}/vsessionid".format(tenant_id),{})
            data = resp.json()
            if data.get("VSessionId"):
                self.VSessionId=data["VSessionId"]
                return True

    def get_request(self, mount_point):
        """GET request"""
        url = "https://%s:%s/dataservice/%s" % (self.vmanage_ip, self.port, mount_point)
        headers = self.get_headers()
        logging.debug('Start of get_request(%s)' % (url + '\t' + str(headers)))
        response = self.session.get(url, verify=False, headers=headers)
        logging.debug('Start of get_request(%s)' % (url + '\t' + str(headers) + str(response.text)))
        if response.status_code>=300:
            response.raise_for_status()
        elif response.status_code==200:
            return response
        else:
            return None

    def post_request(self, mount_point, payload):
        """POST request"""
        url = "https://%s:%s/dataservice/%s" % (self.vmanage_ip, self.port, mount_point)
        headers = self.get_headers()
        payload = json.dumps(payload)
        logging.debug('Start of post_request(%s)' % (url + '\t' + str(headers)))
        response = self.session.post(url=url, data=payload, headers=headers, verify=False)
        logging.debug('Start of post_request(%s)' % (url + '\t' + str(headers) + str(response.text)))
        return response

    def put_request(self, mount_point, payload=None):
        """
        PUT Method
        :param mount_point: The url for API
        :param payload: The payload for API
        :param headers: The header
        :return: response
        """
        url= "https://{}:{}/dataservice/{}".format(self.vmanage_ip,self.port,mount_point)
        headers = self.get_headers()
        if payload:
            payload=json.dumps(payload)
            response = self.session.put(url=url,data=payload,headers=headers,verify=False)
        else:
            response=self.session.put(url=url,headers=headers,verify=False)
        return response

    def post_vsession(self,tenant_id=''):
        """Get a session cookie"""
        # self.VSessionId=None
        if tenant_id == '':
            return 0
        else:
            mount_point = 'tenant/' + tenant_id + '/vsessionid?tenant_id=' + tenant_id
            response = self.post_request(mount_point, payload='')
            return response

    def query_dpi(self, hours='24'):
        """Query DPI data from vManage"""
        mount_point = 'statistics/dpi/aggregation'
        payload = {
            "query": {
                "condition": "AND",
                "rules": [
                    {
                        "value": [
                            hours
                        ],
                        "field": "entry_time",
                        "type": "date",
                        "operator": "last_n_hours"
                    }
                ]
            },
            "aggregation": {
                "field": [
                    {
                        "property": "family",
                        "size": 2000,
                        "sequence": 1
                    },
                    {
                        "property": "vdevice_name",
                        "size": 2000,
                        "sequence": 2
                    }
                ],
                "histogram": {
                    "property": "entry_time",
                    "type": "minute",
                    "interval": 5,
                    "order": "asc"
                },
                "metrics": [
                    {
                        "property": "octets",
                        "type": "sum",
                        "order": "desc"
                    }
                ]
            }
        }

        print('DEBUG: DPI Query payload type:', type(payload))
        response = self.post_request(mount_point, payload)
        return response

    def get_device_info(self, uuid):
        """Get device details info"""
        mount_point = 'system/device/vedges'
        mount_point += '?uuid=' + uuid + '&&'
        response = self.get_request(mount_point)
        return response

    def get_device_config(self, uuid, templateId=''):
        """Get device config by template"""
        payload = {
                "templateId": templateId,
                "deviceIds": [uuid],
        }
        mount_point = 'template/device/config/input/'
        response = self.post_request(mount_point, payload)
        device_config = response.json()['data'][0]
        with open(uuid + '.json', 'w') as file_obj:
            json.dump(device_config, file_obj)
        file_path = here + uuid + '.json'
        print(file_path, '\n', device_config)
        return file_path

    def push_cli_config(self, uuid, templateId=''):
        """Push CLI config to Device"""
        mount_point = 'template/device/config/attachcli'
        # print('DEBUG: push cli config, payload: ', payload, '\n', type(payload))
        with open(uuid + '.json', 'r') as file_obj:
            config_data = json.load(file_obj)
        cli_template = {
            "deviceTemplateList": [
                {
                    "device": [
                    ],
                    "isEdited": False,
                    "templateId": templateId
                }
            ]
        }
        if uuid == config_data['csv-deviceId']:
            cli_template['deviceTemplateList'][0]['device'].append(config_data)
        else:
            print("UUID not equal")
            return 'UUID not equal'
        print('DEBUG: cli_tempdata type:', type(cli_template), '\n', cli_template)
        time.sleep(1)
        response = self.post_request(mount_point, cli_template)
        return response

    def check_job(self, job_id):
        """Check Job Status"""
        mount_point = 'device/action/status/' + job_id['id']
        while True:
            time.sleep(10)
            response = self.get_request(mount_point)
            # print('DEBUG: check_job response :',response.status_code, '\n',
            #       response.headers, '\n', response.text, '\n', response.url)
            if response.status_code == 200:
                if response.json()['data'][0]['status'] == 'Success':
                    return response
                else:
                    continue
            else:
                return '''{job_status: "failed", actionConfig: "job failed"}'''

def set_env():
    help = """Please choose the server you want to connect."""
    print(help)
    for server in sdwan_env.server_list:
        print('({index})\t{server_name}'.format(
            index=sdwan_env.server_list.index(server),
            server_name=server['server_name']))

    server_choice = input("Choose your server:")
    server_choice = int(server_choice)

    server_info = sdwan_env.server_list[server_choice]
    print(server_info)

    if server_info['tenant'] != 'single_tenant_mode':
        print("Please choose the tenant.")
        for tenant in server_info['tenant']:
            print('({index})\t{tenant_name}'.format(
                index=server_info['tenant'].index(tenant),
                tenant_name=tenant['name']))
        tenant_choice = input("Choose your tenant:")
        tenant_choice = int(tenant_choice)
        tenant = server_info['tenant'][tenant_choice]
        server_info['tenant'] = [tenant]
    elif server_info['tenant'] == 'single_tenant_mode':
        print("vManage is in single tenant mode.")

    with open("server_info.json", "w") as file_obj:
        json.dump(server_info, file_obj)
        print("Set env to {name}\nHostname: {hostname}".format(
            name=server_info['server_name'],
            hostname=server_info['hostname']))