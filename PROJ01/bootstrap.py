import requests
import json
from netmiko import ConnectHandler, file_transfer, progress_bar

requests.packages.urllib3.disable_warnings()
#disable InsecureRequestWarning for the Unverified HTTPS request - because we 'verify=False' in the request

USERNAME="admin"
PASSWORD="pocadmin"

login_url = 'https://vmanage.dcloud.cisco.com:8443/j_security_check'
login_data = {'j_username' : USERNAME, 'j_password' : PASSWORD}
response = requests.post(url=login_url, data=login_data, verify=False)
if response.content != b'':
    print ("Authentication fail!")
    exit()
token1='JSESSIONID='+response.cookies.get_dict()['JSESSIONID']
print ('token1=',token1)
token_url='https://vmanage.dcloud.cisco.com:8443/dataservice/client/token'
headers = {'Cookie': token1,'content-type':'application/json'}
response = requests.get(url=token_url, headers=headers, verify=False)
token2=response.text
print ('token2=',token2)

url = "https://vmanage.dcloud.cisco.com:8443/dataservice/system/device/bootstrap/device/C8K-11E7C6ED-39EA-AABF-7829-5D02B848D302?configtype=cloudinit&inclDefRootCert=false&version=v1"

payload = {}
headers = {'Content-Type': "application/json",'Cookie': token1, 'X-XSRF-TOKEN': token2}

# Disable SSL verification
response = requests.get(url, headers=headers, data=payload, verify=False)

# Check if the response status code is OK
if response.status_code == 200:
    # Parse the JSON response content
    json_data = response.json()

    # Access the "bootstrapConfig" key and save it to a file
    bootstrap_config = json_data.get("bootstrapConfig", "")

    with open('ciscosdwan_cloud_init.cfg', 'w') as file:
        file.write(bootstrap_config)
else:
    print(f"Request failed with status code: {response.status_code}")

# Step 3: SCP the file to the router
csr = {
    "device_type": "cisco_ios",
    "host": "192.168.174.196",
    "username": "admin",
    "password": "admin",
    "session_log": "session.log"
}

net_connect = ConnectHandler(**csr)
print ("Connected Successfully")

transfer = file_transfer(net_connect, source_file="ciscosdwan_cloud_init.cfg",dest_file="ciscosdwan_cloud_init.cfg",file_system="bootflash:",direction="put",overwrite_file=True)
print(transfer)
net_connect.send_command("controller-mode enable", expect_string="confirm")
net_connect.send_command(
    command_string="\n",
    expect_string=r"confirm",
    strip_prompt=False,
    strip_command=False)
net_connect.disconnect()