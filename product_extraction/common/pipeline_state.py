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


def update_step(step_name, status, info=None):
    state = read_state() or {}
    steps = state.get('steps', {})
    steps[step_name] = {'status': status, 'info': info or {}, 'ts': datetime.utcnow().isoformat()}
    state['steps'] = steps
    state['last_step'] = step_name
    if status in ('failed', 'error'):
        state['status'] = 'failed'
    write_state(state)
    return state


def mark_complete():
    state = read_state() or {}
    state['status'] = 'complete'
    state['completed_at'] = datetime.utcnow().isoformat()
    write_state(state)
    return state
