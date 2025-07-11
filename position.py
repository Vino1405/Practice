# position_processor.py
import json
import copy
from alignment_properties import process_grid_alignment
from size_properties import process_grid_sizing

 
def process_position_properties(dom_tree):
    """
    Processes all position-related grid properties and calculates pos-row/pos-col
    based on grid positioning behavior.
    """
   
    def _process_node(node, parent_grid=None):
        if not isinstance(node, dict):
            return
    
       
        # Store parent grid info for reference
        current_grid = {
            'columns': parent_grid['columns'] if parent_grid else 1,
            'rows': parent_grid['rows'] if parent_grid else 1,
            'auto_flow': parent_grid.get('grid-auto-flow', 'row') if parent_grid else 'row'
        }
       
        # 1. Normalize shorthand properties first
        if 'grid-row' in grid:
            start, end = _parse_grid_line(grid['grid-row'])
            grid['grid-row-start'] = start
            grid['grid-row-end'] = end
            del grid['grid-row']
       
        if 'grid-column' in grid:
            start, end = _parse_grid_line(grid['grid-column'])
            grid['grid-column-start'] = start
            grid['grid-column-end'] = end
            del grid['grid-column']
       
        # 2. Calculate pos-row and pos-col based on position properties
        _calculate_grid_position(node, current_grid)
       
        # 3. Handle grid-auto-flow if present
        if 'grid-auto-flow' in grid:
            current_grid['auto_flow'] = grid['grid-auto-flow']
       
        # Process children with current grid context
        for child in node.get('component', []):
            _process_node(child, current_grid)
   
    def _calculate_grid_position(node, parent_grid):
        """Calculate pos-row and pos-col based on grid position properties"""
        grid = node.get('grid', {})
       
        # Default to auto placement
        row_start = grid.get('grid-row-start', 'auto')
        row_end = grid.get('grid-row-end', 'auto')
        col_start = grid.get('grid-column-start', 'auto')
        col_end = grid.get('grid-column-end', 'auto')
       
        # Rule 1: Explicit position takes precedence
        if all(p != 'auto' for p in [row_start, row_end, col_start, col_end]):
            try:
                grid['pos-row'] = int(row_start)
                grid['pos-col'] = int(col_start)
                return
            except (ValueError, TypeError):
                pass
       
        # Rule 2: Handle span values
        if isinstance(row_start, str) and row_start.startswith('span'):
            grid['pos-row'] = 1  # Default row for span
        if isinstance(col_start, str) and col_start.startswith('span'):
            grid['pos-col'] = 1  # Default column for span
       
        # Rule 3: Auto placement based on parent's grid-auto-flow
        if parent_grid['auto_flow'] == 'column':
            # Column-major order
            grid['pos-row'] = 1
            if 'pos-col' not in grid:
                grid['pos-col'] = parent_grid['columns'] + 1
                parent_grid['columns'] += 1
        else:
            # Row-major order (default)
            grid['pos-col'] = 1
            if 'pos-row' not in grid:
                grid['pos-row'] = parent_grid['rows'] + 1
                parent_grid['rows'] += 1
       
        # Rule 4: Handle partially specified positions
        if row_start != 'auto' and col_start == 'auto':
            try:
                grid['pos-row'] = int(row_start)
                grid['pos-col'] = 1  # Start new row
            except (ValueError, TypeError):
                pass
       
        if col_start != 'auto' and row_start == 'auto':
            try:
                grid['pos-col'] = int(col_start)
                grid['pos-row'] = 1  # Start new column
            except (ValueError, TypeError):
                pass
   
    def _parse_grid_line(line_value):
        """Converts shorthand like '1 / 3' → (1, 3) or 'span 2' → (auto, span 2)"""
        if isinstance(line_value, str):
            if '/' in line_value:
                start, end = line_value.split('/', 1)
                return start.strip(), end.strip()
            elif line_value.startswith('span'):
                return ('auto', line_value)
        return (line_value, line_value + 1)
   
    _process_node(dom_tree)
    return dom_tree
 
def process_grid_positions(input_json):
    """
    Processes grid position properties in a DOM tree JSON and returns the modified JSON
    with calculated pos-row and pos-col values.

    Args:
        input_json: Input DOM tree as a JSON-compatible dictionary

    Returns:
        dict: Modified DOM tree with grid position properties normalized
              and pos-row/pos-col calculated for all elements.
    """
    if not isinstance(input_json, dict):
        raise ValueError("Input must be a JSON-compatible dictionary")

    dom_tree = copy.deepcopy(input_json)

    # Step 1: Process alignment properties (align-items, justify-items, etc.)
    process_grid_alignment(dom_tree)

    # Step 2: Process sizing properties (grid-template-rows, grid-auto-rows, etc.)
    process_grid_sizing(dom_tree)

    # Step 3: Process position properties (grid-row-start, pos-row, etc.)
    processed_tree = process_position_properties(dom_tree)

    return processed_tree

 
def process_dom_file(input_file="sizetest.json", output_file="sizetestoutput.json"):
    """
    Process DOM tree from input file and save result to output file
   
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
    """
    try:
        # Read input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            dom_tree = json.load(f)
 
        print("Original DOM Tree:")
        print(json.dumps(dom_tree, indent=2, ensure_ascii=False))
       
        # Compute positions and modify the DOM tree
        modified_dom = process_grid_positions(dom_tree)
       
        # Save to output JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(modified_dom, f, indent=2, ensure_ascii=False)
       
        print(f"Successfully processed {input_file} and saved result to {output_file}")
        return modified_dom
       
    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_file}'")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file - {e}")
    except Exception as e:
        print(f"Error: {e}")
 
# Example Usage
if __name__ == "__main__":
    # Example 1: Process from file
    process_dom_file("sizetest.json", "sizeoutputtest.json")
   
    # processed = process_grid_positions(sample_input)
    # print("\nProcessed Sample:")
    # print(json.dumps(processed, indent=2))