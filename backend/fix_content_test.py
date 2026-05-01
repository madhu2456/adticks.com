from datetime import datetime

p = "tests/unit/test_content_freshness.py"
with open(p, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the test function
start_def = None
for i, l in enumerate(lines):
    if "def test_detect_recent_updates" in l:
        start_def = i
        break

if start_def is None:
    print('test function not found')
    raise SystemExit(1)

# Find mock_response start and client assignment end
start = None
for j in range(start_def, min(start_def + 200, len(lines))):
    if "mock_response = MagicMock()" in lines[j]:
        start = j
        break

if start is None:
    print('mock_response not found')
    raise SystemExit(1)

end = None
for k in range(start, min(start + 200, len(lines))):
    if "client = AsyncMock()" in lines[k]:
        end = k
        break

if end is None:
    print('client assignment not found')
    raise SystemExit(1)

# Determine indentation
indent = lines[start][:len(lines[start]) - len(lines[start].lstrip())]

new_block = [
    indent + "mock_response = MagicMock()\n",
    indent + "last_mod = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')\n",
    indent + "mock_response.headers = {\n",
    indent + "    \"last-modified\": last_mod,\n",
    indent + "    \"cache-control\": \"max-age=3600\",\n",
    indent + "    \"etag\": '\\"123abc\\"',\n",
    indent + "}\n",
    indent + "\n",
    indent + "client = AsyncMock()\n",
    indent + "client.head = AsyncMock(return_value=mock_response)\n",
]

new_lines = lines[:start] + new_block + lines[end+1:]
with open(p, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✅ test file updated')
