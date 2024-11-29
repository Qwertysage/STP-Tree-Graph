from genie.conf import Genie

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
    vlan_data = stp_output.get('pvst', {}).get('vlans', {}).get(1, {})
    
    if vlan_data:
        interfaces = vlan_data.get('interfaces', {})
        for interface, interface_data in interfaces.items():
            # Check port state
            port_state = interface_data.get('port_state')
            designated_bridge = interface_data.get('designated_bridge')  # Neighbor's bridge MAC
            role = interface_data.get('role')  # Optional: Role for debugging
            print(f"Interface {interface} on {device_name}: state={port_state}, role={role}, neighbor={designated_bridge}")

            if port_state and port_state.lower() == "forwarding" and designated_bridge:
                # Use the device name and designated bridge as the edge
                edge = (device_name, designated_bridge)
                edges.append(edge)

# Remove duplicate edges
edges = list({tuple(sorted(edge)) for edge in edges})

# Print the list of edges
print("List of edges for VLAN 1 (excluding blocking links):")
print(edges)

# Disconnect from all devices
for device_name, device in devices.items():
    device.disconnect()
