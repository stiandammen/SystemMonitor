import os
import re

# First fix the mess
fix_mappings = [
    (r'systemmonitor\.typing_ext_ext', 'systemmonitor.typing_ext'),
    (r'systemmonitor\.enumss', 'systemmonitor.enums'),
    (r'systemmonitor\.paths_ext_ext', 'systemmonitor.paths_ext'),
    (r'systemmonitor\.datetime_ext_ext', 'systemmonitor.datetime_ext'),
]

# Then ensure everything is correct using word boundaries
final_mappings = [
    (r'systemmonitor\.typing\b', 'systemmonitor.typing_ext'),
    (r'systemmonitor\.enum\b', 'systemmonitor.enums'),
    (r'systemmonitor\.pathlib\b', 'systemmonitor.paths_ext'),
    (r'systemmonitor\.datetime\b', 'systemmonitor.datetime_ext'),
    (r'from \.typing\b', 'from .typing_ext'),
    (r'from \.enum\b', 'from .enums'),
    (r'from \.pathlib\b', 'from .paths_ext'),
    (r'from \.datetime\b', 'from .datetime_ext'),
    (r'from \.\.typing\b', 'from ..typing_ext'),
    (r'from \.\.enum\b', 'from ..enums'),
    (r'from \.\.pathlib\b', 'from ..paths_ext'),
    (r'from \.\.datetime\b', 'from ..datetime_ext'),
]

root_dir = r'E:\[python - prosjekter]\SystemMonitor\src\systemmonitor'

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            
            # Fix mistakes
            for pattern, replacement in fix_mappings:
                new_content = re.sub(pattern, replacement, new_content)
            
            # Apply final clean mappings
            for pattern, replacement in final_mappings:
                new_content = re.sub(pattern, replacement, new_content)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Verified/Fixed: {file_path}")
