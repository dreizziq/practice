"""Consistent SQLite snapshots; restoration always targets a new file."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from contextlib import closing


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def snapshot(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError('Source database does not exist.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the destination exclusively: never overwrite an existing database.
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src:
            with closing(sqlite3.connect(destination)) as dst:
                src.backup(dst)
                if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('SQLite integrity check failed.')
                if dst.execute('PRAGMA foreign_key_check').fetchall():
                    raise ValueError('Foreign key check failed.')
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination


def backup(source, destination):
    destination = Path(destination)
    manifest = Path(str(destination) + '.sha256.json')
    if manifest.exists():
        raise FileExistsError('Manifest already exists.')
    result = snapshot(source, destination)
    payload = {'format': 1, 'sha256': digest(result), 'database': result.name}
    with manifest.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2)
    return result


def restore(source, destination):
    source = Path(source)
    manifest = Path(str(source) + '.sha256.json')
    payload = json.loads(manifest.read_text(encoding='utf-8'))
    if payload.get('format') != 1 or payload.get('sha256') != digest(source):
        raise ValueError('Backup checksum does not match.')
    return snapshot(source, destination)
