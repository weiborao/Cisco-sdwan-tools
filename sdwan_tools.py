# -*- coding: utf-8 -*-

import json
import sys
from rest_api_lib import *
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

if __name__ == "__main__":
    help_msg = '''\nUsage: 
            导出设备配置，存成json文件
            python3 sdwan_tools.py get device_sn 
            例如：python3 sdwan_tools.py get 1920C539181628S

            修改json文件以后，再运行:
            python3 sdwan_tools.py push device_sn 将新的配置推送给vManage
            例如：python3 sdwan_tools.py push 1920C539181628S

            选择vmanage和租户
            python3 sdwan_tools.py set env 
            
            单租户测试：
            pyhthon3 sdwan_tools.py dpi info
            \n'''

    if len(sys.argv) < 3:
        print(help_msg)
        sys.exit(0)
    else:
        action = sys.argv[1]
        device_sn = sys.argv[2]

        server_info_book = 'server_info.json'

        try:
            with open(server_info_book, 'r') as f_obj:
                server_info = json.load(f_obj)

        # 如果文件不存在
        except FileNotFoundError:
            msg = "Sorry, the file " + server_info_book + " does not exist.\n"
            print(msg)
            set_env()
            with open(server_info_book, 'r') as f_obj:
                server_info = json.load(f_obj)

        # print(dir(server_info), '\n', server_info)
        SDWAN_IP = server_info['hostname']
        SDWAN_PORT = server_info['port']
        SDWAN_USERNAME = server_info['username']
        SDWAN_PASSWORD = server_info['password']
        if server_info['tenant'] != 'single_tenant_mode':
            TENANT_ID = server_info['tenant'][0]['id']
            TENANT = server_info['tenant'][0]['name']
        else:
            TENANT_ID = None
            TENANT = None

        if action == 'get' or action == 'push' or action == 'dpi':

            sdwanp = rest_api(
                vmanage_ip=SDWAN_IP,
                port=SDWAN_PORT,
                username=SDWAN_USERNAME,
                password=SDWAN_PASSWORD,
                tenant=TENANT,
                tenant_id=TENANT_ID)
            if TENANT_ID != None:
                sdwanp.set_tenant(TENANT)
                # sdwanp.post_vsession(TENANT_ID)

            if action == 'dpi':
                response = sdwanp.query_dpi('6')
                print(response.json()['data'])
                sys.exit(0)

            device_info = sdwanp.get_device_info(device_sn).json()
            templateId=device_info['data'][0]['templateId']
            if action == 'get':
                response = sdwanp.get_device_config(uuid=device_sn, templateId=templateId)
                # logout = sdwanp.vmanage_logout()
                sys.exit(0)
            if action == 'push':
                push_cli_response = sdwanp.push_cli_config(uuid=device_sn, templateId=templateId)
                job_id = push_cli_response.json()
                print(job_id)
                # print('DEBUG: push cli config response: ', response.text)
                job_status = sdwanp.check_job(job_id).json()
                print('Job summary', '='*10, '\n Job Status: {status}'.format(
                status = job_status['data'][0]['status']))
                print('Job activies:')
                for item in job_status['data'][0]['activity']:
                    print(item)
                # logout = sdwanp.vmanage_logout()
                sys.exit(0)

        elif action == 'set' and device_sn == 'env':
            server_info = None
            set_env()
            sys.exit(0)
        else:
            print("""输入参数不正确""")
            print(help_msg)
