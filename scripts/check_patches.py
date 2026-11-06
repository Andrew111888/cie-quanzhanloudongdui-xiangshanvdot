"""Replay each patch against pristine Git blobs and compare the resulting files."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
(root / 'build').mkdir(exist_ok=True)
records = {}
manifest = json.loads((root / 'configs/source-manifest.json').read_text())
for name, directory in [('xiangshan', 'XiangShan'), ('nemu', 'NEMU')]:
    upstream = root / 'third_party' / directory
    patch = root / 'patches' / f'{name}.patch'
    paths = [line[6:] for line in patch.read_text().splitlines() if line.startswith('+++ b/')]
    if not paths or len(paths) != len(set(paths)):
        raise SystemExit(f'invalid patch file list: {patch}')
    records[name] = {
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=upstream, text=True).strip(),
        'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(), 'files': {},
    }
    with tempfile.TemporaryDirectory(prefix=f'patch-{name}-', dir=root / 'build') as temporary:
        clean = Path(temporary)
        subprocess.run(['git', 'init', '-q'], cwd=clean, check=True)
        for relative in paths:
            path = PurePosixPath(relative)
            if path.is_absolute() or '..' in path.parts:
                raise SystemExit(f'unsafe patch path: {relative}')
            base = subprocess.run(['git', 'show', f'HEAD:{relative}'], cwd=upstream,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if base.returncode == 0:
                target = clean / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(base.stdout)
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=clean, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=clean, check=True)
        for relative in paths:
            actual = (clean / relative).read_bytes()
            expected = manifest['patched_sources'][directory][relative]
            if hashlib.sha256(actual).hexdigest() != expected:
                raise SystemExit(f'patch replay differs from verified source: {name}/{relative}')
            if actual != (upstream / relative).read_bytes():
                raise SystemExit(f'patch replay differs from current source: {name}/{relative}')
            records[name]['files'][relative] = hashlib.sha256(actual).hexdigest()
    print(f'PASS {name}: pristine patch replay matches {len(paths)} current source files')
output = root / 'reports' / 'patch-replay.json'
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(records, indent=2) + '\n')
