import os
import re

mappings = [
    (r'systemmonitor\.typing', 'systemmonitor.typing_ext'),
    (r'systemmonitor\.enum', 'systemmonitor.enums'),
    (r'systemmonitor\.pathlib', 'systemmonitor.paths_ext'),
    (r'systemmonitor\.datetime', 'systemmonitor.datetime_ext'),
    (r'from \.typing', 'from .typing_ext'),
    (r'from \.enum', 'from .enums'),
    (r'from \.pathlib', 'from .paths_ext'),
    (r'from \.datetime', 'from .datetime_ext'),
    (r'from \.\.typing', 'from ..typing_ext'),
    (r'from \.\.enum', 'from ..enums'),
    (r'from \.\.pathlib', 'from ..paths_ext'),
    (r'from \.\.datetime', 'from ..datetime_ext'),
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
                # Use regex with word boundaries where appropriate to avoid partial matches
                # But for systemmonitor.xxx it's already quite specific.
                # Let's use negative lookbehind/lookahead if needed.
                # The user said NOT to change 'import typing' or 'from datetime import'.
                # My mappings for 'systemmonitor.xxx' and 'from .xxx' are safe.
                new_content = re.sub(pattern, replacement, new_content)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated: {file_path}")
