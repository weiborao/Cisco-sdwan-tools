# -*- coding: utf-8 -*-

"""
vManage Rest API library from
https://github.com/ljm625/
with some changes.
"""

import json
import requests
import sdwan_env
import os
import time
import logging

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
# logging.disable(logging.CRITICAL)

# logging.debug('Start of program')

here = os.path.abspath(os.path.dirname(__file__))


class CiscoException(Exception):
    pass


class rest_api(object):
    instance = None

    def __init__(self, vmanage_ip, username, password, port=443, tenant=None):
        self.vmanage_ip = vmanage_ip
        self.port = port
        self.session = {}
        self.token = None
        self.tenant = tenant
        self.VSessionId = None
        self.login(self.vmanage_ip, port, username, password)

    def get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers["X-XSRF-TOKEN"] = self.token
        if self.VSessionId:
            headers["VSessionId"] = self.VSessionId
        return headers

    def login(self, vmanage_ip, port, username, password):
        """Login to vmanage"""
        base_url_str = 'https://%s:%s' % (vmanage_ip, port)

        login_action = '/j_security_check'

        # Format data for loginForm
        login_data = {'j_username': username, 'j_password': password}

        # Url for posting login data
        login_url = base_url_str + login_action

        # url = base_url_str + login_url

        sess = requests.session()
        # If the vmanage has a certificate signed by a trusted authority change verify to True
        login_response = sess.post(url=login_url, data=login_data, verify=False,
                                   headers={"Content-Type": "application/x-www-form-urlencoded"})
        # if self.tenant:
        #     sess.headers.update({'vsession_id':self.tenant})

        if login_response.status_code >= 300:
            # print(
            # "Login Failed")
            raise BaseException("ERROR : The username/password is not correct.")
        if '<html>' in login_response.text:
            raise BaseException("ERROR : Login Failed.")

        self.session = sess
        # Get xsrf_token for 19.2 and later versions
        response = self.session.get(base_url_str + "/dataservice/client/token", verify=False)
        if response.status_code == 200:
            self.token = response.text

    def set_tenant(self, tenant):
        self.VSessionId = None
        resp = self.get_request("tenant")
        data = resp.json()
        tenant_id = None
        if data.get("data") and len(data.get("data")) > 0:
            for item in data["data"]:
                if str(item["name"]) == str(tenant):
                    tenant_id = item["tenantId"]
        if tenant_id:
            resp = self.post_request("tenant/{}/vsessionid".format(tenant_id), {})
            data = resp.json()
            if data.get("VSessionId"):
                self.VSessionId = data["VSessionId"]
                return True

    def get_request(self, mount_point, params=''):
        """GET request"""
        url = "https://%s:%s/dataservice/%s" % (self.vmanage_ip, self.port, mount_point)
        headers = self.get_headers()
        logging.debug('Start of get_request %s' % (url + '\t' + str(headers)))
        if params == '':
            response = self.session.get(url, verify=False, headers=headers)
        else:
            response = self.session.get(url, params=params, verify=False, headers=headers)
        logging.debug('End of get_request %s' % (url + '\t' + str(headers) + '\n' +
                                                 str(response.status_code) + '\n' + str(response.text)))
        # if response.status_code>=300:
        # response.raise_for_status()
        # return response
        # elif response.status_code==200:
        return response
        # else:
        #     return None

    def post_request(self, mount_point, payload):
        """POST request"""
        url = "https://%s:%s/dataservice/%s" % (self.vmanage_ip, self.port, mount_point)
        headers = self.get_headers()
        payload = json.dumps(payload)
        logging.debug('Start of post_request %s' % (url + '\t' + str(headers) + '\n' + str(payload)))
        response = self.session.post(url=url, data=payload, headers=headers, verify=False)
        logging.debug('End of post_request %s' % (url + '\t' + str(headers) + '\n' +
                                                  str(response.status_code) + '\n' + str(response.text)))
        return response

    def put_request(self, mount_point, payload=None):
        """
        PUT Method
        :param mount_point: The url for API
        :param payload: The payload for API
        :param headers: The header
        :return: response
        """
        url = "https://{}:{}/dataservice/{}".format(self.vmanage_ip, self.port, mount_point)
        headers = self.get_headers()
        if payload:
            payload = json.dumps(payload)
            logging.debug('Start of put_request %s' % (url + '\t' + str(headers) + '\n' + str(payload)))
            response = self.session.put(url=url, data=payload, headers=headers, verify=False)
            logging.debug('End of put_request %s' % (url + '\t' + str(headers) + '\n'))
        else:
            logging.debug('Start of put_request %s' % (url + '\t' + str(headers) + '\n'))
            response = self.session.put(url=url, headers=headers, verify=False)
            logging.debug('End of put_request %s' % (url + '\t' + str(headers) + '\n'))

        return response

    def delete_request(self, mount_point):
        """DELETE request"""
        url = "https://%s/dataservice/%s" % (self.vmanage_ip, mount_point)
        factory_template_msg = "Template is a factory default"
        policy_list_ro_msg = "This policy list is a read only list and it cannot be deleted"

        headers = self.get_headers()
        logging.debug('Start of delete_request %s' % (url + '\t' + str(headers) + '\n'))

        response = self.session.delete(url=url, headers=headers, verify=False)
        logging.debug('End of delete_request %s' % (url + '\t' + str(headers) + '\n' +
                                                    str(response.status_code) + '\n' + str(response.text)))

        data = response.content

        # print(response.status_code)
        if response.status_code != 200:
            if (response.status_code == 400):
                if (response.json()['error']['details'] == factory_template_msg):
                    return (response.json()['error']['details'])
                elif (response.json()['error']['details'] == policy_list_ro_msg):
                    return (response.json()['error']['details'])
                else:
                    print(response.json()['error']['details'])
                    raise CiscoException("Fail - Delete")
            else:
                print(response)
                raise CiscoException("Fail - Delete")
        if data:
            return data
        else:
            return "Successful"

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

        response = self.post_request(mount_point, payload)
        return response

    def list_all_device(self):
        """List all devices"""
        mount_point = 'device'
        response = self.get_request(mount_point)
        return response

    def get_device_info(self, uuid):
        """Get device details info"""
        mount_point = 'system/device/vedges'
        mount_point += '?uuid=' + uuid + '&&'
        response = self.get_request(mount_point)
        return response

    def get_device_running(self, uuid):
        """Get device running config"""
        if '/' in uuid:
            uuid = uuid.replace('/', '%2F')

        mount_point = 'template/config/running/' + uuid
        response = self.get_request(mount_point)
        return response

    def get_template_type(self, templateId):
        """Get the template type"""
        mount_point = 'template/device'
        response = self.get_request(mount_point)
        data = response.json()
        template_type = ''
        if data.get("data") and len(data.get("data")) > 0:
            for item in data["data"]:
                if item["templateId"] == templateId:
                    template_type = item["configType"]
        return template_type

    def get_device_cli_data(self, uuid, templateId=''):
        """Get device config by template"""
        payload = {
            "templateId": templateId,
            "deviceIds": [uuid],
        }
        mount_point = 'template/device/config/input/'
        response = self.post_request(mount_point, payload)
        device_config = response.json()['data'][0]
        device_config["templateId"]=templateId
        if templateId == "e0d2cc4a-6c65-4503-88c8-3bb95903fa29":
            device_config["organization-name"]="\"China Unicom SDWAN T1\""
            device_config["vbond-address"]="220.250.74.5"
            device_config["controller-name"]= "\"China Unicom\""
            device_config["admin-name"]="admin"
            device_config["admin-password"]="admin"
        if '/' in uuid:
            uuid = uuid.replace('/', '_')
        logging.debug('Filename %s' % uuid)
        with open(uuid + '.json', 'w') as file_obj:
            json.dump(device_config, file_obj)
        file_path = here + '/' + uuid + '.json'
        print(file_path, '\n', device_config, "\n**** Please edit it.")
        return response

    def push_cli_config(self, uuid, templateId=''):
        """Push CLI config to Device"""
        push_mount_point = 'template/device/config/attachcli/'
        if '/' in uuid:
            uuid = uuid.replace('/', '_')
        logging.debug('Filename %s' % uuid)
        with open(uuid + '.json', 'r') as file_obj:
            config_data = json.load(file_obj)
            if config_data.get("templateId"):
                del config_data["templateId"]
        uuid = uuid.replace('_', '/')
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
        time.sleep(1)

        push_response = self.post_request(push_mount_point, cli_template)
        return push_response

    def push_template_config(self, uuid, templateId=''):
        """Push CLI config to Device"""
        push_mount_point = 'template/device/config/attachfeature'
        if '/' in uuid:
            uuid = uuid.replace('/', '_')
        logging.debug('Filename %s' % uuid)
        with open(uuid + '.json', 'r') as file_obj:
            config_data = json.load(file_obj)
            if config_data.get("templateId"):
                del config_data["templateId"]
        uuid = uuid.replace('_', '/')
        config_data['csv-templateId'] = templateId
        feature_template = {
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
            feature_template['deviceTemplateList'][0]['device'].append(config_data)
        else:
            print("UUID not equal")
            return 'UUID not equal'
        time.sleep(1)

        push_response = self.post_request(push_mount_point, feature_template)
        return push_response

    def preview_config(self, uuid, templateId=''):
        """Preview the config"""
        preview_mount_point = 'template/device/config/config/'
        if '/' in uuid:
            uuid = uuid.replace('/', '_')
        logging.debug('Filename %s' % uuid)
        with open(uuid + '.json', 'r') as file_obj:
            config_data = json.load(file_obj)
        uuid = uuid.replace('_', '/')
        config_data['csv-templateId'] = templateId

        preview_template = {
            "device": {},
            "templateId": templateId,
            "isEdited": False,
            "isMasterEdited": False,
            "isRFSRequired": True
        }
        if uuid == config_data['csv-deviceId']:
            preview_template['device'] = config_data
        else:
            print("UUID not equal")
            return 'UUID not equal'
        time.sleep(1)

        push_response = self.post_request(preview_mount_point, preview_template)
        return push_response

    def list_all_template(self):
        """List all template"""
        mount_point = 'template/device/'
        response = self.get_request(mount_point)
        return response

    def select_template(self, device_sn):
        """Select your template"""
        your_choice = input("Do you want to choose a template for this device?(y/n):")
        if your_choice == 'y':
            response = self.list_all_template()
            all_template_list = response.json()['data']
            print("Please choose your template:")
            for template in all_template_list:
                print("({index}) {device_model}\t{template_name}".format(
                    index=all_template_list.index(template),
                    device_model=template["deviceType"],
                    template_name=template["templateName"]))
            template_choice = input("Please choose template:")
            template_choice = int(template_choice)
            templateId = all_template_list[template_choice]["templateId"]
            return templateId
        else:
            return "Bye"

    def check_job(self, job_id):
        """Check Job Status"""
        mount_point = 'device/action/status/' + job_id['id']
        while True:
            time.sleep(10)
            response = self.get_request(mount_point)

            if response.status_code == 200:
                if response.json()['data'][0]['status'] in ["Success", "Done - Scheduled"]:
                    return response
                elif response.json()['data'][0]['status'] == "In progress":
                    print("Job is in progress...")
                    continue
            else:
                return '''{job_status: "failed", actionConfig: "job failed"}'''

    def list_site_list(self):
        """List all site list"""
        mount_point = 'template/policy/list/site'
        response = self.get_request(mount_point)
        return response

    def add_site_list(self, site_name, site_list):
        """Add site list"""
        mount_point = 'template/policy/list/site'
        payload = {
            "name": site_name,
            "description": site_name,
            "type": "site",
            "listId": None,
            "entries": []
        }
        entries = []
        for list in site_list:
            entry = {"siteId": list}
            entries.append(entry)
        payload["entries"] = entries
        response = self.post_request(mount_point, payload)
        return response

    def edit_site_list(self, site_name, site_list, site_id):
        """Edit Site list"""
        mount_point = 'template/policy/list/site/' + site_id
        payload = {
            "name": site_name,
            "description": site_name,
            "type": "site",
            "listId": None,
            "entries": []
        }
        entries = []
        for list in site_list:
            entry = {"siteId": list}
            entries.append(entry)
        payload["entries"] = entries
        response = self.put_request(mount_point, payload)
        return response

    def get_site_list(self, site_id):
        """Get site list by siteId"""
        mount_point = 'template/policy/list/site/' + site_id
        response = self.get_request(mount_point)
        return response

    def delete_site_list(self, site_id):
        """Delete the site list"""
        mount_point = 'template/policy/list/site/' + site_id
        response = self.delete_request(mount_point)
        return response

    def get_site_id_by_name(self, site_name):
        """Get site ID by name"""
        response = self.list_site_list()
        if response.status_code == 200:
            all_site = response.json()['data']
        site_existed = False
        for site in all_site:
            if site['name'] == site_name:
                site_id = site['listId']
                site_existed = True
        if site_existed:
            return site_id
        else:
            return "site_id does not exist"

    def chu_add_site_list(self, site_name, site_list):
        """Customized add site list"""
        response = self.list_site_list()
        if response.status_code == 200:
            all_site = response.json()['data']
        site_existed = False
        for site in all_site:
            if site['name'] == site_name:
                site_id = site['listId']
                response = self.edit_site_list(site_name, site_list, site_id)
                site_existed = True
        if site_existed == False:
            response = self.add_site_list(site_name, site_list)
            if response.status_code == 200:
                site_id = response.json()["listId"]
            else:
                print(response.status_code)

        response = self.get_site_list(site_id)
        site_list = response.json()
        logging.debug('Site added:\n %s' % str(site_list))

    def chu_delete_site_list(self, site_name_list):
        """Customized add site list"""
        response = self.list_site_list()
        if response.status_code == 200:
            all_site = response.json()['data']
        for site in all_site:
            if site['name'][4:] in site_name_list:
                site_id = site['listId']
                response = self.delete_site_list(site_id)
        return response

    def list_tloc_list(self):
        """List all the TLOC list"""
        mount_point = 'template/policy/list/tloc'
        response = self.get_request(mount_point)
        return response

    def add_tloc_list(self, tloc_name, tloc_ip_list):
        """Add tloc list"""
        mount_point = 'template/policy/list/tloc'
        payload = {
            "name": tloc_name,
            "description": tloc_name,
            "type": "tloc",
            "entries": [
                {
                    "tloc": tloc_ip_list[0],
                    "color": "default",
                    "encap": "ipsec",
                    "preference": "100"
                },
                {
                    "tloc": tloc_ip_list[1],
                    "color": "default",
                    "encap": "ipsec",
                    "preference": "100"
                }
            ]
        }
        response = self.post_request(mount_point, payload)
        return response

    def edit_tloc_list(self, tloc_name, tloc_ip_list, tloc_id):
        """Edit tloc list"""
        mount_point = 'template/policy/list/tloc/' + tloc_id
        payload = {
            "name": tloc_name,
            "description": tloc_name,
            "type": "tloc",
            "entries": [
                {
                    "tloc": tloc_ip_list[0],
                    "color": "default",
                    "encap": "ipsec",
                    "preference": "100"
                },
                {
                    "tloc": tloc_ip_list[1],
                    "color": "default",
                    "encap": "ipsec",
                    "preference": "100"
                }
            ]
        }
        response = self.put_request(mount_point, payload)
        return response

    def get_tloc_list(self, tloc_id):
        """Get tloc list by tlocId"""
        mount_point = 'template/policy/list/tloc/' + tloc_id
        response = self.get_request(mount_point)
        return response

    def delete_tloc_list(self, tloc_id):
        """Delete the tloc list"""
        mount_point = 'template/policy/list/tloc/' + tloc_id
        response = self.delete_request(mount_point)
        return response

    def chu_add_tloc_list(self, tloc_name, tloc_ip_list):
        """Customized add tloc list"""
        response = self.list_tloc_list()
        if response.status_code == 200:
            all_tloc = response.json()['data']
        tloc_existed = False
        for tloc in all_tloc:
            if tloc['name'] == tloc_name:
                tloc_id = tloc['listId']
                response = self.edit_tloc_list(tloc_name, tloc_ip_list, tloc_id)
                tloc_existed = True

        if tloc_existed == False:
            response = self.add_tloc_list(tloc_name, tloc_ip_list)
            if response.status_code == 200:
                tloc_id = response.json()["listId"]
            else:
                print(response.status_code)

        response = self.get_tloc_list(tloc_id)
        tloc_list = response.json()
        logging.debug('TLOC List added:\n %s' % str(tloc_list))

    def chu_delete_tloc_list(self, site_name_list):
        """Customized delete tloc list"""
        response = self.list_tloc_list()
        if response.status_code == 200:
            all_tloc = response.json()['data']
        for tloc in all_tloc:
            if tloc['name'][:-6] in site_name_list:
                tloc_id = tloc['listId']
                response = self.delete_tloc_list(tloc_id)
        return response

    def list_top_policy(self):
        """List all the topology policy"""
        mount_point = 'template/policy/definition/control'
        response = self.get_request(mount_point)
        return response

    def add_box_top_policy(self, top_name, pop_site_id, pop_tloc_list_id, all_box_id):
        """Add customized topology policy"""
        mount_point = 'template/policy/definition/control'
        payload = {
            "name": top_name,
            "type": "control",
            "description": top_name[4:] + " BOX OUT Topology Policy",
            "defaultAction": {
                "type": "reject"
            },
            "sequences": [
                {
                    "sequenceId": 1,
                    "sequenceName": "TLOC",
                    "baseAction": "accept",
                    "sequenceType": "tloc",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": [
                            {
                                "field": "siteList",
                                "ref": pop_site_id
                            }
                        ]
                    },
                    "actions": []
                },
                {
                    "sequenceId": 11,
                    "sequenceName": "TLOC",
                    "baseAction": "reject",
                    "sequenceType": "tloc",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": []
                    },
                    "actions": []
                },
                {
                    "sequenceId": 21,
                    "sequenceName": "Route",
                    "baseAction": "accept",
                    "sequenceType": "route",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": [
                            {
                                "field": "siteList",
                                "ref": all_box_id
                            }
                        ]
                    },
                    "actions": [
                        {
                            "type": "set",
                            "parameter": [
                                {
                                    "field": "tlocList",
                                    "ref": pop_tloc_list_id
                                }
                            ]
                        }
                    ]
                },
                {
                    "sequenceId": 31,
                    "sequenceName": "Route",
                    "baseAction": "accept",
                    "sequenceType": "route",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": []
                    },
                    "actions": [
                        {
                            "type": "set",
                            "parameter": [
                                {
                                    "field": "tlocList",
                                    "ref": pop_tloc_list_id
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        response = self.post_request(mount_point, payload)
        return response

    def edit_box_top_policy(self, top_name, pop_site_id, pop_tloc_list_id, top_policy_id, all_box_id):
        """Edit customized topology policy"""
        mount_point = 'template/policy/definition/control/' + top_policy_id
        payload = {
            "name": top_name,
            "type": "control",
            "description": top_name[4:] + " BOX OUT Topology Policy",
            "defaultAction": {
                "type": "reject"
            },
            "sequences": [
                {
                    "sequenceId": 1,
                    "sequenceName": "TLOC",
                    "baseAction": "accept",
                    "sequenceType": "tloc",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": [
                            {
                                "field": "siteList",
                                "ref": pop_site_id
                            }
                        ]
                    },
                    "actions": []
                },
                {
                    "sequenceId": 11,
                    "sequenceName": "TLOC",
                    "baseAction": "reject",
                    "sequenceType": "tloc",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": []
                    },
                    "actions": []
                },
                {
                    "sequenceId": 21,
                    "sequenceName": "Route",
                    "baseAction": "accept",
                    "sequenceType": "route",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": [
                            {
                                "field": "siteList",
                                "ref": all_box_id
                            }
                        ]
                    },
                    "actions": [
                        {
                            "type": "set",
                            "parameter": [
                                {
                                    "field": "tlocList",
                                    "ref": pop_tloc_list_id
                                }
                            ]
                        }
                    ]
                },
                {
                    "sequenceId": 31,
                    "sequenceName": "Route",
                    "baseAction": "accept",
                    "sequenceType": "route",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": []
                    },
                    "actions": [
                        {
                            "type": "set",
                            "parameter": [
                                {
                                    "field": "tlocList",
                                    "ref": pop_tloc_list_id
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        response = self.put_request(mount_point, payload)
        return response

    def get_top_policy(self, top_policy_id):
        """Get customized topology policy"""
        mount_point = 'template/policy/definition/control/' + top_policy_id
        response = self.get_request(mount_point)
        return response

    def delete_top_policy(self, top_policy_id):
        """Delete the customized topology policy"""
        mount_point = 'template/policy/definition/control/' + top_policy_id
        response = self.delete_request(mount_point)
        return response

    def chu_add_box_top_policy(self, top_name, pop_site_id, pop_tloc_list_id, all_box_id):
        """Customized add box top policy"""
        top_policy_id = ''
        response = self.list_top_policy()
        if response.status_code == 200:
            all_top_policy = response.json()['data']
        top_policy_existed = False
        for top_policy in all_top_policy:
            if top_policy['name'] == top_name:
                top_policy_id = top_policy['definitionId']
                response = self.edit_box_top_policy(top_name, pop_site_id, pop_tloc_list_id, top_policy_id, all_box_id)
                top_policy_existed = True
        if top_policy_existed == False:
            response = self.add_box_top_policy(top_name, pop_site_id, pop_tloc_list_id, all_box_id)
            if response.status_code == 200:
                top_policy_id = response.json()["definitionId"]
            else:
                print(response.status_code)

        response = self.get_top_policy(top_policy_id)
        top_policy = response.json()
        logging.debug('Box Topology list added:\n %s' % str(top_policy))

    def add_pop_top_policy(self, top_name, box_site_id):
        """Add customized topology policy"""
        mount_point = 'template/policy/definition/control'
        payload = {
            "name": top_name,
            "type": "control",
            "description": top_name[4:] + " POP OUT Topology Policy",
            "defaultAction": {
                "type": "reject"
            },
            "sequences": [
                {
                    "sequenceId": 1,
                    "sequenceName": "TLOC",
                    "baseAction": "accept",
                    "sequenceType": "tloc",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": [
                            {
                                "field": "siteList",
                                "ref": box_site_id
                            }
                        ]
                    },
                    "actions": []
                },
                {
                    "sequenceId": 11,
                    "sequenceName": "TLOC",
                    "baseAction": "reject",
                    "sequenceType": "tloc",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": []
                    },
                    "actions": []
                },
                {
                    "sequenceId": 21,
                    "sequenceName": "Route",
                    "baseAction": "accept",
                    "sequenceType": "route",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": []
                    },
                    "actions": []
                }
            ]
        }
        response = self.post_request(mount_point, payload)
        return response

    def edit_pop_top_policy(self, top_name, box_site_id, top_policy_id):
        """Edit customized topology policy"""
        mount_point = 'template/policy/definition/control/' + top_policy_id
        payload = {
            "name": top_name,
            "type": "control",
            "description": top_name[4:] + " POP OUT Topology Policy",
            "defaultAction": {
                "type": "reject"
            },
            "sequences": [
                {
                    "sequenceId": 1,
                    "sequenceName": "TLOC",
                    "baseAction": "accept",
                    "sequenceType": "tloc",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": [
                            {
                                "field": "siteList",
                                "ref": box_site_id
                            }
                        ]
                    },
                    "actions": []
                },
                {
                    "sequenceId": 11,
                    "sequenceName": "TLOC",
                    "baseAction": "reject",
                    "sequenceType": "tloc",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": []
                    },
                    "actions": []
                },
                {
                    "sequenceId": 21,
                    "sequenceName": "Route",
                    "baseAction": "accept",
                    "sequenceType": "route",
                    "sequenceIpType": "ipv4",
                    "match": {
                        "entries": []
                    },
                    "actions": []
                }
            ]
        }
        response = self.put_request(mount_point, payload)
        return response

    def chu_add_pop_top_policy(self, top_name, box_site_id):
        """Customized add box top policy"""
        top_policy_id = ''
        response = self.list_top_policy()
        if response.status_code == 200:
            all_top_policy = response.json()['data']
        top_policy_existed = False
        for top_policy in all_top_policy:
            if top_policy['name'] == top_name:
                top_policy_id = top_policy['definitionId']
                response = self.edit_pop_top_policy(top_name, box_site_id, top_policy_id)
                top_policy_existed = True
        if top_policy_existed == False:
            response = self.add_pop_top_policy(top_name, box_site_id)
            if response.status_code == 200:
                top_policy_id = response.json()["definitionId"]
            else:
                print(response.status_code)

        response = self.get_top_policy(top_policy_id)
        top_policy = response.json()
        logging.debug('POP Topology list added:\n %s' % str(top_policy))

    def chu_delete_top_policy(self, site_name_list):
        """Customized delete top policy"""
        response = self.list_top_policy()
        if response.status_code == 200:
            all_top_policy = response.json()['data']
        for top_policy in all_top_policy:
            if top_policy['name'][4:] in site_name_list:
                top_policy_id = top_policy['definitionId']
                response = self.delete_top_policy(top_policy_id)
        return response

    def list_vsmart_policy(self):
        """List vSmart Policy"""
        mount_point = 'template/policy/vsmart'
        response = self.get_request(mount_point)
        return response

    def add_vsmart_policy(self, policy_name, policy_data_pair):
        """Add vSmart Policy"""
        mount_point = 'template/policy/vsmart/'
        payload = {
            "policyDescription": policy_name,
            "policyType": "feature",
            "policyName": policy_name,
            "policyDefinition": {
                "assembly": []
            },
            "isPolicyActivated": False
        }

        for key1, value1 in policy_data_pair.items():
            policy_payload = {"definitionId": key1, "type": "control", "entries": []}
            for value2 in value1:
                site_list_payload = {
                    "direction": "out",
                    "siteLists": []
                }
                site_list_payload["siteLists"].append(value2)
            policy_payload["entries"].append(site_list_payload)
            payload["policyDefinition"]["assembly"].append(policy_payload)

        response = self.post_request(mount_point, payload)
        return response

    def edit_vsmart_policy(self, policy_name, policy_data_pair, vsmart_policy_id):
        """Edit vSmart Policy"""
        mount_point = 'template/policy/vsmart/' + vsmart_policy_id
        payload = {
            "policyDescription": policy_name,
            "policyType": "feature",
            "policyName": policy_name,
            "policyDefinition": {
                "assembly": []
            },
            "isPolicyActivated": False
        }

        for key1, value1 in policy_data_pair.items():
            policy_payload = {"definitionId": key1, "type": "control", "entries": []}
            for value2 in value1:
                site_list_payload = {
                    "direction": "out",
                    "siteLists": []
                }
                site_list_payload["siteLists"].append(value2)
            policy_payload["entries"].append(site_list_payload)
            payload["policyDefinition"]["assembly"].append(policy_payload)

        response = self.put_request(mount_point, payload)
        return response

    def get_vsmart_policy(self, vsmart_policy_id):
        """Get tloc list by tlocId"""
        mount_point = 'template/policy/vsmart/definition/' + vsmart_policy_id
        response = self.get_request(mount_point)
        return response

    def delete_vsmart_policy(self, vsmart_policy_id):
        """Delete the tloc list"""
        mount_point = 'template/policy/vsmart/' + vsmart_policy_id
        response = self.delete_request(mount_point)
        return response

    def chu_add_vsmart_policy(self, policy_name, policy_data_pair):
        """Customized add vSmart Policy"""
        vsmart_policy_id = ''
        response = self.list_vsmart_policy()
        if response.status_code == 200:
            all_vsmart_policy = response.json()['data']
        vsmart_policy_existed = False
        for vsmart_policy in all_vsmart_policy:
            if vsmart_policy['policyName'] == policy_name:
                vsmart_policy_id = vsmart_policy['policyId']
                response = self.edit_vsmart_policy(policy_name, policy_data_pair, vsmart_policy_id)
                vsmart_policy_existed = True
        if vsmart_policy_existed == False:
            response = self.add_vsmart_policy(policy_name, policy_data_pair)
            if response.status_code == 200:
                time.sleep(1)
                response = self.list_vsmart_policy()
                all_vsmart_policy = response.json()['data']
                for vsmart_policy in all_vsmart_policy:
                    if vsmart_policy['policyName'] == policy_name:
                        vsmart_policy_id = vsmart_policy['policyId']
            else:
                print(response.status_code)

        response = self.get_vsmart_policy(vsmart_policy_id)

        vsmart_policy = response.json()
        logging.debug('vsmart policy added:\n %s' % str(vsmart_policy))

    def chu_delete_vsmart_policy(self, vsmart_policy_name):
        """Customized delete vSmart Policy"""
        response = self.list_vsmart_policy()
        if response.status_code == 200:
            all_vsmart_policy = response.json()['data']
        for vsmart_policy in all_vsmart_policy:
            if vsmart_policy['policyName'] == vsmart_policy_name:
                vsmart_policy_id = vsmart_policy['policyId']
                response = self.delete_vsmart_policy(vsmart_policy_id)
        return response

    def query_device_int_statistics(self, device_system_ip_list):
        """Query device interface statistics"""
        mount_point = 'statistics/interface/aggregation'
        payload = {
          "query": {
            "condition": "AND",
            "rules": [
              {
                "value": [
                  "1"
                ],
                "field": "entry_time",
                "type": "date",
                "operator": "last_n_hours"
              },
              {
                "value": device_system_ip_list,
                "field": "vdevice_name",
                "type": "string",
                "operator": "in"
              }
            ]
          },
          "sort": [
            {
              "field": "entry_time",
              "type": "date",
              "order": "asc"
            }
          ],
          "aggregation": {
            "field": [
              {
                "property": "interface",
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
              "interval": 10,
              "order": "asc"
            },
            "metrics": [
              {
                "property": "rx_kbps",
                "type": "avg"
              },
              {
                "property": "tx_kbps",
                "type": "avg"
              },
              {
                "property": "rx_octets",
                "type": "sum"
              },
              {
                "property": "tx_octets",
                "type": "sum"
              }
            ]
          }
        }
        response = self.post_request(mount_point, payload)
        return response

    def query_all_int_statistics(self):
        """Query device interface statistics"""
        mount_point = 'statistics/interface/aggregation'
        payload = {
          "query": {
            "condition": "AND",
            "rules": [
              {
                "value": [
                  "1"
                ],
                "field": "entry_time",
                "type": "date",
                "operator": "last_n_hours"
              }
            ]
          },
          "sort": [
            {
              "field": "entry_time",
              "type": "date",
              "order": "asc"
            }
          ],
          "aggregation": {
            "field": [
              {
                "property": "interface",
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
              "interval": 10,
              "order": "asc"
            },
            "metrics": [
              {
                "property": "rx_kbps",
                "type": "avg"
              },
              {
                "property": "tx_kbps",
                "type": "avg"
              },
              {
                "property": "rx_octets",
                "type": "sum"
              },
              {
                "property": "tx_octets",
                "type": "sum"
              }
            ]
          }
        }
        response = self.post_request(mount_point, payload)
        return response

def set_env():
    helpmsg = """Please choose the server you want to connect."""
    print(helpmsg)
    for server in sdwan_env.server_list:
        print('({index})\t{server_name}'.format(
            index=sdwan_env.server_list.index(server),
            server_name=server['server_name']))

    server_choice = input("Choose your server:")
    server_choice = int(server_choice)

    server_info = sdwan_env.server_list[server_choice]

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

    with open("current_env.json", "w") as file_obj:
        json.dump(server_info, file_obj)
        print("Set env to {name}\nHostname: {hostname}".format(
            name=server_info['server_name'],
            hostname=server_info['hostname']))

def show_env(SDWAN_SERVER, SDWAN_IP, TENANT):
    print("The current environment are:")
    print("Server name: {}".format(SDWAN_SERVER))
    print("Hostname: {}".format(SDWAN_IP))
    print("Tenant: {}".format(TENANT))

def convert_site_list(site_number):
    """Convert site number to site_list"""
    site_list = []
    # list1 = site_number + '000000-' + site_number + '999999'
    list2 = site_number + '0000000-' + site_number + '9999999'
    # site_list.append(list1)
    site_list.append(list2)
    return site_list
