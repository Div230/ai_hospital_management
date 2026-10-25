"""Generate development-only operator secrets; never prints secret values."""
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / '.env'
    if target.exists():
        print('.env already exists; no configuration changed.')
        return
    config = (ROOT / '.env.example').read_text()
    for key in ('SECRET_KEY', 'DB_PASSWORD', 'AIHMS_DEMO_PASSWORD'):
        config = config.replace(key + '=\n', key + '=' + secrets.token_urlsafe(48) + '\n')
    with target.open('x') as out:
        os.chmod(target, 0o600)
        out.write(config)
    print('Created private development .env. Demo account password is AIHMS_DEMO_PASSWORD in that file.')


if __name__ == '__main__':
    main()
