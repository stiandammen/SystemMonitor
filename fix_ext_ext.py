import os
import re

mappings = [
    (r'systemmonitor\.typing_ext_ext', 'systemmonitor.typing_ext'),
    (r'systemmonitor\.enums_ext', 'systemmonitor.enums'), # Should not happen based on my patterns but good to be safe
    (r'systemmonitor\.paths_ext_ext', 'systemmonitor.paths_ext'),
    (r'systemmonitor\.datetime_ext_ext', 'systemmonitor.datetime_ext'),
]

root_dir = r'E:\[python - prosjekter]\SystemMonitor\src\systemmonitor'

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for pattern, replacement in mappings:
                new_content = re.sub(pattern, replacement, new_content)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed: {file_path}")
