from genie.conf import Genie
from genie.utils import Dq

# Load the testbed YAML file
testbed = Genie.init("testbed.yaml")

# Connect to all devices in the testbed
devices = testbed.devices
for device_name, device in devices.items():
    device.connect()

# Store edges
edges = []

# Iterate over devices to parse STP output
for device_name, device in devices.items():
    print(f"Processing device: {device_name}")
    
    # Parse STP information
    stp_output = device.parse("show spanning-tree")
    
    # Check only for VLAN 1
    vlan_data = stp_output.get('mstp', {}).get('vlans', {}).get('1', {})
    if vlan_data:
        for interface, interface_data in vlan_data.get('interfaces', {}).items():
            # Check port state
            port_state = interface_data.get('port_state')
            if port_state and port_state.lower() == "forwarding":
                # Extract the designated bridge (neighbor switch)
                designated_bridge = interface_data.get('designated_bridge')
                if designated_bridge:
                    neighbor_switch = designated_bridge.split()[0]  # Extract the switch name
                    edge = (device_name, neighbor_switch)
                    edges.append(edge)

# Remove duplicate edges
edges = list({tuple(sorted(edge)) for edge in edges})

# Print the list of edges
print("List of edges for VLAN 1 (excluding blocking links):")
print(edges)

# Disconnect from all devices
for device_name, device in devices.items():
    device.disconnect()
