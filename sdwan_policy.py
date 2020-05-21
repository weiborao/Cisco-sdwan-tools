# -*- coding: utf-8 -*-

import json
import sys
import logging
from rest_api_lib import rest_api, set_env, show_env, convert_site_list
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.WARNING,
                    format=' %(asctime)s - %(levelname)s - %(message)s')
# logging.disable(logging.CRITICAL)
logging.debug("Start of program")

SITE_DATA = 'site_data.json'

if __name__ == "__main__":
    help_msg = '''\nUsage: 
            选择vManage Server和Tenant
            python3 sdwan_tools.py set env 
            
            将所需配置的策略添加到vManage
            python3 sdwan_tools.py policy add
            \n'''
    # if True:
    if len(sys.argv) < 3:
        print(help_msg)
        sys.exit(0)
    else:
        action = sys.argv[1]
        target_obj = sys.argv[2]

        # action = "policy"
        # target_obj = "test"

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

        logging.debug(
            "Current environment is : server\t{}\ttenant\t{}".format(SDWAN_IP, TENANT))

        try:
            with open(SITE_DATA, 'r') as f_obj:
                site_data = json.load(f_obj)

        # 如果文件不存在
        except FileNotFoundError:
            msg = "Sorry, the file " + SITE_DATA + " does not exist.\n"
            sys.exit(1)

        site_to_add_list = site_data['NEW_SITES_TO_ADD']
        site_name_list = []

        for site in site_to_add_list:
            site_name_list.append(site["site"])

        logging.debug("Site list are: {}".format(str(site_name_list)))

        if action in ["get", "show_run", "push", "dpi", "policy"]:

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

            if action == 'policy' and target_obj == 'add':
                # Add site list
                for site_to_add in site_to_add_list:
                    box_site_name = "BOX_" + site_to_add["site"]
                    site_number = site_to_add["site_number"]
                    box_site_list = convert_site_list(site_number)
                    pop_site_name = "POP_" + site_to_add["site"]
                    pop_site_list = [site_to_add["POP_siteId"]]
                    sdwanp.chu_add_site_list(box_site_name, box_site_list)
                    sdwanp.chu_add_site_list(pop_site_name, pop_site_list)

                # Add TLOC list
                for site_to_add in site_to_add_list:
                    tloc_name = site_to_add["site"] + "_Front"
                    tloc_ip_list = ["1.1.{}.1".format(site_to_add["site_number"]),
                                    "1.1.{}.2".format(site_to_add["site_number"])]
                    sdwanp.chu_add_tloc_list(tloc_name, tloc_ip_list)

                # Add Topology policy
                response = sdwanp.list_site_list()
                site_list_data = {}
                if response.status_code == 200:
                    all_site = response.json()['data']
                for site in all_site:
                    # if site['name'][4:] in site_name_list:
                    site_list_data[site["name"]] = site["listId"]

                logging.debug('*' * 10 + 'Site List \n %s' %
                              str(site_list_data))

                response = sdwanp.list_tloc_list()
                tloc_list_data = {}
                if response.status_code == 200:
                    all_tloc = response.json()['data']
                for tloc in all_tloc:
                    tloc_list_data[tloc["name"]] = tloc["listId"]

                logging.debug('*' * 10 + 'TLOC List \n %s' %
                              str(tloc_list_data))

                # ADD BOX Topology Policy
                # Need top_name, pop_site_id, pop_tloc_list_id, top_policy_id, all_box_id
                for site_to_add in site_to_add_list:
                    top_name = "BOX_" + site_to_add["site"]
                    pop_site_name = "POP_" + site_to_add["site"]
                    pop_site_id = site_list_data[pop_site_name]
                    pop_tloc_name = site_to_add["site"] + "_Front"
                    pop_tloc_list_id = tloc_list_data[pop_tloc_name]
                    all_box_id = sdwanp.get_site_id_by_name("BOX_ALL")
                    logging.debug('*' * 10 + 'BOX_ALL \n %s' % str(all_box_id))

                    sdwanp.chu_add_box_top_policy(
                        top_name, pop_site_id, pop_tloc_list_id, all_box_id)

                # ADD POP Topology Policy
                # Need top_name, box_site_id
                for site_to_add in site_to_add_list:
                    top_name = "POP_" + site_to_add["site"]
                    box_site_name = "BOX_" + site_to_add["site"]
                    box_site_id = site_list_data[box_site_name]
                    sdwanp.chu_add_pop_top_policy(top_name, box_site_id)

                # Get the Topology List:
                response = sdwanp.list_top_policy()
                top_list_data = {}
                if response.status_code == 200:
                    all_top_data = response.json()['data']
                for top_data in all_top_data:
                    top_list_data[top_data["name"]] = top_data["definitionId"]

                logging.debug('*' * 10 + 'Topology Policy Data \n %s' %
                              str(top_list_data))

                # Assemble the policy
                policy_data_pair = {}
                for key1, value1 in top_list_data.items():
                    temp_site = []
                    for key2, value2 in site_list_data.items():
                        if key2 == key1:
                            temp_site.append(value2)
                    if temp_site != []:
                        policy_data_pair[value1] = temp_site

                del key1, value1, temp_site, key2, value2
                logging.debug('*' * 10 + 'Policy Data \n %s' %
                              str(policy_data_pair))

                # Create vSmart policy
                vsmart_policy_name = "Custmized_HUB_SPOKE"
                sdwanp.chu_add_vsmart_policy(
                    vsmart_policy_name, policy_data_pair)

            if action == 'policy' and target_obj == 'clear':
                # Delete vSmart Policy
                vsmart_policy_name = "Custmized_HUB_SPOKE"
                sdwanp.chu_delete_vsmart_policy(vsmart_policy_name)
                sdwanp.chu_delete_top_policy(site_name_list)
                sdwanp.chu_delete_tloc_list(site_name_list)
                sdwanp.chu_delete_site_list(site_name_list)

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
