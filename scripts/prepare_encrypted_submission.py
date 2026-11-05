"""Prepare the official PGP submission locally after all packages verify.

No Git push, PR, email or portal upload is performed by this command.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--packages', type=Path, required=True)
parser.add_argument('--official-key', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
manifest = json.loads((args.packages / 'packages-manifest.json').read_text())
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
if manifest['status'] != 'packaged_not_uploaded' or manifest['final_project_head'] != head:
    raise SystemExit('Final submission packages are missing or stale')
for item in manifest['packages']:
    digest = hashlib.sha256()
    with Path(item['file']).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    if digest.hexdigest() != item['sha256']:
        raise SystemExit('Submission ZIP changed: ' + Path(item['file']).name)
expected_key_sha = '3c9915b188124969bb862de674a2ca030c2c7de2e8ebc54f724867dfa680feb5'
fingerprint = '936E3DCCFEB2C1C1472BD43E11489B37147B12E1'
key = args.official_key.resolve(strict=True)
if hashlib.sha256(key.read_bytes()).hexdigest() != expected_key_sha:
    raise SystemExit('Official key differs from the verified 2026-11-05 primary source')
private = root / 'private'
private.mkdir(mode=0o700, exist_ok=True)
os.chmod(private, 0o700)
contact = json.loads((private / 'submission-contact.json').read_text())
email = contact['contact_email']
if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
    raise SystemExit('Invalid contact address; do not print or publish it')
description = '复用香山昆明湖V2向量流水线扩展八路有符号点积指令，实现RTL与NEMU协同验证，提供等价向量基线、实测性能与完整复现材料。'
if len(description) > 100:
    raise SystemExit('Project description is too long')
content = ('team-name: 全栈漏洞队\n'
           'repo-url: https://github.com/Andrew111888/cie2026quanzhanloudongduixiangshanvdot.git\n'
           'github-username: Andrew111888\n'
           f'contact-email: {email}\n'
           f'project-description: {description}\n'
           f'notes: source-sha={head}; 低8项/低32位及最小向量支持域为暂定契约，官方Issue #126问题与答复状态见作品docs/QUESTIONS.md。\n')
folder = private / ('submission-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
folder.mkdir(mode=0o700, exist_ok=False)
plaintext = folder / 'my_submission.txt'
fd = os.open(plaintext, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
with os.fdopen(fd, 'w') as stream: stream.write(content)
home = private / 'gnupg'
home.mkdir(mode=0o700, exist_ok=True)
os.chmod(home, 0o700)
base = ['gpg', '--homedir', str(home), '--batch']
listed = subprocess.check_output([*base, '--with-colons', '--show-keys', str(key)],
                                  text=True, stderr=subprocess.DEVNULL)
fingerprints = [line.split(':')[9] for line in listed.splitlines() if line.startswith('fpr:')]
if not fingerprints or fingerprints[0] != fingerprint:
    raise SystemExit('Official recipient fingerprint mismatch')
subprocess.run([*base, '--import', str(key)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ciphertext = folder / 'submission.asc'
result = subprocess.run([*base, '--yes', '--trust-model', 'always', '--status-fd', '1',
                         '--encrypt', '--recipient', fingerprint, '--armor',
                         '--output', str(ciphertext), str(plaintext)],
                        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
os.chmod(ciphertext, 0o600)
if '[GNUPG:] END_ENCRYPTION' not in result.stdout or not ciphertext.read_text().startswith('-----BEGIN PGP MESSAGE-----'):
    raise SystemExit('No completed armored encryption evidence')
metadata = {'status': 'encrypted_locally_not_submitted', 'final_project_head': head,
            'official_key_sha256': expected_key_sha, 'recipient_fingerprint': fingerprint,
            'description_characters': len(description), 'ciphertext_sha256': hashlib.sha256(ciphertext.read_bytes()).hexdigest(),
            'notes': 'Manual equivalent of the official submit.sh encryption; plaintext remains private with mode 0600. Only submission.asc is intended for the fork.'}
(folder / 'encryption.json').write_text(json.dumps(metadata, indent=2)+'\n')
os.chmod(folder / 'encryption.json', 0o600)
print('ENCRYPTED_SUBMISSION_PREPARED_LOCALLY', folder)
