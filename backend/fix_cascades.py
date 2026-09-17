import re

with open('app/models.py', 'r') as f:
    content = f.read()

# Replace all 'delete-orph' with 'all'
content = content.replace('cascade="all, delete-orph"', 'cascade="all"')
content = content.replace("cascade='all, delete-orph'", 'cascade="all"')
content = content.replace('cascade="delete, delete-orph"', 'cascade="all"')
content = content.replace("cascade='delete, delete-orph'", 'cascade="all"')

with open('app/models.py', 'w') as f:
    f.write(content)

print('Fixed')