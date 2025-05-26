import pandas as pd
# No need for graphviz library if we are just generating the DOT string
import argparse
import os
from collections import defaultdict

# --- Configuration for Node Colors ---
COLOR_ROOT = "pink"
COLOR_MAIN_MENU_CHILD_IS_MENU = "orange"
COLOR_SUB_MENU = "yellow"
COLOR_LEAF = "lightskyblue"

# --- DOT Language Strings ---
DOT_HEADER = """digraph "Speech Board Menu Tree" {
	rankdir=LR;
	splines=polyline;
	nodesep=0.8; 
	ranksep=1.2;
	node [shape=rect, style="rounded,filled", fontname=Helvetica];
	edge [fontname=Helvetica, arrowhead=none];

""" # Removed nodesep and ranksep from example as they were not in the target, but can be added back.
# Your target DOT did not have nodesep and ranksep, so I'll match that.
# If you want them, uncomment and adjust the lines above.
# Let's use the exact header from your target:
DOT_HEADER_TARGET = """digraph "Speech Board Menu Tree" {
	rankdir=LR;
	splines=ortho; // Critical for the orthogonal lines
	node [shape=rect, style="rounded,filled", fontname=Helvetica]; // Default for visible nodes
	edge [fontname=Helvetica, arrowhead=none]; // Global for edges: no arrowheads

"""


def load_and_prepare_data(csv_filepath):
    """Loads CSV, cleans it, and prepares node and children maps."""
    try:
        df = pd.read_csv(csv_filepath)
    except FileNotFoundError:
        print(f"Error: The file '{csv_filepath}' was not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading CSV file '{csv_filepath}': {e}")
        exit(1)

    df = df[df['selection'].notna()]
    df['selection'] = df['selection'].astype(str).str.strip()
    df = df[df['selection'] != '']

    df['is_menu'] = df['is_menu'].astype(bool)
    df['full_pattern'] = df['full_pattern'].astype(str)
    df['menu_pattern'] = df['menu_pattern'].astype(str).str.strip()

    node_data_map = {} # node_id -> {label, is_menu, menu_title, parent_id_pattern}
    children_map = defaultdict(list) # parent_id -> list of child_ids

    main_menu_node_id = "ROOT_MAIN_MENU"

    # First pass: gather all node data
    for _, row in df.iterrows():
        node_id = row['full_pattern']
        node_data_map[node_id] = {
            'label': row['selection'],
            'is_menu': row['is_menu'],
            'menu_title': str(row['menu_title']),
            'parent_id_pattern': row['menu_pattern']
        }

    # Second pass: build children_map using the populated node_data_map
    # This ensures parent_id_pattern correctly refers to existing node_ids
    for node_id, data in node_data_map.items():
        parent_id_pattern = data['parent_id_pattern']
        parent_menu_title = data['menu_title']
        actual_parent_graph_id = None

        if parent_menu_title == 'MAIN MENU' and (parent_id_pattern == "" or parent_id_pattern.lower() == 'nan'):
            actual_parent_graph_id = main_menu_node_id
        elif parent_id_pattern != "" and parent_id_pattern.lower() != 'nan':
            # Check if this parent_id_pattern corresponds to an existing node defined in node_data_map
            if parent_id_pattern in node_data_map or parent_id_pattern == main_menu_node_id:
                actual_parent_graph_id = parent_id_pattern
            # else:
            # print(f"Debug: Parent pattern '{parent_id_pattern}' for node '{node_id}' not in node_data_map during children_map build.")

        if actual_parent_graph_id:
            if node_id not in children_map[actual_parent_graph_id]:
                children_map[actual_parent_graph_id].append(node_id)

    return node_data_map, children_map, main_menu_node_id


def generate_dot_string(node_data_map, children_map, main_menu_node_id):
    """Generates the full DOT language string for the bus style."""
    dot_lines = [DOT_HEADER_TARGET] # Use the target header

    # --- Visible Node Definitions ---
    dot_lines.append("\t// Visible Node Definitions")
    dot_lines.append(f'\t{main_menu_node_id} [label="Main Menu", fillcolor={COLOR_ROOT}];')

    # Sort node_ids for consistent output order (helps with diffing)
    sorted_node_ids = sorted(node_data_map.keys())

    for node_id in sorted_node_ids:
        data = node_data_map[node_id]
        node_label = data['label'].replace('"', '\\"') # Escape double quotes in labels
        is_menu = data['is_menu']
        parent_menu_title = data['menu_title']
        node_color = ""

        if parent_menu_title == 'MAIN MENU':
            node_color = COLOR_MAIN_MENU_CHILD_IS_MENU if is_menu else COLOR_LEAF
        elif is_menu:
            node_color = COLOR_SUB_MENU
        else:
            node_color = COLOR_LEAF

        dot_lines.append(f'\t{node_id} [label="{node_label}", fillcolor={node_color}];')
    dot_lines.append("") # Newline for readability

    # --- Junction Node Definitions ---
    dot_lines.append("\t// Junction Node Definitions (as points)")
    # Collect all parent_ids that will need a junction (have more than 1 child)
    junction_parents = set()
    for parent_id, child_ids in children_map.items():
        if len(child_ids) > 1:
            junction_parents.add(parent_id)

    for parent_id in sorted(list(junction_parents)):
        junction_id = f'"{parent_id}_junction"' # Quote if parent_id could have special chars, though full_pattern shouldn't
        dot_lines.append(f'\t{junction_id} [shape=point, label="", width=0.01, height=0.01];')
    dot_lines.append("")

    # --- Edge Definitions ---
    dot_lines.append("\t// Edge Definitions")
    # Iterate through parents in a sorted order for consistency
    sorted_parent_ids_for_edges = sorted(list(children_map.keys()))

    for parent_id in sorted_parent_ids_for_edges:
        child_ids = children_map.get(parent_id, [])
        if not child_ids:
            continue

        # Sort children for consistent edge order
        sorted_child_ids = sorted(child_ids)

        if len(sorted_child_ids) == 1:
            # Single child, direct edge
            # Ensure parent_id itself is a defined node or the root
            if parent_id == main_menu_node_id or parent_id in node_data_map:
                dot_lines.append(f'\t{parent_id} -> {sorted_child_ids[0]};')
        else:
            # Multiple children, use junction node
            junction_id = f'"{parent_id}_junction"'
            if parent_id == main_menu_node_id or parent_id in node_data_map:
                # This is the critical line from your target DOT
                dot_lines.append(f'\t{parent_id} -> {junction_id};') # No [constraint=false] in target for this line
                for child_id in sorted_child_ids:
                    dot_lines.append(f'\t{junction_id} -> {child_id};')
            # else:
            # print(f"Warning (Bus Style - Multi Child): Parent ID '{parent_id}' for junction '{junction_id}' not a defined node.")

    dot_lines.append("}") # Close the digraph
    return "\n".join(dot_lines)


# --- Main Script Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Graphviz .gv file from a speech board CSV (bus style only).")
    parser.add_argument("csv_input", help="Path to the input CSV file.")
    parser.add_argument("gv_output", help="Path for the output .gv (DOT language) file.")

    args = parser.parse_args()

    node_data, children_data, root_id = load_and_prepare_data(args.csv_input)

    dot_content = generate_dot_string(node_data, children_data, root_id)

    try:
        gv_file_path = args.gv_output
        if not gv_file_path.lower().endswith(".gv"):
            gv_file_path += ".gv"

        with open(gv_file_path, "w", encoding="utf-8") as f: # Specify encoding
            f.write(dot_content)
        print(f"Successfully generated DOT file: {os.path.abspath(gv_file_path)}")
        print(f"You can now render it using: dot -Tsvg \"{os.path.abspath(gv_file_path)}\" -o output.svg")
    except Exception as e:
        print(f"Error writing .gv file: {e}")
        exit(1)