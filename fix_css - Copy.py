
with open('style.css', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('style.css', 'w', encoding='utf-8') as f:
    f.writelines(lines[:1066] + lines[1122:])
print('style.css fixed successfully!')

