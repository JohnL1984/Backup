from netmiko import ConnectHandler
from getpass import getpass
import threading
import sys

class rename (threading.Thread):
    def __init__(self, device):
        threading.Thread.__init__(self)
        self.device = device
    def run(self):
        switch = self.device.split(",")
        platform = switch[2]
        host = switch[1]
        switchName = switch[0]
        device = ConnectHandler(device_type=platform, ip=host, username=username, password=password)
        for vlanId, vlanName in vlans.items():
            print('Renaming VLAN %s, name %s, on %s: '%(vlanId, vlanName, switchName))
            config_commands = ['vlan ' + str(vlanId), 'name ' + str(vlanName)]
            output = device.send_config_set(config_commands)
        
        config_commands = ['copy run start']
        print("VLAN/s successfully renamed - Saving config on %s"%(switchName))


if __name__ == '__main__':
    envList = {1:"SiteA", 2:"SiteB", 3:"SiteC"}
    inputString = ""
    for key, value in envList.items():
        inputString += "%s (%s) - "%(value, key)
    inputString += "Enter a number: "
    envNr = input(inputString)
    while not envNr.isdigit() or int(envNr) not in envList:
        envNr = input(inputString)
    envNr = int(envNr)

    print ("VLAN rename on %s"%(envList(envNr)))

    username = input("Username: ")
    password = getpass()
    vlan_string = input("List the VLANs separated by a comma e.g. 3,6,7: ")
    vlan_string = vlan_string.replace(" ", "")
    vlan_list = vlan_string.split(",")

    vlans = {}
    for vlan in vlan_list:
        vlan_name = input("Input name for vlan %s"%(vlan))
        while (envList[envNr] != vlan_name[0:3]) or  len(vlan_name) >20 or vlan_name[6] != "_":
            vlan_name = input("Check vlan name meets naming convention and re-enter name for vlan %s: "%(vlan))
        vlan_name_edit = vlanname.replace(" ", "")
        vlans[int(vlan)] = vlan_name_edit
    
    answer = input("Type (y) to proceed with VLAN rename: ")
    if answer != "y":
        sys.exit(0)

    with open ("%s.txt"%(envList[envNr].lower())) as f:
        device_list = f.read().splitlines()

    for device in device_list:
        rename(device).start()