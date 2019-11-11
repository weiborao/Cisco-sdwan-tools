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
            python3 sdwan_tools.py set env 
            
            获取设备当前配置文件
            python3 sdwan_tools.py show_run device_sn
            例如：python3 sdwan_tools.py show_run 1920C539181628S
            
            导出设备配置，存成json文件
            python3 sdwan_tools.py get device_sn 
            例如：python3 sdwan_tools.py get 1920C539181628S

            修改json文件以后，再运行:
            python3 sdwan_tools.py push device_sn 将新的配置推送给vManage
            例如：python3 sdwan_tools.py push 1920C539181628S
            
            查看当前的vManage Server和Tenant
            python3 sdwan_tools.py show env 

            单租户测试：
            pyhthon3 sdwan_tools.py dpi info\n'''

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

        logging.debug("Current environment is : server\t{}\ttenant\t{}".format(SDWAN_IP, TENANT))

        if action in ["get", "show_run", "push", "dpi"]:

            sdwanp = rest_api(
                vmanage_ip=SDWAN_IP,
                port=SDWAN_PORT,
                username=SDWAN_USERNAME,
                password=SDWAN_PASSWORD,
                tenant=TENANT)
            if TENANT != "single_tenant_mode":
                sdwanp.set_tenant(TENANT)

            if action == 'dpi' and target_obj == 'info':
                response = sdwanp.query_dpi('6')
                print(response.json()['data'])
                sys.exit(0)

            device_info = sdwanp.get_device_info(target_obj).json()
            templateId=device_info['data'][0]['templateId']
            if action == 'show_run':
                response = sdwanp.get_device_running(uuid=target_obj)
                if data.get('config') and len(data.get('config')) > 0:
                    running_config = response.json()['config']
                    with open(target_obj + ".txt", 'w') as file_obj:
                        file_obj.write(running_config)
                    print(running_config)
                elif data.get('error') and len(data.get('error')) > 0:
                    err_msg = response.json()['error']['detail']
                    print(err_msg)
                sys.exit(0)

            if action == 'get':
                response = sdwanp.get_device_cli_data(uuid=target_obj, templateId=templateId)
                # logout = sdwanp.vmanage_logout()
                sys.exit(0)
            if action == 'push':
                template_type = sdwanp.get_template_type(templateId)
                preview_config = sdwanp.preview_config(uuid=target_obj, templateId=templateId)
                print(preview_config.text)
                ready_to_go = input("Please check and confirm the configuration...(y/n):")
                loop_control = 1
                while loop_control == 1:
                    if ready_to_go == 'y':
                        if template_type == 'file':
                            push_cli_response = sdwanp.push_cli_config(uuid=target_obj, templateId=templateId)
                            job_id = push_cli_response.json()
                        elif template_type == 'template':
                            push_template_response = sdwanp.push_template_config(uuid=target_obj, templateId=templateId)
                            job_id = push_template_response.json()
                        loop_control = 0
                    elif ready_to_go == 'n':
                        print("Job canceled...Exit")
                        sys.exit(0)
                    else:
                        print("Please input y or n.")
                        ready_to_go = input("Please check and confirm the configuration...(y/n):")

                job_status = sdwanp.check_job(job_id).json()
                print('Job summary', '='*10, '\n Job Status: {status}'.format(
                status = job_status['data'][0]['status']))
                print('Job activies:')
                for item in job_status['data'][0]['activity']:
                    print(item)
                # logout = sdwanp.vmanage_logout()
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