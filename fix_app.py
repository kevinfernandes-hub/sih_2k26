import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# Replace duplicate currentInvestigation attributes
content = re.sub(r'currentInvestigation=\{currentInvestigation\}\s+currentInvestigation=\{currentInvestigation\}', r'currentInvestigation={currentInvestigation}', content)
# We can also just remove lines that are literally duplicate currentInvestigation
content = re.sub(r'(\s*currentInvestigation=\{currentInvestigation\}\s*\n)(.*?)(\s*currentInvestigation=\{currentInvestigation\})', r'\1\2', content)

with open('src/App_fixed.jsx', 'w') as f:
    f.write(content)
