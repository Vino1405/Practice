# Grid Alignment Processor Module

This module defines a function `process_grid_alignment` that processes a JSON-like DOM tree to apply and validate CSS Grid alignment properties. It expands shorthand alignment properties, validates their values, and ensures proper inheritance for grid containers and their children.

##  Module: `alignment_properties.py`

###  Function: `process_grid_alignment(dom_tree)`
Processes the grid alignment properties in a nested DOM-like dictionary structure.

####  Input:
- `dom_tree` *(dict)*: The root of a DOM-like tree. Each node may contain:
  - `grid` (dict): CSS Grid-related properties (`display`, `place-items`, etc.)
  - `style` (dict): Other CSS properties (e.g., `justify-self`, `align-self`)
  - `component` (list): Child elements (if any)

####  What it does:
- Identifies grid containers using `display: grid` or `inline-grid`.
- Converts shorthand:
  - `place-items` → `align-items` + `justify-items`
  - `place-content` → `align-content` + `justify-content`
- Validates alignment property values against a whitelist.
- Moves `align-self` and `justify-self` from `style` to `grid` for child elements.
- Ensures all alignment values are valid or replaced with defaults (`start`, `auto`).

### Valid Alignment Values:
| Property           | Allowed Values                                       |
|--------------------|------------------------------------------------------|
| `justify-items`    | `start`, `end`, `center`, `stretch`                 |
| `align-items`      | `start`, `end`, `center`, `stretch`, `baseline`     |
| `justify-content`  | `start`, `end`, `center`, `stretch`, `space-*`      |
| `align-content`    | `start`, `end`, `center`, `stretch`, `space-*`      |
| `justify-self`     | `start`, `end`, `center`, `stretch`, `auto`         |
| `align-self`       | `start`, `end`, `center`, `stretch`, `baseline`, `auto` |

### Example Usage:
```python
from alignment_properties import process_grid_alignment

# Input DOM-like dictionary
dom = {
    "grid": {
        "display": "grid",
        "place-content": "center stretch"
    },
    "component": []
}


# Process grid alignment
processed = process_grid_alignment(dom)
