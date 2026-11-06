"""Show a real derived waveform on the recording's isolated display."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import time

p=argparse.ArgumentParser()
p.add_argument('image',type=Path)
p.add_argument('--seconds',type=float,default=12)
p.add_argument('--title',default='本轮真实FST的派生时序图')
a=p.parse_args();source=a.image.resolve(strict=True)
m=re.fullmatch(r':(\d+)',os.environ.get('DISPLAY',''))
if not m or not 177<=int(m[1])<=219:raise SystemExit('Only an isolated recording display is allowed')
if not 1<=a.seconds<=40:raise SystemExit('Invalid viewing duration')
print('时序图来源：',source,flush=True)
print('源图SHA256：',hashlib.sha256(source.read_bytes()).hexdigest(),flush=True)
temporary=Path(__file__).resolve().parents[1]/'tmp/recording-images'
temporary.mkdir(parents=True,exist_ok=True)
target=temporary/(source.stem+'-'+hashlib.sha256(source.read_bytes()).hexdigest()[:12]+'.png')
subprocess.run(['/usr/bin/convert','-density','160','-background','white',str(source),'-resize','1320x760>',str(target)],check=True)
viewer=subprocess.Popen(['/usr/bin/display','-title',a.title,'-geometry','1320x760+20+20',str(target)])
try:
 time.sleep(.7)
 if viewer.poll() is not None:raise RuntimeError('Waveform viewer did not remain open')
 time.sleep(a.seconds)
finally:
 if viewer.poll() is None:
  viewer.terminate()
  try:viewer.wait(timeout=5)
  except subprocess.TimeoutExpired:viewer.kill();viewer.wait()
