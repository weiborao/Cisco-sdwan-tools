# Cisco-sdwan-tools

## What does the script do?

This SDWAN tool help user to quickly export device config data to a .json file. 
And user can edit it by text editor, and then push the config back to vManage.

Currently, this tool can only get and push the devices with CLI templates.

## How to Run the Script?

**Prerequirment**: please install requests module.
pip install requests

(1) please rename the _sdwan_env_sample.py_ to _sdwan_env.py_.
And edit the server information.

如果你认识中文，请直接运行 python3 sdwan_tools.py

(2) You need to set the environment by running _python3 sdwan_tools.py set env_
Please choose the server you want to connect.

(3) You can check the current env by running _python3 sdwan_tools.py show env_

(4) Export the json data of the CLI config from vManage by running python3 sdwan_tools get `device_sn`
For example: python3 sdwan_tools get 1920C539181628S
Please make sure you input the right SN, as the script does not handle input errors.

The json data will be written to file 1920C539181628S.json
Then you can edit it.

(5) Push the json data to vManage by running python3 sdwan_tools pus `device_sn`
python3 sdwan_tools.py push 1920C539181628S
It will return the job_id and track the job status.
sample output:
Job summary ==========
 Job Status: Success
Job activies:
[1-Nov-2019 10:58:37 CST] Configuring device with cli template: Box
[1-Nov-2019 10:58:37 CST] Generating configuration from template
[1-Nov-2019 10:58:37 CST] Checking and creating device in vManage
[1-Nov-2019 10:58:39 CST] Device is online
[1-Nov-2019 10:58:39 CST] Updating device configuration in vManage
[1-Nov-2019 10:58:40 CST] Pushing configuration to device
[1-Nov-2019 10:58:49 CST] Template successfully attached to device
