from typing import List, Dict, Optional, Union
import difflib
from dataclasses import dataclass, field
from pprint import pprint

@dataclass
class Button:
    type: str
    target: Optional[Union[int, None]]

@dataclass
class Element:
    name: str
    type: str
    data: Optional[Union[str, list]] = None
    should_submit_data: bool = False
    skip_if_unlocalized: bool = False
    is_localized: Optional[bool] = None

@dataclass
class Child:
    description: str
    node_id: int
    parent_node_id: Optional[int] = None  # Reference to parent node

@dataclass
class Node:
    id: int
    key: str
    header: str
    subheader: Optional[str]
    info: Optional[str]
    button: Optional[Button]
    elements: List[Element]
    report_type: Optional[str]
    children: List[Child] = field(default_factory=list)
    is_multi_select_required: bool = False
    is_auto_submit: bool = False

@dataclass
class ReportData:
    name: str
    variant: str
    version: str
    postback_url: str
    root_node_id: int
    success_node_id: int
    fail_node_id: int
    nodes: Dict[int, Node]

# Function to parse the elements from the JSON
def parse_elements(elements_data):
    elements = []
    for element_data in elements_data:
        element = Element(
            name=element_data.get("name"),
            type=element_data.get("type"),
            data=element_data.get("data"),
            should_submit_data=element_data.get("should_submit_data", False),
            skip_if_unlocalized=element_data.get("skip_if_unlocalized", False),
            is_localized=element_data.get("is_localized")
        )
        elements.append(element)
    return elements

# Function to parse the children and link to the parent node
def parse_children(children_data, parent_node_id):
    children = []
    for child_data in children_data:
        child = Child(description=child_data[0], node_id=child_data[1], parent_node_id=parent_node_id)
        children.append(child)
    return children

# Function to parse nodes from the JSON
def parse_nodes(nodes_data):
    nodes = {}
    for node_id, node_data in nodes_data.items():
        node = Node(
            id=node_data.get("id"),
            key=node_data.get("key"),
            header=node_data.get("header"),
            subheader=node_data.get("subheader"),
            info=node_data.get("info"),
            button=Button(type=node_data["button"]["type"], target=node_data["button"].get("target")) if node_data.get("button") else None,
            elements=parse_elements(node_data.get("elements", [])),
            report_type=node_data.get("report_type"),
            children=parse_children(node_data.get("children", []), parent_node_id=int(node_id)),
            is_multi_select_required=node_data.get("is_multi_select_required", False),
            is_auto_submit=node_data.get("is_auto_submit", False)
        )
        nodes[int(node_id)] = node
    return nodes

# Function to parse the full JSON object into ReportData
def parse_report_data(data):
    return ReportData(
        name=data["name"],
        variant=data["variant"],
        version=data["version"],
        postback_url=data["postback_url"],
        root_node_id=data["root_node_id"],
        success_node_id=data["success_node_id"],
        fail_node_id=data["fail_node_id"],
        nodes=parse_nodes(data["nodes"])
    )

# # Function to search for a breadcrumb based on similarity
# def search_breadcrumb(report_data: ReportData, search_term: str) -> Optional[Node]:
#     search_term = search_term.lower()
#     all_breadcrumbs = []

#     # Create a mapping between descriptions and their node IDs
#     breadcrumb_to_node_map = {}
#     for node in report_data.nodes.values():
#         for child in node.children:
#             description = child.description.lower()
#             all_breadcrumbs.append(description)
#             breadcrumb_to_node_map[description] = report_data.nodes[child.node_id]

#     # Use difflib to find the closest match (case-insensitive)
#     closest_matches = difflib.get_close_matches(search_term, all_breadcrumbs, n=1, cutoff=0.5)

#     if closest_matches:
#         closest_match = closest_matches[0]
#         return breadcrumb_to_node_map[closest_match]
#     else:
#         return None

# Update find_breadcrumbs to correctly traverse from the root to the last node
def find_breadcrumbs(last_node: Node, nodes_dict: Dict[int, Node]) -> List[int]:
    breadcrumbs = []
    current_node = last_node

    # Traverse through child-parent relationships based on button targets and child arrays
    while current_node:
        breadcrumbs.insert(0, current_node.id)  # Insert at the beginning of the list

        # Try to find a node that has this node as a child or target in its button
        parent_node = next(
            (node for node in nodes_dict.values()
             if any(child.node_id == current_node.id for child in node.children) or
             (node.button and node.button.target == current_node.id)),
            None
        )
        current_node = parent_node  # Move up to the parent node

    return breadcrumbs

# Correct element detection logic
def detect_elements(breadcrumbs: List[int], nodes_dict: Dict[int, Node]) -> Dict[str, List[str]]:
    elements_data = {}

    # Traverse backward and detect elements that influence selection (before final node)
    for breadcrumb_id in breadcrumbs[:-1]:  # We exclude the last breadcrumb (final node)
        node = nodes_dict[breadcrumb_id]
        for element in node.elements:
            # Only look for checkboxes that influence the selection
            if element.type == 'checkbox' and element.data:
                # We capture all selected items from checkboxes that influence the report
                selected_items = [item[0] for item in element.data]  # Collect all available options
                elements_data[element.name] = selected_items  # Populate elements based on earlier nodes

    return elements_data


# Function to search for a breadcrumb based on similarity
def search_breadcrumb(report_data: ReportData, search_term: str) -> Optional[Node]:
    # Create a list of all breadcrumb descriptions
    all_breadcrumbs = []
    breadcrumb_to_node_map = {}

    # Collect breadcrumbs and map them to nodes
    for node in report_data.nodes.values():
        for child in node.children:
            all_breadcrumbs.append(child.description)
            breadcrumb_to_node_map[child.description] = report_data.nodes[child.node_id]

    # Use difflib to find the closest match
    closest_matches = difflib.get_close_matches(search_term, all_breadcrumbs, n=1, cutoff=0.6)

    if closest_matches:
        closest_match = closest_matches[0]
        return breadcrumb_to_node_map[closest_match]
    else:
        return None

def dfs_print(report_data: ReportData, node_id: int=-1, depth=0):
    if node_id == -1:
        node_id = report_data.root_node_id
        
    # Retrieve the current node using its ID
    node = report_data.nodes.get(node_id)
    if not node:
        return

    # Indentation to show hierarchy depth
    indent = "  " * depth
    indent_child = "  " * (depth + 1)

    
    # Print the current node's information
    print(f"{indent}Node ID: {node.id} - Key: {node.key} - Description: {""}")
    
    # For each child, print their information and recursively apply DFS
    for child in node.children:
        child_node = report_data.nodes.get(child.node_id)
        if child_node:
            # print(f"{indent}  Child ID: {child.node_id} - Description: '' - Has Children: {'Yes' if child_node.children else 'No'}")
            dfs_print(report_data, child.node_id, depth + 1)
            
            
# Function to create a response using the last node ID and auto-detect elements
def create_user_response(report_data: ReportData, last_node_id: int, guild_id: str, user_id: str):
    if report_data.name != "user":
        raise ValueError("Invalid report data name. Expected 'user'.")
    
    # Get the last node
    last_node = report_data.nodes[last_node_id]
    
    # Correctly traverse the breadcrumbs from the root to the last node
    breadcrumbs = find_breadcrumbs(last_node, report_data.nodes)

    # Detect elements generically from the nodes in the breadcrumb path
    elements = detect_elements(breadcrumbs, report_data.nodes)

    # Create the response
    response = {
        "version": report_data.version,
        "variant": report_data.variant,  # Variant can be adjusted based on your need
        "language": "en",
        "breadcrumbs": breadcrumbs,  # Full breadcrumb trail
        "elements": elements,  # Detected elements based on breadcrumb path
        "guild_id": guild_id,
        "user_id": user_id,
        "name": "user"
    }
    
    return response


def create_message_response(report_data: ReportData, last_node_id: int, guild_id: str, user_id: str):
    if report_data.name != "message":
        raise ValueError("Invalid report data name. Expected 'message'.")
    
    # Get the last node
    last_node = report_data.nodes[last_node_id]
    
    # Correctly traverse the breadcrumbs from the root to the last node
    breadcrumbs = find_breadcrumbs(last_node, report_data.nodes)

    # Detect elements generically from the nodes in the breadcrumb path
    elements = detect_elements(breadcrumbs, report_data.nodes)

    # Create the response
    response = {
        "version": report_data.version,
        "variant": report_data.variant,  # Variant can be adjusted based on your need
        "language": "en",
        "breadcrumbs": breadcrumbs,  # Full breadcrumb trail
        "elements": elements,  # Detected elements based on breadcrumb path
        "guild_id": guild_id,
        "user_id": user_id,
        "name": "message"
    }
    
    return response


def create_response(report_data: ReportData, last_node_id: int, id_1: str, id_2: str):
    if report_data.name == "message":
        return create_message_response(report_data, last_node_id, id_1, id_2)
    
    if report_data.name == "user":
        return create_user_response(report_data, last_node_id, id_1, id_2)