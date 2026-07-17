import json
from pathlib import Path
from datetime import datetime
import tempfile

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / 'runtime' / 'state' / 'pipeline_state.json'


def _atomic_write(path: Path, data: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    try:
        with open(fd, 'w', encoding='utf-8') as f:
            f.write(data)
        Path(tmp).replace(path)
    finally:
        try:
            if Path(tmp).exists():
                Path(tmp).unlink()
        except Exception:
            pass


def read_state():
    if not STATE_FILE.exists():
        return None
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def write_state(state: dict):
    state['updated_at'] = datetime.utcnow().isoformat()
    _atomic_write(STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2))


def start_run(run_id=None):
    state = {
        'run_id': run_id or datetime.now().strftime('%Y%m%d_%H%M%S'),
        'start_time': datetime.utcnow().isoformat(),
        'steps': {},
        'last_step': None,
        'status': 'running'
    }
    write_state(state)
    return state


def get_run_id():
    """Return the current run's id, or None if no run has started."""
    state = read_state() or {}
    return state.get('run_id')


def update_step(step_name, status, info=None):
    """Record a step's latest status.

    A step's status is always its most recent status (a later 'done' overrides
    an earlier 'failed', and vice-versa). The overall pipeline status is derived
    from the steps every time:

    - 'failed' when any step's latest status is 'failed'/'error'
    - 'running' otherwise (mark_complete sets 'complete' explicitly)

    This means a stage that fails an early attempt but succeeds on retry ends up
    'done', and the pipeline is not left in a 'failed' state after eventual
    success. Passing info=None preserves any previously stored info for the step
    (so recording a status never erases a recorded output).
    """
    state = read_state() or {}
    steps = state.get('steps', {})
    prev = steps.get(step_name, {})
    # Preserve prior info unless new info is explicitly supplied.
    merged_info = prev.get('info', {}) if info is None else info
    steps[step_name] = {
        'status': status,
        'info': merged_info or {},
        'ts': datetime.utcnow().isoformat(),
    }
    state['steps'] = steps
    state['last_step'] = step_name

    # Derive overall status from the latest per-step statuses.
    any_failed = any(
        s.get('status') in ('failed', 'error') for s in steps.values()
    )
    if any_failed:
        state['status'] = 'failed'
    elif state.get('status') != 'complete':
        state['status'] = 'running'

    write_state(state)
    return state


def record_step_output(step_name, path):
    """Record the identity of a file a step produced during the current run.

    Stores path + size + mtime + the current run_id under the step's info. A
    downstream stage can later call step_output_is_current() to confirm the file
    on disk was produced by *this* run (not a stale leftover from a prior run).
    """
    state = read_state() or {}
    steps = state.get('steps', {})
    p = Path(path)
    try:
        stat = p.stat()
        output_meta = {
            'path': str(p),
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'run_id': state.get('run_id'),
        }
    except OSError:
        output_meta = {
            'path': str(p),
            'size': None,
            'mtime': None,
            'run_id': state.get('run_id'),
        }

    entry = steps.get(step_name, {'status': 'running', 'info': {}, 'ts': datetime.utcnow().isoformat()})
    info = entry.get('info') or {}
    info['output'] = output_meta
    entry['info'] = info
    steps[step_name] = entry
    state['steps'] = steps
    write_state(state)
    return state


def step_output_is_current(step_name, path):
    """Return True only if `path` matches the output this run recorded for the step.

    Guards against consuming stale outputs: the recorded run_id must equal the
    current run_id, and the file on disk must still match the recorded size and
    mtime. Any mismatch (missing record, different run, changed/missing file)
    returns False.
    """
    state = read_state() or {}
    run_id = state.get('run_id')
    step = state.get('steps', {}).get(step_name, {})
    output = (step.get('info') or {}).get('output')
    if not output:
        return False
    if output.get('run_id') != run_id:
        return False
    p = Path(path)
    if str(p) != output.get('path'):
        return False
    try:
        stat = p.stat()
    except OSError:
        return False
    if stat.st_size <= 0:
        return False
    if output.get('size') is not None and stat.st_size != output.get('size'):
        return False
    if output.get('mtime') is not None and stat.st_mtime != output.get('mtime'):
        return False
    return True


def mark_complete():
    state = read_state() or {}
    state['status'] = 'complete'
    state['completed_at'] = datetime.utcnow().isoformat()
    write_state(state)
    return state
