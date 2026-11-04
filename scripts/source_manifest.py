"""Record local source identity without collecting contact or network data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).rstrip('\n')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


result = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'repositories': {}}
project_head = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
result['project_head'] = project_head.stdout.strip() if project_head.returncode == 0 else None
for name in ('XiangShan', 'NEMU'):
    repo = root / 'third_party' / name
    changed = {}
    for line in git(repo, 'status', '--porcelain', '--untracked-files=all').splitlines():
        relative = line[3:]
        path = repo / relative
        if path.is_file():
            changed[relative] = sha256(path.read_bytes())
    result['repositories'][name] = {
        'head': git(repo, 'rev-parse', 'HEAD'),
        'status': git(repo, 'status', '--porcelain', '--untracked-files=all'),
        'submodules': git(repo, 'submodule', 'status', '--recursive').splitlines(),
        'changed_source_sha256': changed,
    }
result['project_files_sha256'] = {}
for directory in ('scripts', 'tests', 'workloads', 'datapath', 'patches', 'configs'):
    for path in sorted((root / directory).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            result['project_files_sha256'][str(path.relative_to(root))] = sha256(path.read_bytes())
output = Path(sys.argv[1])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
print(output)
