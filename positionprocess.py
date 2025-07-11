
def process_position_properties(dom_tree):
    """
    Enhanced grid position processor with:
    - Proper column-flow handling
    - Nested grid context isolation
    - Column count awareness
    """

    def _process_node(node, parent_grid=None, is_first_child=False):
        if not isinstance(node, dict):
            return

        # Initialize grid if not exists
        if 'grid' not in node:
            node['grid'] = {}
        grid = node['grid']

        # Create current grid context
        current_grid = {
            'columns': 1,
            'rows': 1,
            'auto_flow': grid.get('grid-auto-flow', 
                                 parent_grid['auto_flow'] if parent_grid else 'row'),
            'is_grid_container': grid.get('display') == 'grid',
            'max_columns': _get_max_columns(grid)
        }

        # Normalize shorthand properties
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

        # Calculate positions
        _calculate_grid_position(node, parent_grid, current_grid, is_first_child)

        # Process children
        children = node.get('component', [])
        for i, child in enumerate(children):
            _process_node(child, current_grid, i == 0)

    def _calculate_grid_position(node, parent_grid, current_grid, is_first_child):
        grid = node.get('grid', {})
        row_start = grid.get('grid-row-start', 'auto')
        col_start = grid.get('grid-column-start', 'auto')

        # Rule 1: Explicit position takes precedence
        if row_start != 'auto' and col_start != 'auto':
            try:
                grid['pos-row'] = int(row_start)
                grid['pos-col'] = int(col_start)
                return
            except (ValueError, TypeError):
                pass

        # Rule 2: Handle span values
        if isinstance(row_start, str) and row_start.startswith('span'):
            grid['pos-row'] = 1
        if isinstance(col_start, str) and col_start.startswith('span'):
            grid['pos-col'] = 1

        # Rule 3: Auto placement
        if parent_grid:
            if parent_grid['auto_flow'] == 'column':
                # Column-major logic
                if parent_grid['columns'] > parent_grid.get('max_columns', 3):
                    parent_grid['columns'] = 1
                    parent_grid['rows'] += 1

                grid['pos-row'] = parent_grid['rows']
                grid['pos-col'] = parent_grid['columns']
                parent_grid['columns'] += 1
            else:
                # Row-major logic (default)
                grid['pos-row'] = parent_grid['rows']
                grid['pos-col'] = parent_grid['columns']
                parent_grid['rows'] += 1
        else:
            # Root element defaults
            grid.setdefault('pos-row', 1)
            grid.setdefault('pos-col', 1)

    def _get_max_columns(grid):
        """Extracts column count from grid-template-columns"""
        if 'grid-template-columns' in grid:
            parts = grid['grid-template-columns'].split()
            if 'repeat(' in parts[0]:
                try:
                    return int(parts[0].split('(')[1].split(',')[0])
                except (IndexError, ValueError):
                    pass
            return len(parts)
        return None  # Indicates implicit grid

    def _parse_grid_line(line_value):
        """Converts shorthand grid lines"""
        if isinstance(line_value, str):
            if '/' in line_value:
                return tuple(part.strip() for part in line_value.split('/', 1))
            elif line_value.startswith('span'):
                return ('auto', line_value)
        return (line_value, line_value + 1)

    _process_node(dom_tree)
    return dom_tree