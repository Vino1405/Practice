# grid_detector.py
from position import process_position_properties
 
def process_grid_containers(dom_tree):
    """
    Finds all nodes with display:grid and processes their position properties
    """
    def _traverse(node):
        if not isinstance(node, dict):
            return
       
        # Check if current node is a grid container
        if _is_grid_container(node):
            process_position_properties(node)
       
        # Process children recursively
        for child in node.get('component', []):
            _traverse(child)
   
    def _is_grid_container(node):
        """Check if node has display:grid"""
        style = node.get('style', {})
        grid = node.get('grid', {})
        return (style.get('display') == 'grid' or
                grid.get('display') == 'grid' or
                node.get('attributes', {}).get('display') == 'grid')
   
    _traverse(dom_tree)
    return dom_tree
 