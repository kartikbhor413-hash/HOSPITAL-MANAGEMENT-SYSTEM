"""
helpers/json_db.py
Thread-safe and process-safe atomic JSON file storage engine for Smart Hospital Management System.
Features:
- FileLock + Thread RLock concurrency control
- Atomic file write via tempfile + os.replace to prevent corruption
- Auto-incrementing primary key generator (e.g. PAT001, DOC001, BILL001)
- Activity logging integration
"""

import os
import json
import re
import tempfile
import threading
from datetime import datetime
from filelock import FileLock

# Base paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOCKS_DIR = os.path.join(DATA_DIR, ".locks")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOCKS_DIR, exist_ok=True)

# In-memory thread lock
_thread_lock = threading.RLock()


# Cache lock instances per collection so FileLock re-entrancy works properly
_file_locks = {}

def _get_file_path(collection: str) -> str:
    """Returns absolute path to a JSON collection file."""
    if not collection.endswith(".json"):
        collection = f"{collection}.json"
    return os.path.join(DATA_DIR, collection)


def _get_lock(collection: str) -> FileLock:
    """Returns cached FileLock instance for given collection."""
    clean_name = os.path.splitext(os.path.basename(collection))[0]
    if clean_name not in _file_locks:
        lock_path = os.path.join(LOCKS_DIR, f"{clean_name}.lock")
        _file_locks[clean_name] = FileLock(lock_path, timeout=5)
    return _file_locks[clean_name]


def _read_unlocked(collection: str) -> list:
    """Reads data directly without acquiring lock (assumes caller already holds lock)."""
    file_path = _get_file_path(collection)
    if not os.path.exists(file_path):
        _write_unlocked(collection, [])
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[JSON_DB WARN] Failed to decode {file_path}: {e}. Returning empty list.")
        return []


def _write_unlocked(collection: str, data: list) -> bool:
    """Writes data atomically without acquiring lock (assumes caller already holds lock)."""
    file_path = _get_file_path(collection)
    temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, prefix="tmp_shms_", suffix=".json")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, file_path)
        return True
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise IOError(f"Atomic write failed for {file_path}: {str(e)}")


def read_data(collection: str) -> list:
    """
    Safely reads JSON collection with file & thread locks.
    Returns list of dicts. If file doesn't exist, initializes it as empty list [].
    """
    with _thread_lock:
        with _get_lock(collection):
            return _read_unlocked(collection)


def write_data(collection: str, data: list) -> bool:
    """
    Safely writes data to JSON file using atomic replacement (temp file -> os.replace)
    to prevent file corruption during power cuts or simultaneous writes.
    """
    with _thread_lock:
        with _get_lock(collection):
            return _write_unlocked(collection, data)


def generate_next_id(collection: str, prefix: str, id_field: str = "id", digits: int = 3) -> str:
    """
    Scans collection to find the maximum existing numerical index for the prefix,
    and returns the next formatted ID (e.g. PAT001 -> PAT002).
    """
    items = read_data(collection)
    max_num = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)

    for item in items:
        if isinstance(item, dict) and id_field in item:
            val = str(item[id_field]).strip()
            match = pattern.match(val)
            if match:
                try:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass

    next_num = max_num + 1
    return f"{prefix}{str(next_num).zfill(digits)}"


def find_by_id(collection: str, id_value: str, id_field: str = "id"):
    """Returns item dictionary if found, else None."""
    items = read_data(collection)
    for item in items:
        if isinstance(item, dict) and str(item.get(id_field)) == str(id_value):
            return item
    return None


def filter_data(collection: str, predicate) -> list:
    """Returns items matching the predicate function."""
    items = read_data(collection)
    return [item for item in items if predicate(item)]


def insert_record(collection: str, record: dict, prefix: str = None, id_field: str = "id") -> dict:
    """
    Safely inserts a record. If prefix is supplied and id_field not set, generates new ID.
    Returns inserted record.
    """
    with _thread_lock:
        with _get_lock(collection):
            items = _read_unlocked(collection)
            if prefix and (id_field not in record or not record[id_field]):
                max_num = 0
                pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
                for item in items:
                    val = str(item.get(id_field, "")).strip()
                    m = pattern.match(val)
                    if m:
                        try:
                            n = int(m.group(1))
                            if n > max_num:
                                max_num = n
                        except ValueError:
                            pass
                record[id_field] = f"{prefix}{str(max_num + 1).zfill(3)}"

            items.append(record)
            _write_unlocked(collection, items)
            return record


def update_record(collection: str, id_value: str, updates: dict, id_field: str = "id") -> dict:
    """
    Updates record matching id_value with given updates dict.
    Returns updated record or None if not found.
    """
    with _thread_lock:
        with _get_lock(collection):
            items = _read_unlocked(collection)
            target = None
            for item in items:
                if isinstance(item, dict) and str(item.get(id_field)) == str(id_value):
                    item.update(updates)
                    target = item
                    break
            if target:
                _write_unlocked(collection, items)
            return target


def delete_record(collection: str, id_value: str, id_field: str = "id") -> bool:
    """
    Deletes record matching id_value.
    Returns True if deleted, False if not found.
    """
    with _thread_lock:
        with _get_lock(collection):
            items = _read_unlocked(collection)
            initial_count = len(items)
            new_items = [i for i in items if str(i.get(id_field)) != str(id_value)]
            if len(new_items) != initial_count:
                _write_unlocked(collection, new_items)
                return True
            return False


def log_activity(user_id: str, role: str, action: str, module: str) -> dict:
    """
    Records an activity audit entry into data/activity_logs.json.
    """
    now = datetime.now()
    log_entry = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%I:%M:%S %p"),
        "user_id": user_id or "SYSTEM",
        "role": role or "System",
        "action": action,
        "module": module
    }
    return insert_record("activity_logs", log_entry, prefix="LOG", id_field="log_id")
