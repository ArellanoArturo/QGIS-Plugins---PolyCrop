import os
import base64

def create_svg(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

# Icon for the plugin
icon_svg = """<svg width="32" height="32" xmlns="http://www.w3.org/2000/svg">
  <path d="M 4 28 Q 16 16 28 4" stroke="#8B4513" stroke-width="3" fill="none"/>
  <circle cx="10" cy="22" r="3" fill="#228B22"/>
  <circle cx="16" cy="16" r="3" fill="#FFD700"/>
  <circle cx="22" cy="10" r="3" fill="#FF4500"/>
</svg>"""

create_svg("icon.svg", icon_svg)

# Resources
resources_dir = "resources"
if not os.path.exists(resources_dir):
    os.makedirs(resources_dir)

tree_svg = """<svg width="24" height="24" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="14" width="4" height="10" fill="#8B4513"/>
  <path d="M 12 2 C 4 2 2 10 12 16 C 22 10 20 2 12 2" fill="#228B22"/>
</svg>"""

bush_svg = """<svg width="24" height="24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="10" fill="#32CD32"/>
  <circle cx="8" cy="8" r="4" fill="#228B22"/>
  <circle cx="16" cy="14" r="4" fill="#228B22"/>
</svg>"""

crop_svg = """<svg width="24" height="24" xmlns="http://www.w3.org/2000/svg">
  <path d="M 12 24 L 12 10" stroke="#8B4513" stroke-width="2"/>
  <path d="M 12 14 Q 6 10 12 2" stroke="#FFD700" stroke-width="3" fill="none"/>
  <path d="M 12 18 Q 18 14 12 6" stroke="#FFD700" stroke-width="3" fill="none"/>
</svg>"""

create_svg(os.path.join(resources_dir, "arbol.svg"), tree_svg)
create_svg(os.path.join(resources_dir, "arbusto.svg"), bush_svg)
create_svg(os.path.join(resources_dir, "cultivo.svg"), crop_svg)

print("Assets generated.")
