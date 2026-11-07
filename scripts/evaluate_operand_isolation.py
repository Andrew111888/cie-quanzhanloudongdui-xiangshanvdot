#!/usr/bin/env python3
"""Run a local elastic-wrapper comparison; counters are activity, never power."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
FILES = ["rtl/VdotAccRetimedDatapath.sv", "experiments/isolation/IsolationCompare.sv",
         "experiments/isolation/isolation_test.cpp", "scripts/evaluate_operand_isolation.py"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verilator", default=shutil.which("verilator") or "/home/yh/chipyard/.conda-env/bin/verilator")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = (args.output or ROOT / "reports" / f"operand-isolation-{stamp}").resolve()
    out.mkdir(parents=True, exist_ok=False)
    sources = out / "sources"
    hashes = {}
    for relative in FILES:
        dst = sources / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, dst)
        hashes[relative] = hashlib.sha256(dst.read_bytes()).hexdigest()
    commands = []
    def run(command, logfile):
        start = time.monotonic()
        with (out / logfile).open("w") as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        commands.append({"argv": command, "exit_code": result.returncode,
                         "seconds": round(time.monotonic()-start, 3), "log": logfile})
        (out / "commands.json").write_text(json.dumps(commands, indent=2)+"\n")
        if result.returncode:
            raise RuntimeError(f"Command failed ({result.returncode}); see {out / logfile}")
    version = subprocess.check_output([args.verilator, "--version"], text=True).strip()
    obj = out / "obj_dir"
    run([args.verilator, "--cc", "--exe", "--build", "--top-module", "IsolationCompare",
         "-DSYNTHESIS", "-Wno-fatal", "--Mdir", str(obj), "-j", str(args.jobs),
         "-CFLAGS", "-std=c++17 -O2", "-MAKEFLAGS", "CXX=/usr/bin/g++ LINK=/usr/bin/g++",
         str(sources / FILES[0]), str(sources / FILES[1]), str(sources / FILES[2])], "build.log")
    run([str(obj / "VIsolationCompare")], "simulation.log")
    modes = []
    names = ["continuous_dot", "dot_with_bubbles_stalls_flush", "mixed_quarter_dot", "bursty_dot"]
    for line in (out / "simulation.log").read_text().splitlines():
        if not line.startswith("ISOLATION_PASS "):
            continue
        row = {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", line)}
        row["name"] = names[row["mode"]]
        row["conservation_pass"] = row["accepted"] == row["checked"] + row["killed"]
        row["seed"] = 20261107 + row["mode"]
        row["stable_sample_activity"] = {
            field: {"baseline_bit_flips": row[f"baseline_{field}"],
                    "isolated_bit_flips": row[f"isolated_{field}"],
                    "change_percent": round(100*(row[f"isolated_{field}"]/row[f"baseline_{field}"]-1), 6)}
            for field in ["products", "stage1", "result"]}
        modes.append(row)
    if len(modes) != 4 or any(not row["conservation_pass"] for row in modes):
        raise RuntimeError("Missing mode or conservation failure")
    result = {
        "status": "PASS", "scope": "experimental_elastic_wrapper_simulation",
        "source_sha256": hashes, "verilator": version, "modes": modes,
        "sampling": {"cycles_per_mode": 12008, "traffic_cycles": 12000,
            "samples_per_cycle": 2,
            "points": "after input settle before rising edge, and after rising-edge settle",
            "counters": "XOR popcount across successive stable samples of 128 product bits, 192 stage-1 register bits, and 32 result-register bits",
            "initial_previous_value": "zero; Verilator initializes unreset registers to zero",
            "glitches_counted": False, "clock_tree_counted": False,
            "mux_inputs_or_full_core_counted": False},
        "verification": {"golden": "independent signed-int8 low-eight dot plus optional uint32 accumulator; high 96 bits zero",
            "regular_operation": "test-only independent 16-lane low-int8 multiply; not actual VIMac64b",
            "checks": ["all valid results and tags equal golden, including stalled outputs",
                       "producer holds request while blocked", "flush removes all queued transactions",
                       "accepted equals checked plus flushed", "drain has no outstanding transactions",
                       "all four independent stage-enable patterns observed",
                       "disabled stage registers hold across rising edges"],
            "stage_enables": "stage1=accept&&in_dot; stage2=move&&dot1; enables may differ",
            "full_core_integrated": False, "formal_equivalence": False},
        "continuous_dot": {"accepted_per_traffic_cycle": modes[0]["accepted"]/12000,
                           "added_wrapper_pipeline_cycles": 0,
                           "frequency_or_timing_measured": False,
                           "warning": "Timing cost of operand mux and extra enable logic is unmeasured"},
        "power_measured": False, "area_measured": False,
        "limitations": ["Stable-sample flips are activity indicators, not power or glitch activity",
                        "Input isolation gates bubbles to zero, so dot-bubble boundaries can add product transitions",
                        "Wrapper uses explicit flush and two-entry elastic tags; real XiangShan redirect and ROB handling are not modified or validated here",
                        "Baseline and isolated share a modeled standard multiply path; standard vector FU integration still requires regression"],
        "reproduce": "python3 scripts/evaluate_operand_isolation.py --verilator " + args.verilator}
    (out / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(out)
    for mode in modes:
        print(mode["name"], json.dumps(mode["stable_sample_activity"]))

if __name__ == "__main__":
    main()
