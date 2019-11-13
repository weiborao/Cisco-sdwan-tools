# Cisco-sdwan-config-tool

## 1. What does the tool do?

- This SDWAN tool help user to quickly export device config data to a .json file. And user can edit it by text editor, and then push the config back to vManage;

- This tool can get and push the devices with CLI templates as well as Feature templates;

- This tool supports single tenant vManage as well as Multi-tenant vManage.

## 2. How to Run the Script?

**Prerequirment**: please install requests module.
```
%pip install requests
%git clone https://github.com/weiborao/Cisco-sdwan-tools
%cd Cisco-sdwan-tools/
```

### (1) Setup the environment
1. Please rename the _sdwan_env_sample.py_ to _sdwan_env.py_.
And edit the server information.

```python

# -*- coding: utf-8 -*-

server_list = [
    {
        "server_name": "chusdwan",
        "hostname": "180.37.12.38",
        "port": 443,
        "username": "admin",
        "password": "xd13ddcdd",
        "tenant": [
            {
                "name": "T1"
            },
            {
                "name": "T2"
            },
            {
                "name": "T3"
            }]
    },
    {
        "server_name": "dcloudrtp",
        "hostname": "dcloud-sdwan-inst-rtp.cisco.com",
        "port": 443,
        "username": "admin",
        "password": "sxddwedd",
        "tenant": "single_tenant_mode"
    }
]
```

2. You need to set the environment by running _python3 sdwan_tools.py set env

```
Cisco-sdwan-tools % python sdwan_tools.py set env
Please choose the server you want to connect.
(0) chusdwan
(1) dcloudrtp
Choose your server:**0**
Please choose the tenant.
(0) T1
(1) T2
(2) T3
Choose your tenant:**0**
Set env to chusdwan
Hostname: 180.37.12.38
```

3. You can check the current env by running _python3 sdwan_tools.py show env
```
The current environment are:
Server name: chusdwan
Hostname: 180.37.12.38
Tenant: T1
```

### (2) Export, Edit and Push the Config back
4. Export the json data of the CLI config from vManage by running python3 sdwan_tools get device_sn
For example: 
`Cisco-sdwan-tools % python3 sdwan_tools.py get 1920C539181628S`

Please make sure you input the right SN, as the script does not handle input errors.

The json data will be written to file 1920C539181628S.json
```json
{
  "csv-status": "complete",
  "csv-deviceId": "1920C539181628S",
  "csv-deviceIP": "100.98.0.14",
  "csv-host-name": "XXXX-LAB",
  "host-name": "XXXXLAB-F4-TEST",
  "system-ip-address": "100.98.0.14",
  "siteid": "202946001",
  "organization-name": "\"XXXX SDWAN T1\"",
  "vbond-address": "X.X.X.X",
  "controller-name": "\"XXXX\"",
  "admin-name": "admin",
  "admin-password": "XXXX",
  "cellular": "\nomp\n no shutdown\n graceful-restart\n advertise connected\n advertise static",
  "WAN_Port_Name": "ge0/4",
  "WAN_TYPE_INFO": "\nshaping-rate 2048\nip address 10.43.11.11/24\n  tunnel-interface\n   encapsulation ipsec\n   no allow-service bgp\n   allow-service dhcp\n   allow-service dns\n   allow-service icmp\n   no allow-service sshd\n   no allow-service netconf\n   no allow-service ntp\n   no allow-service ospf\n   no allow-service stun\n  !\n  no shutdown\n  !\n  ip route 0.0.0.0/0  10.43.11.1\n !",
  "cellular_interface": "",
  "VPN1": "\nvpn 100\n interface ge0/2\n  ip address 100.77.1.1/28\n  no   shutdown\n !\n",
  "VPN2": "!",
  "VPN3": "!",
  "VPN4": "!"
}
```

Then you can edit it.

Here is a script to help you to convert the multi-line texts to the requried data format.
```python
multilin_str = '''vpn 0
 dns 114.114.114.114 primary
 interface ge0/4
  ip dhcp-client
  pppoe-client ppp-interface ppp1
  no shutdown
 !
 interface ppp1
  ppp authentication chap
   hostname 86152074
   password xxxxx
  !
  tunnel-interface
   encapsulation ipsec
   color biz-internet restrict
   no allow-service bgp
   allow-service dhcp
   allow-service dns
   allow-service icmp
   no allow-service sshd
   no allow-service netconf
   no allow-service ntp
   no allow-service ospf
   no allow-service stun
   allow-service https
  !
  mtu      1492
  no shutdown
 !
!
'''
str_list = multilin_str.splitlines()

for string in str_list:
    print(string, end='\\n')
```

The output will be:
> vpn 0\n dns 114.114.114.114 primary\n interface ge0/4\n  ip dhcp-client\n  pppoe-client ppp-interface ppp1\n  no shutdown\n !\n interface ppp1\n  ppp authentication chap\n   hostname 86152074\n   password xxxxx\n  !\n  tunnel-interface\n   encapsulation ipsec\n   color biz-internet restrict\n   no allow-service bgp\n   allow-service dhcp\n   allow-service dns\n   allow-service icmp\n   no allow-service sshd\n   no allow-service netconf\n   no allow-service ntp\n   no allow-service ospf\n   no allow-service stun\n   allow-service https\n  !\n  mtu      1492\n  no shutdown\n !\n!\n

5. Push the json data to vManage by running python3 sdwan_tools push device_sn
`Cisco-sdwan-tools % python3 sdwan_tools.py push 1920C539181628S`

```python
....Output omitted
  vpn 0
   interface ge0/4
    ip address 10.43.11.11/24
    tunnel-interface
     encapsulation ipsec
     no allow-service bgp
     allow-service dhcp
     allow-service dns
     allow-service icmp
     no allow-service sshd
     no allow-service netconf
     no allow-service ntp
     no allow-service ospf
     no allow-service stun
     allow-service https
    !
    no shutdown
    shaping-rate 2048
   !
   ip route 0.0.0.0/0 10.43.11.1
  !
  vpn 100
   interface ge0/2
    ip address 100.77.1.1/28
    no shutdown
   !
  !
  vpn 512
   interface ge0/0
    ip address 192.168.254.1/24
    no shutdown
   !
  !
  policy
   app-visibility
   flow-visibility
  !
 !
!

Please check and confirm the configuration...(y/n):y

```
It will return the job_id and track the job status.

sample output:
```
Job summary ==========
 Job Status: Success
Job activies:
[12-Nov-2019 22:13:35 CST] Configuring device with cli template: Box
[12-Nov-2019 22:13:35 CST] Generating configuration from template
[12-Nov-2019 22:13:35 CST] Checking and creating device in vManage
[12-Nov-2019 22:13:37 CST] Device is online
[12-Nov-2019 22:13:37 CST] Updating device configuration in vManage
[12-Nov-2019 22:13:38 CST] Pushing configuration to device
[12-Nov-2019 22:13:55 CST] Template successfully attached to device
```

### (3) Other small tools:
6. show run function. python3 sdwan_tools show_run device_sn
You can quickly get the running config and save to files.
`Cisco-sdwan-tools % python sdwan_tools.py show_run 1920C539181628S`
```
...Output omitted...
omp
 no shutdown
 graceful-restart
 advertise connected
 advertise static
!
vpn 0
 interface ge0/4
  ip address 10.43.11.11/24
  tunnel-interface
   encapsulation ipsec
   no allow-service bgp
   allow-service dhcp
   allow-service dns
   allow-service icmp
   no allow-service sshd
   no allow-service netconf
   no allow-service ntp
   no allow-service ospf
   no allow-service stun
   allow-service https
  !
  no shutdown
  shaping-rate 2048
 !
 ip route 0.0.0.0/0 10.43.11.1
!
vpn 100
 interface ge0/2
  ip address 100.77.1.1/28
  no shutdown
 !
!
vpn 512
 interface ge0/0
  ip address 192.168.254.1/24
  no shutdown
 !
!
policy
 app-visibility
 flow-visibility
!
```

7. Get DPI aggregated info.
This is just for fun.
`python3 sdwan_tools.py dpi info`

```
[{'entry_time': 1573551900000, 'count': 3, 'family': 'mail', 'vdevice_name': '1.1.74.35', 'octets': 675}, {'entry_time': 1573551900000, 'count': 1, 'family': 'tunneling', 'vdevice_name': '100.110.0.25', 'octets': 3666}, {'entry_time': 1573551600000, 'count': 236, 'family': 'network-service', 'vdevice_name': '100.110.0.25', 'octets': 21096}, {'entry_time': 1573551600000, 'count': 123, 'family': 'network-service', 'vdevice_name': '1.1.74.3', 'octets': 21039}, {'entry_time': 1573551600000, 'count': 80, 'family': 'network-service', 'vdevice_name': '100.88.0.50', 'octets': 13874}, {'entry_time': 1573551600000, 'count': 26, 'family': 'network-service', 'vdevice_name': '1.1.74.35', 'octets': 12223}, {'entry_time': 1573551600000, 'count': 12, 'family': 'network-service', 'vdevice_name': '100.117.0.27', 'octets': 1642}, {'entry_time': 1573551600000, 'count': 26, 'family': 'network-service', 'vdevice_name': '1.1.74.163', 'octets': 1606}, {'entry_time': 1573551600000, 'count': 7, 'family': 'network-service', 'vdevice_name': '1.1.74.131', 'octets': 412}, {'entry_time': 1573551600000, 'count': 40, 'family': 'web', 'vdevice_name': '100.88.0.50', 'octets': 1274630}, {'entry_time': 1573551600000, 'count': 60, 'family': 'web', 'vdevice_name': '100.117.0.27', 'octets': 1049143}, {'entry_time': 1573551600000, 'count': 47, 'family': 'web', 'vdevice_name': '1.1.74.3', 'octets': 905876}, {'entry_time': 1573551600000, 'count': 40, 'family': 'web', 'vdevice_name': '1.1.74.35', 'octets': 415718}, {'entry_time': 1573551600000, 'count': 6, 'family': 'web', 'vdevice_name': '100.110.0.25', 'octets': 7460}, {'entry_time': 1573551600000, 'count': 1, 'family': 'web', 'vdevice_name': '1.1.74.163', 'octets': 516}, {'entry_time': 1573551600000, 'count': 1, 'family': 'standard', 'vdevice_name': '100.110.0.25', 'octets': 245509}, {'entry_time': 1573551600000, 'count': 46, 'family': 'standard', 'vdevice_name': '100.117.0.27', 'octets': 47940}, {'entry_time': 1573551600000, 'count': 6, 'family': 'standard', 'vdevice_name': '100.88.0.50', 'octets': 3167}, {'entry_time': 1573551600000, 'count': 2, 'family': 'mail', 'vdevice_name': '100.88.0.50', 'octets': 862}, {'entry_time': 1573551600000, 'count': 1, 'family': 'tunneling', 'vdevice_name': '100.117.0.27', 'octets': 7760}]
```
## 4. Caveats 
This tool's task is spesific, maily uses the requests module to do the job.
It requires user to input the right information, such as hostname, username, password and device_sn.

## 5. Questions and Contact Info

If you have any issues or a pull request, you can submit a Issue or contact me directly。

My Cisco CEC ID is: werao

## 6. License
This project is licensed to you under the terms of the [Cisco Sample Code License](LICENSE).

## 7. Acknowledgments

* Getting Started with Cisco SD-WAN REST APIs
  - `git clone https://github.com/ai-devnet/Getting-started-with-Cisco-SD-WAN-REST-APIs.git`
* Cisco SD-WAN EXIM (Export and Import)
  - `git clone https://github.com/CiscoSE/cisco-sd-wan-export-import`
