from genie.conf import Genie

# Load the testbed YAML file
testbed = Genie.init("testbed.yaml")

# Connect to all devices in the testbed
devices = testbed.devices
for device_name, device in devices.items():
    device.connect()

# Store edges
info = {}
info['root'] = {}
info['stp'] = {}

# Iterate over devices to parse STP output
for device_name, device in devices.items():
    print(f"Processing device: {device_name}")
    
    # Parse STP information
    stp_output = device.parse("show spanning-tree")
    cdp_output = device.parse("show cdp neighbor")
    vlan_data = stp_output.get('pvst', {}).get('vlans', {}).get(1, {})
    if vlan_data['root']['address']==vlan_data['bridge']['address']:
        info['root'] = device_name
    
    if vlan_data:
        interfaces = vlan_data.get('interfaces', {})
        for interface, interface_data in interfaces.items():
            # Check port state
            port_state = interface_data.get('port_state')
            if port_state == 'blocking':
                continue
            role = interface_data.get('role')

            neighbor = "client unknown"
            for i, j in cdp_output['cdp']["index"].items():
                if interface != j["local_interface"]:
                    continue
                
                neighbor = {"device" : j["device_id"].split('.')[0],
                 "port" : "GigabitEthernet" + j["port_id"]}

            if neighbor == "client unknown":
                continue

            device_stp = {
                interface :
                {"state" : port_state, "role" : role, "neighbor" : neighbor}
                }

            try:
                info['stp'][device_name].append(device_stp)
            except Exception as KeyError:
                info['stp'][device_name] = [device_stp]

print(info)
# Disconnect from all devices
for device_name, device in devices.items():
    device.disconnect()
