"""Record a real command session on an isolated X11 display.

No user desktop or browser is captured. The script, transcript, timestamps,
source identities, video metadata and command status are retained together.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument('script', type=Path)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--label', default='香山 vdot 实际终端会话')
parser.add_argument('--timeout-seconds', type=int, default=600)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
script = args.script.resolve(strict=True)
output = args.output.resolve()
if not 1 <= args.timeout_seconds <= 7200:
    raise SystemExit('Invalid session timeout')
if output.exists():
    raise SystemExit('Refusing to overwrite an existing recording directory')
toolroot = root / 'tools/video/sysroot'
xvfb = toolroot / 'usr/bin/Xvfb'
xterm = toolroot / 'usr/bin/xterm'
for program in (xvfb, xterm):
    if not os.access(program, os.X_OK):
        raise SystemExit('Missing local recording tool: ' + str(program))
for name in ('ffmpeg', 'ffprobe', 'xdpyinfo', 'xsetroot', 'script'):
    if shutil.which(name) is None:
        raise SystemExit('Missing recording dependency: ' + name)
output.mkdir(parents=True)
(root / 'tmp').mkdir(exist_ok=True)
shutil.copyfile(script, output / 'commands.sh')
metadata = {'label': args.label, 'started_at_utc': datetime.now(timezone.utc).isoformat(),
            'capture_method': 'real xterm on isolated Xvfb, ffmpeg x11grab',
            'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
            'recording_complete': False, 'command_exit_status': None}
environment = os.environ.copy()
environment.update(SHELL='/bin/bash',
                   LD_LIBRARY_PATH=str(toolroot / 'usr/lib/x86_64-linux-gnu'),
                   XAPPLRESDIR=str(toolroot / 'etc/X11/app-defaults'))
display_number = next((n for n in range(177, 220) if not Path(f'/tmp/.X{n}-lock').exists()
                       and not Path(f'/tmp/.X11-unix/X{n}').exists()), None)
if display_number is None:
    raise SystemExit('No free recording display')
environment['DISPLAY'] = f':{display_number}'
server = terminal = encoder = None
source_command = [sys.executable, str(root / 'scripts/source_manifest.py')]
log_handles = []


def stop_requested(number, frame):
    raise SystemExit(128 + number)


signal.signal(signal.SIGTERM, stop_requested)
signal.signal(signal.SIGINT, stop_requested)


def open_log(name):
    handle = (output / name).open('w')
    log_handles.append(handle)
    return handle


try:
    subprocess.run([*source_command, str(output / 'source-before.json')], check=True)
    with tempfile.TemporaryDirectory(prefix='recording-', dir=root / 'tmp') as temporary:
        temporary = Path(temporary)
        ready, gate, status = (temporary / name for name in ('ready', 'start', 'status'))
        wrapper = temporary / 'session.sh'
        execution = shlex.join(['/bin/bash', str(script)])
        wrapper.write_text('\n'.join([
            '#!/bin/bash', 'set +e',
            'printf "\\n%s\\n\\n" ' + shlex.quote(args.label),
            'touch ' + shlex.quote(str(ready)),
            'while [[ ! -e ' + shlex.quote(str(gate)) + ' ]]; do sleep 0.1; done',
            shlex.join(['script', '--quiet', '--flush', '--return', '--command', execution,
                        '--log-out', str(output / 'terminal.log'),
                        '--log-timing', str(output / 'terminal.timing')]),
            'vdot_status=$?',
            'printf "%s\\n" "$vdot_status" > ' + shlex.quote(str(status)),
            'printf "\\nCommand exit status: %s\\n" "$vdot_status"',
            'sleep 2', 'exit "$vdot_status"', '']))
        server = subprocess.Popen([str(xvfb), environment['DISPLAY'], '-screen', '0',
                                   '1360x820x24', '-nolisten', 'tcp', '-ac'],
                                  env=environment, stdout=open_log('xvfb.log'), stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 10
        while subprocess.run(['xdpyinfo', '-display', environment['DISPLAY']],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            if server.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('Virtual display startup failed')
            time.sleep(.1)
        subprocess.run(['xsetroot', '-solid', '#101b2d'], env=environment, check=True)
        terminal = subprocess.Popen([str(xterm), '-ut', '-u8', '-geometry', '128x36+16+12',
                                     '-fa', 'DejaVu Sans Mono', '-fs', '13', '-bg', '#101b2d',
                                     '-fg', '#dbe5f1', '-b', '14', '-bw', '0',
                                     '-e', '/bin/bash', str(wrapper)],
                                    cwd=root, env=environment, stdout=open_log('xterm.log'), stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 10
        while not ready.exists():
            if terminal.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('Recording terminal startup failed')
            time.sleep(.1)
        encoder = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y',
                                    '-f', 'x11grab', '-video_size', '1360x820', '-framerate', '10',
                                    '-i', environment['DISPLAY'], '-an', '-c:v', 'libx264',
                                    '-preset', 'veryfast', '-crf', '20', '-threads', '2',
                                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                                    str(output / 'recording.mp4')],
                                   env=environment, stdin=subprocess.PIPE, text=True,
                                   stdout=open_log('ffmpeg.log'), stderr=subprocess.STDOUT)
        time.sleep(.7)
        if encoder.poll() is not None:
            raise RuntimeError('Video encoder startup failed')
        gate.touch()
        deadline = time.monotonic() + args.timeout_seconds
        while terminal.poll() is None:
            if encoder.poll() is not None:
                raise RuntimeError('Video encoder exited before the command session')
            if time.monotonic() > deadline:
                raise RuntimeError('Command recording exceeded its time budget')
            time.sleep(.25)
        if not status.exists():
            raise RuntimeError('Command session did not leave an exit status')
        metadata['command_exit_status'] = int(status.read_text().strip())
        encoder.communicate('q\n', timeout=20)
        if encoder.returncode:
            raise RuntimeError('Video encoder did not finish successfully')
    subprocess.run([*source_command, str(output / 'source-after.json')], check=True)
    before = json.loads((output / 'source-before.json').read_text())
    after = json.loads((output / 'source-after.json').read_text())
    if before['repositories'] != after['repositories'] or before['project_files_sha256'] != after['project_files_sha256']:
        raise RuntimeError('Source identity changed during recording')
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                       'stream=codec_name,width,height,r_frame_rate:format=duration,size',
                       '-of', 'json', str(output / 'recording.mp4')], text=True))
    if float(probe['format']['duration']) <= 0 or not probe.get('streams'):
        raise RuntimeError('Recorded video is empty')
    metadata['video'] = probe
    metadata['video_sha256'] = hashlib.sha256((output / 'recording.mp4').read_bytes()).hexdigest()
    metadata['recording_complete'] = True
finally:
    if encoder is not None and encoder.poll() is None:
        try:
            encoder.communicate('q\n', timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            encoder.kill(); encoder.wait()
    for process in (terminal, server):
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()
    metadata['ended_at_utc'] = datetime.now(timezone.utc).isoformat()
    (output / 'recording.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    for handle in log_handles:
        handle.close()
if metadata['command_exit_status']:
    raise SystemExit(metadata['command_exit_status'])
print('RECORDING_COMPLETE', output)
