#!bin/python
#version 3.0.1
from netmiko import ConnectHandler
from getpass import getpass
import threading
import time
import sys
import orionsdk
import smtplib
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning


disable_warnings(InsecureRequestWarning)

# Class definition to check if vlans already exist
class check (threading.Thread):
    def __init__(self, ndevice):
        threading.Thread.__init__(self)
        self.device = ndevice
    def run(self):
        try:
            global exists
            switch = self.device.split(",")
            platform = switch[2]
            host = switch[1]
            device = ConnectHandler(device_type=platform, ip=host, username=username, password=password)
            for item in vlan_list:
                vlan = device.send_command("show vlan id %s"%(item))
                if 'not found' not in vlan:
                    print('Vlan: %s already exists on: %s check the VLAN ID. Please check and re-run.'%(item, switch[0]))
                    exists = True
        except:
            print('VLAN could not be deployed to %s, please check your Credentials, if they are correct contact Networks quoting the Switch ID as it may be unreachable.'%(switch[0]))
            exists = True # set to True so script will exit 

# Class definition to create vlans and populate trunks
class create (threading.Thread):
    def __init__(self, device):
        threading.Thread.__init__(self)
        self.device = device
    def run(self):
            switch = self.device.split(",")
            # If user choose DC or DC and SUB deploy vlan to these locations
            if perim == "DC" or perim =="DCSUB":
                platform = switch[2]
                host = switch[1]
                switchName = switch[0]
                device = ConnectHandler(device_type=platform, ip=host, username=username, password=password)
                if switch[3] == "DC":
                    for vlanID, vlanNameSub in vlans.items():
                        vlanName, subnet = vlanNameSub.split(",")
                        print ('Creating VLAN: %s name: %s on: %s'%(vlanID, vlanName, switchName))
                        config_commands = ['vlan ' + str(vlanID), 'name ' + str(vlanName)]
                        output = device.send_config_set(config_commands)
                    if ESX != "NO":
                        config_commands = ['do show int des | i 5493716']
                        output = device.send_config_set(config_commands)
                        ESXi_Interfaces = output.splitlines()
                        for E in ESXi_Interfaces:
                            E = E.split()[0]
                            if "Eth" in E or "Gi" in E or "Te" in E:
                                print('Adding VLANs: %s to interface: %s on: %s'%(vlan_string, E, switchName))
                                config_commands = ['interface ' + str(E), 'switchport trunk allowed vlan add ' + str(vlan_string), 'end']
                                output = device.send_config_set(config_commands)
                            

                # Add VLANs to FW Trunks
                    config_commands = ['do show %s'%(fwChange)]
                    output = device.send_config_set(config_commands)
                    FW_Interfaces = output.splitlines()
                    for F in FW_Interfaces:
                        F = F.split()[0]
                        if "Eth" in F or "Gi" in F:
                            print('Adding VLANs: %s to Firewall trunk: %s on: %s'%(vlan_string, F, switchName))
                            config_commands = ['interface ' + str(F),'switchport trunk allowed vlan add ' + str(vlan_string), 'end']
                            output = device.send_config_set(config_commands)
                      

                    config_commands = ['copy run start']
                    print("VLANs successfully added - Saving Config on %s"%(switchName))
                    output = device.send_config_set(config_commands)
        
            # If user choose SUB or DC and SUB deploy vlan to these locations
            if perim == "SUB" or perim == "DCSUB":
                platform = switch[2]
                host = switch[1]
                switchName = switch[0]
                device = ConnectHandler(device_type=platform, ip=host, username=username, password=password)
                if switch[3] == "SUB":
                    for vlanID, vlanNameSub in vlans.items():
                        vlanName, subnet = vlanNameSub.split(",")
                        print ('Creating VLAN: %s name: %s on: %s'%(vlanID, vlanName, switchName))
                        config_commands = ['vlan ' + str(vlanID), 'name ' + str(vlanName)]
                        output = device.send_config_set(config_commands)

            # Add VLANs to FW Trunks specified in input, this will run for DC, SUB or DCSUB
                config_commands = ['do show %s'%(fwChange)]
                output = device.send_config_set(config_commands)
                FW_Interfaces = output.splitlines()
                for F in FW_Interfaces:
                    F = F.split()[0]
                    if "Eth" in F:
                        print('Adding VLANs: %s to Firewall trunk: %s on: %s'%(vlan_string, F, switchName))
                        config_commands = ['interface ' + str(F),'switchport trunk allowed vlan add ' + str(vlan_string), 'end']
                        output = device.send_config_set(config_commands)

                config_commands = ['copy run start']
                print("VLANs successfully added - Saving Config on %s"%(switchName))
                output = device.send_config_set(config_commands)

def createIPAM():
    # Get credentials for IPAM and assign to orion SDK swisclient login
    print("Input IPAM credentials. UPSport username and password.")
    username = input("username: ")
    password = getpass()
    swis = orionsdk.SwisClient("test-UPS-0111.UPS.int", "UPS\\" + str(username), str(password))
    
    for vlanID, vlanNameSub in vlans.items():
        vlanName, subnet = vlanNameSub.split(",")
        subnet, mask = subnet.split('/')
        splitOctets = subnet.split('.')
        subnetBlock = '.'.join(subnet.split('.')[:-2])
    
        if envList[envNr] == "DEV":
            if subnetBlock == "192.248":
                pID = 832
            elif subnetBlock == "192.249":
                pID = 949
            elif subnetBlock == "192.251":
                pID = 3449
            elif subnetBlock == "192.252":
                pID = 952
            elif subnetBlock == "192.253":
                pID = 992
            elif subnetBlock == "192.254":
                pID = 994
            elif subnetBlock == "192.168":
                pID = 997
            else:
                print("Subnet range specified is not in DEV domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                'FriendlyName': str(subnet + "/" + mask),
                'Comments': str(vlanName),
                'ScanInterval': 60, 
                'DisableNeighborScanning': False,
                'NeighborScanAddress': '192.19.254.40',
                'NeighborScanInterval': 60,
                'VLAN': str(vlanID),
                'Location':'Belfast',
                }
        
            customPrSPO = {
                            'Country_City':'Belfast HQ', 
                        }

        elif envList[envNr] == "NDC":
            if subnetBlock == "192.225":
                pID = 3960
            else:
                print("Subnet range specified is not in NDC domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                        'FriendlyName': str(subnet + "/" + mask),
                        'Comments': str(vlanName),
                        'ScanInterval': 60, 
                        # 'DisableNeighborScanning': False,
                        # 'NeighborScanAddress': '***',
                        # 'NeighborScanInterval': 60,
                        'VLAN': str(vlanID),
                        'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
            #                 'Primary_DNS':'*****', 
            #                 'Secondary_DNS':'*****', 
            #                 'Nessus_Asset_Range':str(subnet + "/" + mask), 
            #                'Nessus_Asset_List':'IPAM-*****',
                        }

        elif envList[envNr] == "FCN" or envList[envNr] == "FEN":
            if subnetBlock == "192.192":
                pID = 3436
            elif subnetBlock == "192.193":
                pID = 3437
            elif subnetBlock == "192.194":
                pID = 4017
            elif subnetBlock == "192.30":
                pID = 773
            else:
                print("Subnet range specified is not in FCN domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                        'FriendlyName': str(subnet + "/" + mask),
                        'Comments': str(vlanName),
                        'ScanInterval': 60, 
                        'DisableNeighborScanning': False,
                        'NeighborScanAddress': '192.19.254.120',
                        'NeighborScanInterval': 60,
                        'VLAN': str(vlanID),
                        'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
                        'Primary_DNS':'192.192.0.11', 
                        'Secondary_DNS':'192.192.0.12', 
                        'Nessus_Asset_Range':str(subnet + "/" + mask), 
                        'Nessus_Asset_List':'IPAM-LIST-NETWORK',
                        }


        elif envList[envNr] == "RYC":
            if subnetBlock == "192.28":
                pID = 4243
            elif subnetBlock == "201.46":
                pID = 1647
            elif subnetBlock == "62.62":
                pID = 1032
            elif subnetBlock == "202.46":
                pID = 817
            else:
                print("Subnet range specified is not in RYC domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                    'FriendlyName': str(subnet + "/" + mask),
                    'Comments': str(vlanName),
                    'ScanInterval': 60, 
                    # 'DisableNeighborScanning': False,
                    # 'NeighborScanAddress': '***',
                    # 'NeighborScanInterval': 60,
                    'VLAN': str(vlanID),
                    'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
                        }

        elif envList[envNr] == "RPC":
            if subnetBlock == "192.0":
                pID = 1085
            elif subnetBlock == "192.1":
                pID = 1087
            elif subnetBlock == "192.3":
                pID = 3975
            elif subnetBlock == "192.46":
                pID = 1644
            elif subnetBlock == "192.240":
                pID = 1115
            elif subnetBlock == "192.241":
                pID = 1165
            elif subnetBlock == "192.242":
                pID = 1167
            elif subnetBlock == "192.243":
                pID = 1170
            else:
                print("Subnet range specified is not in RPC domain, please check your information, exiting.")
                sys.exit(0)
            
            prSPO = {
                        'FriendlyName': str(subnet + "/" + mask),
                        'Comments': str(vlanName),
                        'ScanInterval': 60, 
                        'DisableNeighborScanning': False,
                        'NeighborScanAddress': '192.19.254.20',
                        'NeighborScanInterval': 60,
                        'VLAN': str(vlanID),
                        'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
                        'Primary_DNS':'192.1.13.11', 
                        'Secondary_DNS':'192.1.13.12', 
                        'Nessus_Asset_Range':str(subnet + "/" + mask), 
                        'Nessus_Asset_List':'IPAM-CORE-NETWORK',
                        }

        elif envList[envNr] == "SPO":
            if subnetBlock == "192.128":
                pID = 1243
            elif subnetBlock == "192.191":
                pID = 1240
            elif subnetBlock == "150.50":
                pID = 1642
            elif subnetBlock == "159.46":
                pID = 1187
            elif subnetBlock == "192.168":
                pID = 1201
            else:
                print("Subnet range specified is not in SPO domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                        'FriendlyName': str(subnet + "/" + mask),
                        'Comments': str(vlanName),
                        'ScanInterval': 60, 
                        'DisableNeighborScanning': False,
                        'NeighborScanAddress': '192.19.254.110',
                        'NeighborScanInterval': 60,
                        'VLAN': str(vlanID),
                        'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
                        'Primary_DNS':'192.128.41.11', 
                        'Secondary_DNS':'192.128.41.12', 
                        'Nessus_Asset_Range':str(subnet + "/" + mask), 
                        'Nessus_Asset_List':'IPAM-CENTRE-NETWORK',
                        }


        elif envList[envNr] == "DMZ":
            if subnetBlock == "192.20":
                pID = 1659
            elif subnetBlock == "192.224":
                pID = 1605
            elif subnetBlock == "192.64":
                pID = 1381
            elif subnetBlock == "192.65":
                pID = 1623
            elif subnetBlock == "192.66":
                pID = 1619
            elif subnetBlock == "192.67":
                pID = 3971
            elif subnetBlock == "192.68":
                pID = 3973
            elif subnetBlock == "192.69":
                pID = 4185
            elif subnetBlock == "192.70":
                print("No subnets exist in this folder at present, please add this one manually to IPAM and inform script admin.")
            elif subnetBlock == "192.91":
                pID = 1656
            elif subnetBlock == "192.17":
                pID = 3482
            elif subnetBlock == "192.168":
                pID = 1467
            else:
                print("Subnet range specified is not in DMZ domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                        'FriendlyName': str(subnet + "/" + mask),
                        'Comments': str(vlanName),
                        'ScanInterval': 60, 
                        'DisableNeighborScanning': False,
                        'NeighborScanAddress': '192.19.254.60',
                        'NeighborScanInterval': 60,
                        'VLAN': str(vlanID),
                        'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
        #                 'Primary_DNS':'***', 
        #                 'Secondary_DNS':'***', 
                        'Nessus_Asset_Range':str(subnet + "/" + mask), 
                        'Nessus_Asset_List':'IPAM-DMZ-NETWORK',
                        }

            
        elif envList[envNr] == "AZP":
            if subnetBlock == "192.100":
                pID = 1052
            elif subnetBlock == "192.96":
                pID = 1042
            elif subnetBlock == "192.98":
                pID = 1059
            elif subnetBlock == "192.99":
                pID = 1066
            elif subnetBlock == "192.168":
                pID = 1635
            else:
                print("Subnet range specified is not in AZP domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                        'FriendlyName': str(subnet + "/" + mask),
                        'Comments': str(vlanName),
                        'ScanInterval': 60, 
                        'DisableNeighborScanning': False,
                        'NeighborScanAddress': '192.100.47.129',
                        'NeighborScanInterval': 60,
                        'VLAN': str(vlanID),
                        'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
            #                 'Primary_DNS':'***', 
            #                 'Secondary_DNS':'***', 
            #                 'Nessus_Asset_Range':str(subnet + "/" + mask), 
            #                 'Nessus_Asset_List':'***',
                        }

        elif envList[envNr] == "RND":
            if subnetBlock == "192.29":
                pID = 3416
            else:
                print("Subnet range specified is not in RND domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                        'FriendlyName': str(subnet + "/" + mask),
                        'Comments': str(vlanName),
                        'ScanInterval': 60, 
                        'DisableNeighborScanning': False,
                        'NeighborScanAddress': '192.100.47.129',
                        'NeighborScanInterval': 60,
                        'VLAN': str(vlanID),
                        'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
            #                 'Primary_DNS':'***', 
            #                 'Secondary_DNS':'***', 
            #                 'Nessus_Asset_Range':str(subnet + "/" + mask), 
            #                 'Nessus_Asset_List':'***',
                        }


        elif envList[envNr] == "UPS":
            if subnetBlock == "192.16":
                pID = 301
            elif subnetBlock == "192.19":
                pID = 351
            else:
                print("Subnet range specified is not in UPS domain, please check your information, exiting.")
                sys.exit(0)

            prSPO = {
                        'FriendlyName': str(subnet + "/" + mask),
                        'Comments': str(vlanName),
                        'ScanInterval': 60, 
                        'DisableNeighborScanning': False,
                        'NeighborScanAddress': '192.19.254.30',
                        'NeighborScanInterval': 60,
                        'VLAN': str(vlanID),
                        'Location':'Belfast',
            }

            customPrSPO = {
                        'Country_City':'Belfast HQ', 
                        'Primary_DNS':'192.16.62.11', 
                        'Secondary_DNS':'192.16.62.12', 
                        'Nessus_Asset_Range':str(subnet + "/" + mask), 
                        'Nessus_Asset_List':'IPAM-UPS-NETWORK',
                        }
        
        #Create Subnet and move under correct folder
        results = swis.invoke('IPAM.SubnetManagement', 'CreateSubnet', str(subnet), int(mask)) 
        results = swis.query("SELECT TOP 10 Uri FROM IPAM.Subnet WHERE Address='" + str(subnet) + "'""") 
        uriSubnet = results['results'][0]['Uri']
        results = swis.update("" + str(uriSubnet) + "", ParentId=int(pID), **prSPO)
        #Update Subnet Custom Properties - 
        results = swis.query("SELECT TOP 10 SubnetId FROM IPAM.Subnet WHERE Address='" + str(subnet) + "'""") #find new subnet
        subnetId = results['results'][0]['SubnetId']
        results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.GroupNodeDisplayCustomProperties/GroupId=" + str(subnetId) + "/CustomProperties", **customPrSPO) #create GCP
        results = swis.invoke('IPAM.SubnetManagement', 'ChangeDisableAutoScanning', str(subnetId), True) #create GCP
            
# # IP ALLOCATE section 

        fwPrefix = {
            "RPC":"FO", 
            "SPO":"FE", 
            "DMZ":"FD", 
            "DEV":"FR",
            "AZP":"FP", 
            "UPS":"FS", 
            "FCN":"CN",
            "FEN":"CN",
            "NDC":"DC",
            "RYC":"N/A"
                        }  

        subnetBlock = '.'.join(subnet.split('.')[:-1])
        if mask == '16' or mask == '17' or mask == '18' or mask == '19' or mask == '20' or mask == '21' or mask == '22' or mask == '23' or mask == '24' and envList[envNr] != "RYC":
            #SET VIP
            results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetBlock) + ".10""'") #find IP Uri 
            ipNodeID = results['results'][0]['IpNodeId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", DnsBackward = str(fwPrefix[envList[envNr]]) + '-VIP-VLAN' + str(vlan), Alias = str(fwPrefix[envList[envNr]]) + '-VIP-VLAN' + str(vlan), Status = '1', SysName = 'Checkpoint Firewall', SkipScan = True, Comments = str(fwPrefix[envList[envNr]]) + '-VIP-VLAN' + str(vlan))  
            #Set Gateway IP in settings
            results = swis.query("SELECT TOP 10 SubnetId FROM IPAM.Subnet WHERE Address='" + str(subnet) + "'""") #find new subnet
            subnetId = results['results'][0]['SubnetId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.GroupNodeDisplayCustomProperties/GroupId=" + str(subnetId) + "/CustomProperties", Gateway_IP=str(subnetBlock) + ".10") #create GCP


            #SET PHYSICAL IP 1
            results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetBlock) + ".5""'") #find IP Uri 
            ipNodeID = results['results'][0]['IpNodeId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", DnsBackward = str(fwPrefix[envList[envNr]]) + '-1-VLAN' + str(vlan), Alias = str(fwPrefix[envList[envNr]]) + '-1-VLAN' + str(vlan), Status = '1', SysName = 'Checkpoint Firewall', SkipScan = True, Comments = str(fwPrefix[envList[envNr]]) + '-1-VLAN' + str(vlan))  
            #SET PHYSICAL IP 2
            results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetBlock) + ".6""'") #find IP Uri 
            ipNodeID = results['results'][0]['IpNodeId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", DnsBackward = str(fwPrefix[envList[envNr]]) + '-2-VLAN' + str(vlan), Alias = str(fwPrefix[envList[envNr]]) + '-2-VLAN' + str(vlan), Status = '1', SysName = 'Checkpoint Firewall', SkipScan = True, Comments = str(fwPrefix[envList[envNr]]) + '-2-VLAN' + str(vlan)) 
            i = 1
            while i < 5:
                #SET ReSUBved IP 1
                results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetBlock) + "." + str(i) + "'")  
                ipNodeID = results['results'][0]['IpNodeId']
                results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", Alias = 'Reserved', Status = '4', SysName = 'SSP', SkipScan = True, Comments = 'Reserved')  
                i += 1
            e = 7
            while e < 10:
                #SET ReSUBved IP 1
                results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetBlock) + "." + str(e) + "'")  
                ipNodeID = results['results'][0]['IpNodeId']
                results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", Alias = 'Reserved', Status = '4', SysName = 'SSP', SkipScan = True, Comments = 'Reserved')  
                e += 1   
        
        i = 0
        lastOctet = int(splitOctets[3])
        subnetSlice = '.'.join(subnet.split('.')[:-1])
        
        if mask == '25' or mask == '26' or mask == '27' or mask == '28' or mask == '29' and envList[envNr] != "RYC":
            #SET VIP
            results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetSlice) + "." + str(lastOctet + (i +  1)) + "'") #find IP Uri 
            ipNodeID = results['results'][0]['IpNodeId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", DnsBackward = str(fwPrefix[envList[envNr]]) + '-VIP-VLAN' + str(vlan), Alias = str(fwPrefix[envList[envNr]]) + '-VIP-VLAN' + str(vlan), Status = '1', SysName = 'Checkpoint Firewall', SkipScan = True, Comments = str(fwPrefix[envList[envNr]]) + '-VIP-VLAN' + str(vlan))  
            #Set Gateway IP in settings
            results = swis.query("SELECT TOP 10 SubnetId FROM IPAM.Subnet WHERE Address='" + str(subnet) + "'""") #find new subnet
            subnetId = results['results'][0]['SubnetId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.GroupNodeDisplayCustomProperties/GroupId=" + str(subnetId) + "/CustomProperties", Gateway_IP=str(subnetSlice) + "." + str(lastOctet + (i +  1))) #create GCP

            
            #SET PHYSICAL IP 1
            results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetSlice) + "." + str(lastOctet + (i +  2)) + "'") #find IP Uri 
            ipNodeID = results['results'][0]['IpNodeId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", DnsBackward = str(fwPrefix[envList[envNr]]) + '-1-VLAN' + str(vlan), Alias = str(fwPrefix[envList[envNr]]) + '-1-VLAN' + str(vlan), Status = '1', SysName = 'Checkpoint Firewall', SkipScan = True, Comments = str(fwPrefix[envList[envNr]]) + '-1-VLAN' + str(vlan))  
            #SET PHYSICAL IP 2
            results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetSlice) + "." + str(lastOctet + (i +  3)) + "'") #find IP Uri 
            ipNodeID = results['results'][0]['IpNodeId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", DnsBackward = str(fwPrefix[envList[envNr]]) + '-2-VLAN' + str(vlan), Alias = str(fwPrefix[envList[envNr]]) + '-2-VLAN' + str(vlan), Status = '1', SysName = 'Checkpoint Firewall', SkipScan = True, Comments = str(fwPrefix[envList[envNr]]) + '-2-VLAN' + str(vlan))  
            #SET ReSUBved IP 1
            results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetSlice) + "." + str(lastOctet + (i +  4)) + "'") #find IP Uri 
            ipNodeID = results['results'][0]['IpNodeId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", Alias = 'Reserved', Status = '4', SysName = 'SSP', SkipScan = True, Comments = 'Reserved')  
            #SET ReSUBved IP 2
            results = swis.query("SELECT TOP 10 IpNodeId FROM IPAM.IPNode WHERE IPAddress='" + str(subnetSlice) + "." + str(lastOctet + (i +  5)) + "'") #find IP Uri 
            ipNodeID = results['results'][0]['IpNodeId']
            results = swis.update("swis://dev-ipam-0001.development.int/Orion/IPAM.IPNode/IpNodeId=" + str(ipNodeID) + "", Alias = 'Reserved', Status = '4', SysName = 'SSP', SkipScan = True, Comments = 'Reserved')  
            
    return 0

def generateTicket():

    fwPrefix = {
            "RPC":"FO", 
            "SPO":"FE", 
            "DMZ":"FD", 
            "DEV":"FR",
            "AZP":"FP", 
            "UPS":"FS", 
            "FCN":"CN",
            "FEN":"CN",
            "NDC":"DC",
            "RYC":"N/A"
            }

    fwTrunkDev = {
                "1":"ESXi hosts and FW trunk Dev Core ", 
                "2":"ESXi hosts and FW trunk Dev No_Core", 
                "3":"ESXi hosts and FW trunk FEN eth 2", 
                "4":"ESXi hosts and FW trunk FCN Eth 1-04", 
                "5":"ESXi hosts and FW trunk RPC_servers ", 
                "6":"ESXi hosts and FW trunk RPC Clients", 
                "7":"ESXi hosts and FW trunk DMZ 3", 
                "8":"ESXi hosts and FW trunk DMZ 4", 
                "9":"ESXi hosts and both UPS FW trunks", 
                "10":"ESXi hosts and both SPO FW trunks", 
                "11":"ESXi hosts and FW trunk CDC PRD ", 
                "12":"ESXi hosts and FW trunk CDC PPR", 
                "13":"ESXi hosts and FW trunk DMZ_1", 
                "14":"ESXi hosts and FW trunk DMZ_2",
                "15":"ESXi hosts and both AZP FW trunks", 
                "16":"ESXi hosts (not added to Physical FW trunks)",
                "17":"N/A"
                }

    outputAll = []
    for vlan_Id, vlanNameSub in vlans.items():
        vlanName, s = vlanNameSub.split(",")
        subnet, mask = s.split('/')
        splitOctets = subnet.split('.')
        lastOctet = int(splitOctets[3])
        subnet = '.'.join(subnet.split('.')[:-1])
        i = 0

        outputAll.append("VLAN Name: " + str(vlanName) + ", subnet " + str(s) + " - VLAN" + str(vlan_Id))

        if mask == '16' or mask == '17' or mask == '18' or mask == '19' or mask == '20' or mask == '21' or mask == '22' or mask == '23' or mask == '24':
            outputLine = "{}-VIP-VLAN{} {}.10".format(fwPrefix[envList[envNr]], vlan_Id, subnet)
            outputAll.append(outputLine)
            outputLine = "{}-1-VLAN{} {}.5".format(fwPrefix[envList[envNr]], vlan_Id, subnet)
            outputAll.append(outputLine)
            outputLine = "{}-2-VLAN{} {}.6".format(fwPrefix[envList[envNr]], vlan_Id, subnet) 
            outputAll.append(outputLine)
            outputAll.append("Added to IPAM")
            outputAll.append("Added to vlan.dat, " + fwTrunkDev[fw] )
        else:
            outputLine = "{}-VIP-VLAN{} {}.{}".format(fwPrefix[envList[envNr]], vlan_Id, subnet, str(lastOctet + (i +  1))) 
            outputAll.append(outputLine)
            outputLine = "{}-1-VLAN{} {}.{}".format(fwPrefix[envList[envNr]], vlan_Id, subnet, str(lastOctet + (i +  2))) 
            outputAll.append(outputLine)
            outputLine = "{}-2-VLAN{} {}.{}".format(fwPrefix[envList[envNr]], vlan_Id, subnet, str(lastOctet + (i +  3))) 
            outputAll.append(outputLine)
            outputAll.append("Added to IPAM")
            outputAll.append("Added to vlan.dat, " + fwTrunkDev[fw])
        outputAll.append(" ")
            
    for line in outputAll:
        print(line)


            
    #code to email output to user
    receiver = input("Enter the email address that will recieve the output: ")
    #ticketRef = input("Enter the ticket reference for the change: ")
    ticketRef = "TEST"
    smtp_SUBver = "smtp.UPS.int"
    port = 25
    sender = "vlanAutomation@UPS.int"
    #receiver = "John-Anthony.Leathem@ext.test..eu "
    message = """\
Subject:{}
From:{}
To:{}

{}    

"""

    with smtplib.SMTP(smtp_SUBver, port) as SUBver:
        SUBver.sendmail(sender, receiver, message.format(ticketRef, sender, receiver,'\n'.join(outputAll)))

# Start main program
if __name__ == '__main__':
    # List of environments that can be configured
    envList = {1:"RPC", 2:"SPO", 3:"DMZ", 4:"DEV", 5:"RYC", 6:"AZP", 7:"UPS", 8:"FEN", 9:"NDC", 10:"FCN"}
    inputString = ""
    for key, value in envList.items():
        inputString += "%s (%s) - "%(value, key)
    inputString += "Enter a number: "
    # Prompts to enter network/DC or SUB (or both)/firewall trunks to which VLANs will be added.
    envNr = input(inputString)
    while not envNr.isdigit() or int(envNr) not in envList:
        envNr = input(inputString)
    envNr = int(envNr)
    environment = envList[envNr]

    print ("New VLAN creation on %s" %(environment))
    #print ("New VLAN creation on %s" %(environment))

    #choice for user on whether to deploy to the DC, SUB or DC and SUB
    perim = input("DC's only (1) - SUB's only (2) - DC's + SUB's (3) - Enter a number: ")
    while (perim != '1') and (perim != '2') and (perim != '3'):
        perim = input("DC's only (1) - SUB's only (2) - DC's + SUB's (3) - Enter a number: ")

    if perim == '1':
        perim = "DC"
        print ("New VLAN creation on %s DC switches only (core/distribution)"%(envList[envNr]))
    elif perim == '2':
        perim = "SUB"
        print ("New VLAN creation on %s SUB switches only (access)"%(envList[envNr]))
    elif perim == '3':
        perim = "DCSUB"
        print ("New VLAN creation on %s DC and SUB switches (core/distribution/access)"%(envList[envNr]))

    #Select FW trunk based on enviroment selction
    #if you add a new FW option make sure to add the string conversion below also
    # Set respective code matching interface descriptions!!
    if envNr == 1:
        fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nRPC servers (5) - RPC Clients (6) : ")
        while  (fw != '5') and (fw != '6'): 
            fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\n RPC servers (5) - RPC Clients (6) : ")
        if fw == '5': #RPC servers
            fwChange = 'int des | i 2657830'
        elif fw == '6': #RPC Clients
            fwChange = 'int des | i 6128749'
    if envNr == 2:
        fw = "10"
        fwChange = 'int des | i 2657830'
    if envNr == 3:
        fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nDMZ 0 (7) - DMZ `1 (8) - DMZ 2 (13) - DMZ 4 (14) : ")
        while  (fw != '7') and (fw != '8') and (fw != '13') and (fw != '14'): 
            fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nDMZ 0 (7) - DMZ `1 (8) - DMZ 2 (13) - DMZ 4 (14) : ")
        if fw == '7': #DMZ 0
            fwChange = 'int des | i 2657830'
        elif fw == '8': #DMZ 1
            fwChange = 'int des | i 6128749'
        elif fw == '13': #DMZ 2
            fwChange = 'int des | i 5387290'
        elif fw == '14': #DMZ OTHER OUT (ELO,SKYPE,XWAY)
            fwChange = 'int des | i 9876725'
    if envNr == 4:
        fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nDEV_CORE (1) - DEV_NoCORE (2) : ")
        while  (fw != '1') and (fw != '2') and (fw != '16'): 
            fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nDEV_CORE (1) - DEV_NoCORE (2) : ")
        if fw == '1': #DEV_Core
            fwChange = 'int des | i 2657830'
        elif fw == '2': #DEEV_NoCORE
            fwChange = 'int des | i 6128749'
    if envNr == 5:
        fw = "17"
        fwChange = 'int des | i *!*!'
    if envNr == 6:
        fw = "15"
        fwChange = 'int des | i 6128749'
    if envNr == 7:
        fw = "9"
        fwChange = 'int des | i 2657830'
    if envNr == 8:
        fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nFEN (3) - FRZ (16) : ")
        while  (fw != '3') and (fw != '16'): 
            fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nFEN (3) - FRZ (16) : ") 
        if fw == '3': #FEN
            fwChange = 'int des | i 2657830'
        elif fw == '16': #FRZ
            fwChange = 'int des | i *!*!'
    if envNr == 9:
        fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nNDC prd (11) - NDC Ppr (12) : ")
        while  (fw != '11') and (fw != '12'): 
            fw = input("Please enter the number for Firewall trunk would you like the VLAN added to?\nNDC prd (11) - NDC Ppr (12) : ") 
        if fw == '11': #NDC Prd
            fwChange = 'int des | i 6128749'
        elif fw == '12': #NDC Ppr
            fwChange = 'int des | i !*!*'
    if envNr == 10:
        fw = "4"
        fwChange = 'int des | i 6128749'


    ESX = input("Add to ESXi hosts? hit ENTER to add or type 'NO' to skip: ")

    #login and data variables
    username = input("Switch username: ")
    password = getpass()
    vlan_string = input("List the Vlans separated by a comma e.g. '3, 6, 9': ")
    vlan_string = vlan_string.replace(" ", "")
    vlan_list = vlan_string.split(",") 

    #Data gathering/validation - !vlan name must start with ENV then STG then _ and cant be more than 20 chars. Also the script will remove whitespace.
    vlans = {} 
    for vlan in vlan_list:
        vlan_name = input("Input Vlan name for Vlan %s: "%(vlan))
        while (envList[envNr] != vlan_name[0:3]) or len(vlan_name) > 20 or vlan_name[6] != "_":
            vlan_name = input("Check input meets naming convention requirements! Name must begin '<ENV><STG>_'. Input Vlan name for Vlan %s: "%(vlan) + "\n")
        vlan_name_edit = vlan_name.replace(" ", "")
        subnet_string = input("Enter the subnet and mask separted for VLAN %s e.g. 192.2.1.48/28: "%(vlan))
        while "/" not in subnet_string:
            subnet_string = input("Enter the subnet and mask separted for VLAN %s e.g. 192.2.1.48/28: "%(vlan))
        subnet_list = subnet_string.replace(" ", "")
        vlans[int(vlan)] = vlan_name_edit + "," + subnet_list

    answer = input("Type (y) to continue with switch VLAN creation. Please check vlan names and ID match before you continue: ")
    if answer != "y" and answer !="Y":
        sys.exit(0)


    #open and read text files with the list of switches in the different domains.
    with open("%s.txt"%(envList[envNr].lower())) as f:
    #with open("%s.txt"%(envList[envNr].lower())) as f:
        device_list = f.read().splitlines()

    exists = False
    threads = [] #empty list
    Threads = []

    #starts check function 
    for devices in device_list:
        threads.append(check(devices)) #populates empty list threads with the data from each thread run on each device
    for thread in threads:
        thread.start() #starts each thread
    for thread in threads:
        thread.join() #wait for the thread to finish

    if exists:
        sys.exit(0)

    # #initiates class create to create VLANs and add VLANs to Trunks.
    for device in device_list:
        Threads.append(create(device)) #populates empty list threads with the data from each thread run on each device
    for Thread in Threads:
        Thread.start() #starts each thread
    for Thread in Threads:
        Thread.join() #wait for the thread to finish

        
    print("\n")
    answer = input("Do you want to add the subnets associated to the VLANs to IPAM? Type (y) to agree : ")
    if answer == "y":
        createIPAM()

    answer = input("Do you want to email the information for the UPSport works ticket to yourself? Type (y) to agree : ")
    print("\n")
    if answer == "y":
        generateTicket()