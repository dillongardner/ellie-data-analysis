import pandas as pd
import argparse
import os
from collections import defaultdict

# --- Configuration for Node Colors ---
COLOR_ROOT = "pink"
COLOR_MAIN_MENU_CHILD_IS_MENU = "orange"
COLOR_SUB_MENU = "yellow"
COLOR_LEAF = "lightskyblue"

# --- DOT Language Headers ---
# Header for Bus Style (matches your preferred target)
DOT_HEADER_BUS = """digraph "Speech Board Menu Tree" {
	rankdir=LR;
	splines=ortho; // Critical for the orthogonal lines
	node [shape=rect, style="rounded,filled", fontname=Helvetica]; // Default for visible nodes
	edge [fontname=Helvetica, arrowhead=none]; // Global for edges: no arrowheads

"""

# Header for Simple Style (can be similar, but splines might behave differently)
# For simple style, 'splines=polyline' or even 'splines=true' (default curved) might be better
# if 'ortho' becomes too messy without junctions. Let's keep 'ortho' for now for consistency.
DOT_HEADER_SIMPLE = """digraph "Speech Board Menu Tree" {
	rankdir=LR;
	splines=ortho; 
	nodesep=0.5; // Consider adding/adjusting these for simple style if needed
	ranksep=0.8;  // Consider adding/adjusting these for simple style if needed
	node [shape=rect, style="rounded,filled", fontname=Helvetica];
	edge [fontname=Helvetica, arrowhead=none]; // No arrowheads for consistency

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

    node_data_map = {}
    children_map = defaultdict(list)
    main_menu_node_id = "ROOT_MAIN_MENU"

    for _, row in df.iterrows():
        node_id = row['full_pattern']
        node_data_map[node_id] = {
            'label': row['selection'],
            'is_menu': row['is_menu'],
            'menu_title': str(row['menu_title']),
            'parent_id_pattern': row['menu_pattern']
        }

    for node_id, data in node_data_map.items():
        parent_id_pattern = data['parent_id_pattern']
        parent_menu_title = data['menu_title']
        actual_parent_graph_id = None

        if parent_menu_title == 'MAIN MENU' and (parent_id_pattern == "" or parent_id_pattern.lower() == 'nan'):
            actual_parent_graph_id = main_menu_node_id
        elif parent_id_pattern != "" and parent_id_pattern.lower() != 'nan':
            if parent_id_pattern in node_data_map or parent_id_pattern == main_menu_node_id:
                actual_parent_graph_id = parent_id_pattern

        if actual_parent_graph_id:
            if node_id not in children_map[actual_parent_graph_id]:
                children_map[actual_parent_graph_id].append(node_id)

    return node_data_map, children_map, main_menu_node_id


def generate_dot_string(node_data_map, children_map, main_menu_node_id, use_bus_style=True):
    """Generates the full DOT language string."""

    if use_bus_style:
        dot_lines = [DOT_HEADER_BUS]
    else:
        dot_lines = [DOT_HEADER_SIMPLE] # Or a custom header for simple style

    # --- Visible Node Definitions ---
    dot_lines.append("\t// Visible Node Definitions")
    dot_lines.append(f'\t{main_menu_node_id} [label="Main Menu", fillcolor={COLOR_ROOT}];')

    sorted_node_ids = sorted(node_data_map.keys())

    for node_id in sorted_node_ids:
        data = node_data_map[node_id]
        node_label = data['label'].replace('"', '\\"')
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
    dot_lines.append("")

    # --- Junction Node Definitions (only for bus style) ---
    if use_bus_style:
        dot_lines.append("\t// Junction Node Definitions (as points)")
        junction_parents = set()
        for parent_id, child_ids in children_map.items():
            if len(child_ids) > 1: # Only create junction if more than one child
                junction_parents.add(parent_id)

        for parent_id in sorted(list(junction_parents)):
            junction_id = f'"{parent_id}_junction"'
            dot_lines.append(f'\t{junction_id} [shape=point, label="", width=0.01, height=0.01];')
        dot_lines.append("")

    # --- Edge Definitions ---
    dot_lines.append("\t// Edge Definitions")
    sorted_parent_ids_for_edges = sorted(list(children_map.keys()))

    for parent_id in sorted_parent_ids_for_edges:
        child_ids = children_map.get(parent_id, [])
        if not child_ids:
            continue

        sorted_child_ids = sorted(child_ids)

        if use_bus_style:
            if len(sorted_child_ids) == 1:
                if parent_id == main_menu_node_id or parent_id in node_data_map:
                    dot_lines.append(f'\t{parent_id} -> {sorted_child_ids[0]};')
            else: # More than one child, use junction
                junction_id = f'"{parent_id}_junction"'
                if parent_id == main_menu_node_id or parent_id in node_data_map:
                    dot_lines.append(f'\t{parent_id} -> {junction_id};')
                    for child_id in sorted_child_ids:
                        dot_lines.append(f'\t{junction_id} -> {child_id};')
        else: # Simple style (no junctions)
            if parent_id == main_menu_node_id or parent_id in node_data_map:
                for child_id in sorted_child_ids:
                    dot_lines.append(f'\t{parent_id} -> {child_id};')

    dot_lines.append("}")
    return "\n".join(dot_lines)


# --- Main Script Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Graphviz .gv file from a speech board CSV.")
    parser.add_argument("csv_input", help="Path to the input CSV file.")
    parser.add_argument("gv_output", help="Path for the output .gv (DOT language) file.")
    parser.add_argument("--simple-edges", action="store_true",
                        help="Use simple direct edges instead of bus-style with junction nodes.")

    args = parser.parse_args()

    node_data, children_data, root_id = load_and_prepare_data(args.csv_input)

    # Determine if bus style should be used
    use_bus = not args.simple_edges # Bus style is default

    dot_content = generate_dot_string(node_data, children_data, root_id, use_bus_style=use_bus)

    try:
        gv_file_path = args.gv_output
        if not gv_file_path.lower().endswith(".gv"):
            gv_file_path += ".gv"

        with open(gv_file_path, "w", encoding="utf-8") as f:
            f.write(dot_content)
        style_message = "simple edges" if args.simple_edges else "bus style edges"
        print(f"Successfully generated DOT file ({style_message}): {os.path.abspath(gv_file_path)}")
        print(f"You can now render it using: dot -Tsvg \"{os.path.abspath(gv_file_path)}\" -o output.svg")
    except Exception as e:
        print(f"Error writing .gv file: {e}")
        exit(1)