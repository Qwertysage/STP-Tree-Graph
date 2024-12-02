from genie.conf import Genie
import networkx as nx
import matplotlib.pyplot as plt

def extract_filtered_edges(data):
    edges = []  # To store valid edges
    stp = data['stp']  # Access the STP data

    # Iterate through each switch and its interfaces
    for switch, interfaces in stp.items():
        for interface_data in interfaces:
            for interface, details in interface_data.items():
                # Get neighbor information
                neighbor = details.get('neighbor', {}).get('device')
                neighbor_port = details.get('neighbor', {}).get('port')
                role = details.get('role')

                # Filter for designated roles
                if role == "designated" and neighbor and neighbor_port:
                    # Check if the neighbor has the corresponding root port
                    neighbor_interfaces = stp.get(neighbor, [])
                    for neighbor_data in neighbor_interfaces:
                        for neighbor_interface, neighbor_details in neighbor_data.items():
                            # Match the neighbor port and verify it is a root port
                            if (
                                neighbor_interface == neighbor_port
                                and neighbor_details.get('role') == "root"
                            ):
                                # Add edge if valid
                                edge = tuple(sorted((switch, neighbor)))  # Ensure no duplicates
                                edges.append(edge)

    # Remove duplicate edges
    unique_edges = list(set(edges))
    return unique_edges
def visualize_hierarchical_topology(edges):
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add edges dynamically
    G.add_edges_from(edges)
    
    # Create a hierarchical layout
    def hierarchy_pos(G, root=None, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5):
        """
        Generate a hierarchical layout for the graph.
        """
        pos = _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)
        return pos

    def _hierarchy_pos(G, root, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None, parent=None, parsed=[]):
        if pos is None:
            pos = {root: (xcenter, vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
        if len(children) != 0:
            dx = width / len(children)
            nextx = xcenter - width / 2 - dx / 2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G, child, width=dx, vert_gap=vert_gap,
                                     vert_loc=vert_loc - vert_gap, xcenter=nextx, pos=pos,
                                     parent=root, parsed=parsed)
        return pos

    # Generate hierarchical positions
    pos = hierarchy_pos(G, root="SW1")
    
    # Visualize the graph with the hierarchical layout
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, edge_color='gray', linewidths=1, font_size=10)
    plt.title("Hierarchical Layer 2 Topology: SW1 Root")
    plt.show()

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

edges = extract_filtered_edges(info)
print(edges)
visualize_hierarchical_topology(edges)

# Disconnect from all devices
for device_name, device in devices.items():
    device.disconnect()
