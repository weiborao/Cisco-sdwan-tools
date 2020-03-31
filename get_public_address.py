# -*- coding: utf-8 -*-

import json
import sys
from rest_api_lib import *
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import logging

logging.basicConfig(level=logging.WARNING, format=' %(asctime)s - %(levelname)s - %(message)s')
# logging.disable(logging.CRITICAL)
logging.debug("Start of program")

if __name__ == "__main__":
    help_msg = '''\nUsage: 
            选择vManage Server和Tenant
            python3 get_public_address.py set env 

            查看当前的vManage Server和Tenant
            python3 get_public_address.py show env 

            测试：
            pyhthon3 get_public_address.py pub add\n'''

    if len(sys.argv) < 3:
        print(help_msg)
        sys.exit(0)
    else:
        action = sys.argv[1]
        target_obj = sys.argv[2]

        current_env = 'current_env.json'

        try:
            with open(current_env, 'r') as f_obj:
                server_info = json.load(f_obj)

        # 如果文件不存在
        except FileNotFoundError:
            msg = "Sorry, the file " + current_env + " does not exist.\n"
            print(msg)
            set_env()
            with open(current_env, 'r') as f_obj:
                server_info = json.load(f_obj)

        SDWAN_SERVER = server_info['server_name']
        SDWAN_IP = server_info['hostname']
        SDWAN_PORT = server_info['port']
        SDWAN_USERNAME = server_info['username']
        SDWAN_PASSWORD = server_info['password']
        if server_info['tenant'] != 'single_tenant_mode':
            TENANT = server_info['tenant'][0]['name']
        else:
            TENANT = 'single_tenant_mode'

        del server_info
        logging.debug("Current environment is : server\t{}\ttenant\t{}".format(SDWAN_IP, TENANT))

        if action in ["pub"]:

            sdwanp = rest_api(
                vmanage_ip=SDWAN_IP,
                port=SDWAN_PORT,
                username=SDWAN_USERNAME,
                password=SDWAN_PASSWORD,
                tenant=TENANT)
            del SDWAN_PASSWORD
            if TENANT != "single_tenant_mode":
                sdwanp.set_tenant(TENANT)

            if action == 'pub' and target_obj == 'add':
                response = sdwanp.list_all_device()
                device_list_data = response.json()['data']
                # print(device_list_data)
                device_list = []
                for device in device_list_data:
                    device_list.append(device['deviceId'])
                mount_point = 'device/control/waninterface'
                pub_add_list = []
                for device in device_list:
                    params='deviceId='+device
                    response = sdwanp.get_request(mount_point, params)
                    if response.status_code == 200:
                        response_data = response.json()['data']
                        pub_add = {}
                        pub_add['host-name'] = ''
                        pub_add['public_ip'] = ''
                        for data in response_data:
                            pub_add['host-name'] = data['vdevice-host-name']
                            pub_add['public_ip'] = data['public-ip']
                            pub_add_list.append(pub_add)
                for pub_add in pub_add_list:
                    print(pub_add['host-name']+'\t'+pub_add['public_ip'])
                sys.exit(0)

        elif action == 'set' and target_obj == 'env':
            server_info = None
            set_env()
            sys.exit(0)

        elif action == 'show' and target_obj == 'env':
            show_env(SDWAN_SERVER, SDWAN_IP, TENANT)
            sys.exit(0)

        else:
            print("""输入参数不正确""")
            print(help_msg)

logging.debug("End of program")