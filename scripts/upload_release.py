#!/usr/bin/env python3
"""Upload release assets to GitHub v1.0.0."""
import subprocess, urllib.request, json, os, sys

def get_token():
    p = subprocess.Popen(
        ['git', 'credential', 'fill'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    out, _ = p.communicate(input='protocol=https\nhost=github.com\n\n')
    for line in out.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1]
    return ''

token = get_token()
if not token:
    print('ERROR: Could not retrieve GitHub token from credential manager.')
    sys.exit(1)

API_BASE = 'https://api.github.com/repos/MohsinSyed130605/Klipwerk/releases/413159423'
UPLOAD_BASE = 'https://uploads.github.com/repos/MohsinSyed130605/Klipwerk/releases/413159423/assets'
AUTH = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Klipwerk'}

# Check and remove existing assets with the same name
try:
    req = urllib.request.Request(API_BASE + '/assets', headers={**AUTH, 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        existing = json.loads(resp.read().decode())
        target_names = {'Klipwerk-Setup-x64.exe', 'Klipwerk-Portable-x64.exe', 'Klipwerk-Source-v1.0.0.zip'}
        for asset in existing:
            if asset.get('name') in target_names:
                aid = asset.get('id')
                print(f"Deleting older release asset: {asset.get('name')} (ID: {aid})...")
                del_url = f"https://api.github.com/repos/MohsinSyed130605/Klipwerk/releases/assets/{aid}"
                del_req = urllib.request.Request(del_url, headers={**AUTH, 'Accept': 'application/vnd.github+json'}, method='DELETE')
                urllib.request.urlopen(del_req, timeout=30).close()
except Exception as e:
    print('Warning checking existing assets:', e)

files = [
    ('Klipwerk-Setup-x64.exe',       'application/vnd.microsoft.portable-executable'),
    ('Klipwerk-Portable-x64.exe',    'application/vnd.microsoft.portable-executable'),
    ('Klipwerk-Source-v1.0.0.zip',   'application/zip'),
]

for fname, ctype in files:
    size = os.path.getsize(fname)
    print(f'Uploading {fname} ({size // 1048576} MB)...')
    sys.stdout.flush()
    url = UPLOAD_BASE + '?name=' + fname
    headers = {**AUTH, 'Content-Type': ctype, 'Accept': 'application/vnd.github+json'}
    with open(fname, 'rb') as f:
        data = f.read()
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read().decode())
            dl_url = result.get('browser_download_url', 'no url')
            print('  OK:', dl_url)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print('  HTTP ERROR', e.code, body[:300])
    except Exception as e:
        print('  ERROR:', e)

print('\nAll done. Visit: https://github.com/MohsinSyed130605/Klipwerk/releases/tag/v1.0.0')
