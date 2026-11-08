import os
import pwd
import sys
from pathlib import Path

from sqlalchemy.engine.url import make_url

_DEFAULT_DATABASE_URL = 'sqlite:///data/maciota.db'
_DEFAULT_CHECKPOINT_PATH = 'data/checkpoints.db'
_RUNTIME_USER = 'maciota'


def sqlite_parent_directories(
    database_url: str = _DEFAULT_DATABASE_URL,
    checkpoint_path: str = _DEFAULT_CHECKPOINT_PATH,
) -> list[Path]:
    parents: list[Path] = []
    url = make_url(database_url)
    if url.drivername.startswith('sqlite') and url.database not in {None, ':memory:'}:
        parents.append(Path(url.database).parent)
    parents.append(Path(checkpoint_path).parent)
    return parents


def _grant(path: Path, uid: int, gid: int) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chown(path, uid, gid)
    for child in path.rglob('*'):
        os.chown(child, uid, gid)


def grant_sqlite_directories(database_url: str, checkpoint_path: str) -> None:
    account = pwd.getpwnam(_RUNTIME_USER)
    seen: set[Path] = set()
    for parent in sqlite_parent_directories(database_url, checkpoint_path):
        if parent in seen:
            continue
        seen.add(parent)
        _grant(parent, account.pw_uid, account.pw_gid)


def main() -> None:
    grant_sqlite_directories(
        os.environ.get('DATABASE_URL', _DEFAULT_DATABASE_URL),
        os.environ.get('CHECKPOINT_PATH', _DEFAULT_CHECKPOINT_PATH),
    )
    account = pwd.getpwnam(_RUNTIME_USER)
    os.initgroups(account.pw_name, account.pw_gid)
    os.setgid(account.pw_gid)
    os.setuid(account.pw_uid)
    command = sys.argv[1:] or ['maciota-bot']
    os.execvp(command[0], command)


if __name__ == '__main__':
    main()
