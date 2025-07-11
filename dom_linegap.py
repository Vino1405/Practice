import re
import json
import random
import string
import webcolors
# from app.parsing.grid_properties import compute_dom_positions
from grid_detector import process_grid_containers
 
SELF_CLOSING_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
                     "link", "meta", "param", "source", "track", "wbr"}
 
GRID_PROPERTIES = {
    "display", "grid", "grid-template", "grid-template-areas", "grid-template-rows",
    "grid-template-columns", "grid-auto-rows", "grid-auto-columns", "grid-auto-flow",
    "grid-column-gap", "grid-row-gap", "gap", "justify-items", "align-items",
    "place-items", "justify-content", "align-content", "place-content"
}
 
class HTMLNode:
    def __init__(self, tag, attributes=None, parent=None, is_text=False):
        self.tag = tag.lower() if not is_text else "text"
        self.attributes = attributes or {}
        self.children = []
        self.parent = parent
        self.is_text = is_text
        self.styles = {}
        self.text_content = ""
        self.proxy = []  # Track line gaps and <br> tags
 
    def add_text(self, text):
        self.text_content += text
 
    def apply_styles(self, css_rules):                                                  
        for selector, properties in css_rules.items():
            if self.matches(selector):
                self.styles.update(self._convert_em_to_px(properties))
        for child in self.children:
            child.apply_styles(css_rules)
 
    def _is_named_color(self, color_name):
        """Check if a string is a valid CSS color name"""
        try:
            webcolors.name_to_hex(color_name)
            return True
        except ValueError:
            return False
   
    def _convert_em_to_px(self, properties, base_px=16):
        converted = {}
        color_props = {'background', 'background-color', 'color', 'border-color',
                    'border-top-color', 'border-right-color', 'border-bottom-color',
                    'border-left-color'}
        border_props = {'border', 'border-top', 'border-right', 'border-bottom', 'border-left'}
 
        for prop, value in properties.items():
            if isinstance(value, str):
                value = value.strip().lower()
                try:
                    # Handle border properties - only convert non-hex colors
                    if prop in border_props:
                        # Split border value into parts
                        parts = value.split()
                        new_parts = []
                        for part in parts:
                            # Check if part is a color that needs conversion
                            if (part.startswith('#') and len(part) != 7) or (  # 3-digit hex or invalid
                                part.startswith(('rgb(', 'rgba(')) or  # rgb/rgba
                                (not part.startswith('#') and self._is_named_color(part))):  # named colors
                                new_parts.append('#000000')
                            else:
                                new_parts.append(part)
                        converted[prop] = ' '.join(new_parts)
                   
                    # Rest of the method remains the same...
                    elif 'rem' in value or 'em' in value:
                        parts = value.split()
                        px_parts = []
                        for part in parts:
                            if part.endswith('rem'):
                                num = float(part.replace('rem', ''))
                                px_parts.append(f"{round(num * base_px)}px")
                            elif part.endswith('em'):
                                num = float(part.replace('em', ''))
                                px_parts.append(f"{round(num * base_px)}px")
                            else:
                                px_parts.append(part)
                        converted[prop] = ' '.join(px_parts)
 
                    elif prop in color_props:
                        converted[prop] = self._convert_to_hex_color(value)
 
                    else:
                        if prop == 'background':
                            converted['background-color'] = value
                        else:
                            converted[prop] = value
 
                except ValueError:
                    converted[prop] = value
            else:
                converted[prop] = value
        return converted
 
 
 
   
    def _convert_to_hex_color(self, color):
        """
        Convert various color formats to hexadecimal
        :param color: Color in any supported format
        :return: Hexadecimal color string (e.g., "#ff0000")
                Returns "#ff0000" (red) for any unconvertable format
        """
        if isinstance(color, str):
            color = color.strip().lower()
           
            # Handle rgb/rgba colors
            if color.startswith(('rgb(', 'rgba(')):
                try:
                    values = color.split('(')[1].split(')')[0]
                    components = [c.strip() for c in values.split(',')]
                    r, g, b = map(int, components[:3])
                    return '#{:02x}{:02x}{:02x}'.format(
                        max(0, min(255, r)),
                        max(0, min(255, g)),
                        max(0, min(255, b)))
                except (ValueError, IndexError):
                    return "#ff0000"  # Fallback to red
           
            # Try named color
            try:
                return webcolors.name_to_hex(color)
            except ValueError:
                pass  # Continue to hex parsing
           
            # Handle hex colors
            if color.startswith('#'):
                color = color[1:]
           
            if len(color) == 3 and all(c in '0123456789abcdef' for c in color):
                return f"#{color[0]}{color[0]}{color[1]}{color[1]}{color[2]}{color[2]}"
           
            if len(color) == 6 and all(c in '0123456789abcdef' for c in color):
                return f"#{color}"
           
            return "#ff0000"  # Fallback to red
       
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            try:
                r, g, b = map(int, color[:3])
                return '#{:02x}{:02x}{:02x}'.format(
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b)))
            except (ValueError, TypeError):
                return "#ff0000"  # Fallback to red
       
        return "#ff0000"  # Fallback to red for all other cases
 
    def matches(self, selector):                                            
        selector_parts = selector.strip().lower().split()
        if not selector_parts:
            return False
 
        current_part = selector_parts[-1]
        if not self._matches_single_part(current_part):
            return False
 
        ancestor_parts = selector_parts[:-1]
        current_ancestor = self.parent
        for part in reversed(ancestor_parts):
            found = False
            while current_ancestor:
                if current_ancestor._matches_single_part(part):
                    found = True
                    current_ancestor = current_ancestor.parent
                    break
                current_ancestor = current_ancestor.parent
            if not found:
                return False
        return True
 
    def _matches_single_part(self, part):
        if "[" in part:
            tag_part, attr_part = part.split("[", 1)
            attr_part = attr_part.split("]")[0]
            if tag_part and tag_part != self.tag:
                return False
            attr_name, _, attr_value = attr_part.partition("=")
            attr_name = attr_name.strip()
            attr_value = attr_value.strip(' "\'') if attr_value else None
            if attr_value:
                return self.attributes.get(attr_name) == attr_value
            return attr_name in self.attributes
        else:
            if part.startswith("."):
                class_name = part[1:]
                return class_name in self.attributes.get("class", "").split()
            elif part.startswith("#"):
                id_name = part[1:]
                return id_name == self.attributes.get("id", "")
            else:
                return self.tag == part
 
    def to_json(self):                                                  
        grid = {}
        style = {}
        for prop, value in self.styles.items():
            if prop in GRID_PROPERTIES:
                grid[prop] = value
            else:
                style[prop] = value
 
        attributes = self.attributes.copy()
        if self.text_content.strip():
            attributes["value"] = self.text_content.strip()
 
        name = ""
        if "id" in attributes:
            name = attributes["id"]
        elif "value" in attributes:
            name = str(attributes["value"])
        elif "name" in attributes:
            name = attributes["name"]
        else:
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            name = f"auto_{random_str}"
 
        json_tag = self.tag
        if self.tag == "body":
            json_tag = "div"
        elif self.tag == "input" and "type" in self.attributes:
            input_type = self.attributes["type"].lower()
            if input_type == "radio":
                json_tag = "radio"
            elif input_type == "checkbox":
                json_tag = "checkbox"
            elif input_type == "text":
                json_tag = "textbox"
            elif input_type == "date":
                json_tag = "datepicker"
            elif input_type == "password":
                json_tag = "password"
            elif input_type == "file":
                json_tag = "file"
            elif input_type == "email":
                json_tag = "textbox"
            elif input_type == "tel":
                json_tag = "textbox"
 
        elif self.tag == "select":
            json_tag = "dropdown"
        elif self.tag == "a":
            json_tag = "link"
        elif self.tag == "p":
            json_tag = "label"
       
 
       # Special case: label with checkbox or radio input
        if self.tag == "label":
            for child in self.children:
                if child.tag == "input" and child.attributes.get("type", "").lower() in ("checkbox", "radio"):
                    input_json = child.to_json()
                    label_json = {
                        "name": name,
                        "tag": "label",
                        "component": [],
                        "grid": grid,
                        "style": style,
                        "attributes": {"value": self.text_content.strip()}
                    }
                    components = [input_json, label_json]
                    if self.proxy:
                        components.extend([{"proxy": proxy} for proxy in self.proxy])
 
                    return {
                        "name": f"{name}",
                        "tag": "div",
                        "component": components,
                        "grid": {},
                        "style": {},
                        "attributes": {}
                    }
               
        # Process children and handle proxies
        components = []
        for child in self.children:
            child_json = child.to_json()
            components.append(child_json)
           
            # Add proxy as separate component after the child
            if child.proxy:
                for proxy in child.proxy:
                    components.append({"proxy": proxy})
 
        output = {
            "name": name,
            "tag": json_tag,
            "component": components,
            "grid": grid,
            "style": style,
            "attributes": attributes
        }
 
 
        return output
class CSSParser:
    def __init__(self, css):
        self.css = css
 
    def parse(self):
        rules = {}
        # Remove all CSS comments first
        css_without_comments = re.sub(r'/\*.*?\*/', '', self.css, flags=re.DOTALL)
        # Then remove @media rules
        css_without_media = re.sub(r'@media\s*.*?{.*?}', '', css_without_comments, flags=re.DOTALL)
       
        for match in re.findall(r"([^{]+){([^}]+)}", css_without_media):
            selectors, declarations = match
            properties = self.parse_declarations(declarations)
            for selector in selectors.split(","):
                cleaned_selector = selector.strip()
                if cleaned_selector:
                    rules[cleaned_selector] = properties
        return rules
 
    def parse_declarations(self, declarations):
        properties = {}
        # Remove any remaining comments in declarations
        declarations = re.sub(r'/\*.*?\*/', '', declarations)
        for declaration in declarations.split(";"):
            declaration = declaration.strip()
            if ":" in declaration:
                prop, value = map(str.strip, declaration.split(":", 1))
                properties[prop] = value
        return properties
 
 
 
class HTMLParser:
    def __init__(self, html):
        self.html = html
        self.root = HTMLNode("html")
        self.stack = [self.root]
        self.errors = []
 
    def parse(self):
        lines = self.html.splitlines()
        token_pattern = r"<!--.*?-->|<[^>]+>|[^<]+"  # tokens: comments, tags, or text
        tokens = []
 
        for line in lines:
            if line.strip() == "":
                tokens.append({'type': 'linegap'})
            else:
                for match in re.finditer(token_pattern, line, re.DOTALL):
                    tokens.append({'type': 'token', 'value': match.group(0)})
 
        for item in tokens:
            if item['type'] == 'linegap':
                if self.stack:
                    current_parent = self.stack[-1]
                    # Attach line gap to last child if exists, else to parent
                    if current_parent.children:
                        target_node = current_parent.children[-1]
                    else:
                        target_node = current_parent
                    if "linegap" not in target_node.proxy:
                        target_node.proxy.append("linegap")
                continue
 
            token = item['value'].strip()
            if not token:
                continue
            if not self.stack:
                continue
 
            if token.startswith("<") and not token.startswith("</"):
                self.handle_open_tag(token[1:-1].strip())
            elif token.startswith("</"):
                self.handle_close_tag(token[2:-1].strip())
            else:
                self.add_text(token)
 
        # Check for unclosed tags
        if len(self.stack) > 1:
            unclosed = [node.tag for node in self.stack[1:]]
            self.errors.append(f"Error: Unclosed tags detected: {', '.join(unclosed)}")
        self.finalize_dom_tree()
       
        return self.root
 
    def finalize_dom_tree(self):
        """Close all remaining open tags and report unclosed tags"""
        if len(self.stack) > 1:  # More than just root remains
            unclosed_tags = [node.tag for node in self.stack[1:]]
            self.errors.append(f"Warning: Auto-closed unclosed tags: {', '.join(unclosed_tags)}")
           
            # Close all tags except root
            while len(self.stack) > 1:
                self.stack.pop()
 
    def handle_open_tag(self, tag):
        if tag.startswith("!"):
            return
 
        parts = tag.split(maxsplit=1)
        tag_name = parts[0].lower()
        attributes = {}
 
        if len(parts) > 1:
            attributes = self.parse_attributes(parts[1])
 
        if tag_name == "html" and self.stack[-1] is self.root:
            self.root.attributes.update(attributes)
            return
 
        parent = self.stack[-1]
        node = HTMLNode(tag_name, attributes, parent)
        parent.children.append(node)
 
        if tag_name == "br":
            node.proxy.append("br")
 
        if tag_name not in SELF_CLOSING_TAGS:
            self.stack.append(node)
 
    def parse_attributes(self, attr_str):
        attributes = {}
        attr_matches = re.findall(
            r'([\w\-:]+)(?:=(".*?"|\'.*?\'|\S+))?', attr_str)
 
        for key, value in attr_matches:
            key = key.lower()
            processed_value = True
 
            if value:
                if value.startswith(("'", '"')) and value.endswith(("'", '"')):
                    processed_value = value[1:-1]
                else:
                    processed_value = value
 
                if isinstance(processed_value, str) and processed_value.isdigit():
                    processed_value = int(processed_value)
                else:
                    try:
                        processed_value = float(processed_value)
                    except ValueError:
                        pass
 
            attributes[key] = processed_value
 
        return attributes
 
    def handle_close_tag(self, tag):
        tag = tag.lower()
        found = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                found = True
                break
        if not found:
            self.errors.append(f"Error: Unmatched closing tag </{tag}>")
 
    def add_text(self, text):
        text = text.strip()
        if text:
            self.stack[-1].add_text(text)
 
def main():
    html_file = "sizetest.html"
    css_file = "sizetest.css"
    output_file = "sizetest.json"
 
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
 
    with open(css_file, "r", encoding="utf-8") as f:
        css = f.read()
 
    html_parser = HTMLParser(html)
    dom = html_parser.parse()
 
    if html_parser.errors:
        print("HTML validation errors:")
        for error in html_parser.errors:
            print(f"  - {error}")
 
    css_parser = CSSParser(css)
    css_rules = css_parser.parse()
 
    dom.apply_styles(css_rules)
 
    body_node = next((child for child in dom.children if child.tag == "body"), None)
    if body_node:
       # Step 1: Convert to JSON and compute basic positions
        # output = compute_dom_positions(body_node.to_json())
    # Step 2: Process grid containers and their position properties
        output = process_grid_containers(body_node.to_json())
    else:
        output = {"error": "No <body> tag found"}
 
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
 
    print(f"Generated JSON output at {output_file}")
 
if __name__ == "__main__":
    main()
 