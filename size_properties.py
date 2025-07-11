import re

def process_grid_sizing(dom_tree):
    """
    Processes CSS grid sizing properties in a DOM-like JSON tree.
    Uses 'grid' key for grid-specific styles.
    Handles:
    - grid-template, grid-template-rows, grid-template-columns
    - grid-auto-rows, grid-auto-columns
    - gap, grid-gap, grid-row-gap, grid-column-gap
    """

    def is_grid_container(styles):
        return styles.get("display") in ("grid", "inline-grid")

    def parse_template_value(value):
        if not value or value.strip() == "none":
            return []

        value = value.strip()

        # Handle repeat(n, value)
        repeat_matches = re.findall(r"repeat\((\d+),\s*([^\)]+)\)", value)
        if repeat_matches:
            expanded = []
            for count, unit in repeat_matches:
                expanded.extend([unit.strip()] * int(count))
            return expanded

        # Leave minmax() or nested expressions untouched
        if "minmax(" in value or "(" in value:
            return [value]

        # Otherwise, split by space
        return [v.strip() for v in value.split() if v.strip()]

    def split_gap_shorthand(gap_value):
        if not gap_value:
            return None, None
        values = gap_value.strip().split()
        if len(values) == 1:
            return values[0], values[0]
        elif len(values) == 2:
            return values[0], values[1]
        return None, None

    def validate_size_value(value):
        return bool(value.strip()) if isinstance(value, str) else False

    def process_element(element):
        styles = element.get("grid", {})

        if not is_grid_container(styles):
            # Process children even if not a grid container
            for child in element.get("component", []):
                if isinstance(child, dict):
                    process_element(child)
            return

        # Step 1: Handle grid-template shorthand
        if "grid-template" in styles:
            template_value = styles.pop("grid-template")
            if "/" in template_value:
                rows_part, cols_part = map(str.strip, template_value.split("/", 1))
                if rows_part:
                    styles["grid-template-rows"] = rows_part
                if cols_part:
                    styles["grid-template-columns"] = cols_part
            else:
                styles["grid-template-rows"] = template_value

        # Step 2: Handle gap and grid-gap
        for gap_prop in ["gap", "grid-gap"]:
            if gap_prop in styles:
                row_gap, col_gap = split_gap_shorthand(styles.pop(gap_prop))
                if row_gap and "grid-row-gap" not in styles:
                    styles["grid-row-gap"] = row_gap
                if col_gap and "grid-column-gap" not in styles:
                    styles["grid-column-gap"] = col_gap


        # Step 3: Parse grid-template-rows and columns
        for prop in ["grid-template-rows", "grid-template-columns"]:
            if prop in styles:
                parsed = parse_template_value(styles[prop])
                if parsed:
                    styles[prop] = " ".join(parsed)
                else:
                    styles.pop(prop, None)

        # Step 4: Clean invalid grid-auto-rows and columns
        for prop in ["grid-auto-rows", "grid-auto-columns"]:
            if prop in styles and not validate_size_value(styles[prop]):
                styles.pop(prop, None)

        # Step 5: Clean invalid gaps
        for prop in ["grid-row-gap", "grid-column-gap"]:
            if prop in styles and not validate_size_value(styles[prop]):
                styles.pop(prop, None)

        # Step 6: Recursively process children
        for child in element.get("component", []):
            if isinstance(child, dict):
                process_element(child)

    # Start processing at root
    process_element(dom_tree)
    return dom_tree
