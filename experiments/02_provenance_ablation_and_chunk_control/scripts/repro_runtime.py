"""Persistent run session. Importing this module never creates or resets a run."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root, ENV_FILE  # path mapping only, see paths.py
import argparse
from dataclasses import dataclass
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import tempfile

ROOT = legacy_root('round3')
GROUP = 'B'
ROUND = ROOT / 'round3'
QUERY_MINUTES = 60
SESSION_PATH = ROOT / 'config/repro_session.json'
DEFAULT_CONFIG = ENV_FILE
OUTPUT_DIRS = ['results', 'logs', 'report']


@dataclass(frozen=True)
class Runtime:
    start: dt.datetime
    query_deadline: dt.datetime
    deadline: dt.datetime
    watchdog_deadline: dt.datetime
    config_path: Path


def utc_time(value):
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError('开始时间必须是带时区的 ISO-8601 时间。')
    try:
        result = dt.datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    except ValueError:
        raise RuntimeError('开始时间格式无效；已有会话不会被重建。') from None
    if result.tzinfo is None or result.utcoffset() is None:
        raise RuntimeError('开始时间必须包含时区。')
    return result.astimezone(dt.timezone.utc)


def _validate(data, require_active=True):
    required = {'schema_version', 'group', 'root', 'start_utc', 'config_path'}
    if not isinstance(data, dict) or not required.issubset(data) or type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise RuntimeError('会话文件格式无效；请保留文件并检查，不会自动重建。')
    if data['group'] != GROUP or data['root'] != str(ROOT):
        raise RuntimeError('会话属于其他运行副本；不能复制旧会话继续运行。')
    start = utc_time(data['start_utc'])
    if not isinstance(data['config_path'], str) or not data['config_path'].strip() or not Path(data['config_path']).expanduser().is_absolute():
        raise RuntimeError('会话中的配置路径无效；已有会话不会被重建。')
    config = Path(data['config_path']).expanduser().resolve()
    explicit_start = os.environ.get('LIGHTRAG_REPRO_START_UTC', '').strip()
    if explicit_start and utc_time(explicit_start) != start:
        raise RuntimeError('环境变量开始时间与已保存会话冲突。取消 LIGHTRAG_REPRO_START_UTC 后可读取原会话；不能延长窗口。')
    explicit_config = os.environ.get('LIGHTRAG_REPRO_CONFIG', '').strip()
    if explicit_config and Path(explicit_config).expanduser().resolve() != config:
        raise RuntimeError('配置路径与已保存会话不一致；不会更换当前运行的配置。')
    runtime = Runtime(start, start + dt.timedelta(minutes=QUERY_MINUTES),
                      start + dt.timedelta(minutes=120), start + dt.timedelta(minutes=105), config)
    now = dt.datetime.now(dt.timezone.utc)
    if require_active and now < runtime.start:
        raise RuntimeError('会话开始时间在未来，拒绝运行。')
    if require_active and now >= runtime.deadline:
        raise RuntimeError('本轮120分钟窗口已结束；保留会话和结果，另建新运行副本。不会自动重置时间。')
    if require_active and not config.is_file():
        raise RuntimeError('找不到会话指定的配置文件，请检查外置硬盘；无需复制密钥。')
    return runtime


def _read(require_active=True):
    try:
        data = json.loads(SESSION_PATH.read_text())
    except (OSError, ValueError):
        raise RuntimeError('无法读取已有会话文件；保留文件并检查，不会自动重建。') from None
    return _validate(data, require_active)


def _check_empty_outputs():
    for directory in OUTPUT_DIRS:
        path = ROUND / directory
        if path.is_file() or any(p.is_file() or p.is_symlink() for p in path.rglob('*')):
            raise RuntimeError('已有活动输出但没有会话，拒绝重新计时。请保留结果并检查：' + str(path))
    if (ROUND / 'evidence/public_runtime_config.json').exists():
        raise RuntimeError('已有运行配置证据但没有会话，拒绝重新计时。')


def get_runtime(create=False, require_active=True):
    """Create only for an explicit run entrypoint; otherwise read the fixed session."""
    if SESSION_PATH.exists():
        runtime = _read(require_active)
    elif not create:
        raise RuntimeError('本副本尚未开始运行。请按 START_HERE.txt 执行首个运行命令；无需手动设置开始时间。')
    else:
        SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
        lock_fd = os.open(SESSION_PATH.with_suffix('.lock'), os.O_CREAT | os.O_RDWR, 0o600)
        with os.fdopen(lock_fd, 'a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if SESSION_PATH.exists():
                runtime = _read(require_active)
            else:
                _check_empty_outputs()
                config = Path(os.environ.get('LIGHTRAG_REPRO_CONFIG') or DEFAULT_CONFIG).expanduser().resolve()
                raw_start = os.environ.get('LIGHTRAG_REPRO_START_UTC', '').strip()
                start = utc_time(raw_start) if raw_start else dt.datetime.now(dt.timezone.utc)
                data = {'schema_version': 1, 'group': GROUP, 'root': str(ROOT),
                        'start_utc': start.isoformat(), 'config_path': str(config)}
                runtime = _validate(data, require_active=True)
                fd, temp_name = tempfile.mkstemp(prefix='.repro-session-', dir=SESSION_PATH.parent)
                try:
                    with os.fdopen(fd, 'w') as output:
                        json.dump(data, output, ensure_ascii=False, indent=2)
                        output.write('\n');output.flush();os.fsync(output.fileno())
                    try:
                        os.link(temp_name, SESSION_PATH)  # Never overwrite another session.
                    except FileExistsError:
                        runtime = _read(require_active)
                finally:
                    Path(temp_name).unlink(missing_ok=True)
    os.environ.setdefault('LIGHTRAG_REPRO_START_UTC', runtime.start.isoformat())
    os.environ.setdefault('LIGHTRAG_REPRO_CONFIG', str(runtime.config_path))
    return runtime


def main():
    parser = argparse.ArgumentParser(description='只查看本组会话状态；不创建会话、不调用 API。')
    parser.add_argument('action', nargs='?', choices=['status'], default='status')
    parser.parse_args()
    if not SESSION_PATH.exists():
        print(json.dumps({'state': 'not_started', 'group': GROUP, 'session_file': str(SESSION_PATH),
                          'instruction': '直接执行 START_HERE.txt 中的首个运行命令。该命令会调用真实 API；首次运行会固定开始时间。'}, ensure_ascii=False, indent=2))
        return
    runtime = get_runtime(require_active=False)
    now = dt.datetime.now(dt.timezone.utc)
    state = 'expired' if now >= runtime.deadline else 'future' if now < runtime.start else 'active'
    print(json.dumps({'state': state, 'group': GROUP, 'start_utc': runtime.start.isoformat(),
                      'query_deadline_utc': runtime.query_deadline.isoformat(),
                      'deadline_utc': runtime.deadline.isoformat(), 'config_file_exists': runtime.config_path.is_file(),
                      'session_file': str(SESSION_PATH)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
