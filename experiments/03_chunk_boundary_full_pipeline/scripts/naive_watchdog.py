"""Run naive followup within the existing indexing session."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    from repro_runtime import get_runtime
    runtime=get_runtime(create=False)
    root=legacy_root('round4_full_20261030')
    round_dir=root/'round4_full_20261030'
    start=datetime.datetime.now(datetime.timezone.utc)
    if start<runtime.start or start>=runtime.watchdog_deadline:
        raise RuntimeError('Shared run window is not active; refusing to start a child')
    limit=min(600,(runtime.watchdog_deadline-start).total_seconds())
    with (round_dir/'logs/naive_followup.log').open('x') as log:
        p=subprocess.Popen([sys.executable,'-B','-u',str(round_dir/'scripts/run_naive_followup.py')],cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        status='completed'
        try:
            p.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            status='timeout'
            os.killpg(p.pid,signal.SIGTERM)
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL)
                p.wait()
        if p.returncode!=0 and status=='completed':
            status='failed'
        if status=='completed':
            summary_path=round_dir/'results/naive_followup_status.json'
            if not summary_path.is_file() or json.loads(summary_path.read_text()).get('status')!='completed':
                status='failed'
        result={'started_utc':start.isoformat(),'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'pid':p.pid,'exit_code':p.returncode,'child_alive':p.poll() is None,'timeout_seconds':limit}
        (round_dir/'results/naive_watchdog.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
