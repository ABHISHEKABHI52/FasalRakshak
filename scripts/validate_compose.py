"""Validate docker-compose.yml structure without Docker (Phase 1 helper).

Checks: YAML parses; expected services exist; each service has build/image;
healthchecks present for db/backend; container-to-container URLs do not use
localhost and target the `db` service (docs/15 §1); declared secrets are
environment references, never hard-coded values.

`${VAR}` references are resolved from .env (if present) else .env.example,
which is what `docker compose` does.

Usage: python scripts/validate_compose.py [path/to/docker-compose.yml]
"""

import re
import sys
from pathlib import Path

import yaml

EXPECTED_SERVICES = {"db", "backend", "frontend"}
SECRET_KEYS = {"JWT_SECRET", "POSTGRES_PASSWORD", "DATABASE_URL"}
_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-[^}]*)?\}")


def load_env_map(root: Path) -> dict[str, str]:
    """Resolve ${VAR} placeholders the way docker compose does (.env, else .env.example)."""
    values: dict[str, str] = {}
    for candidate in (root / ".env", root / ".env.example"):
        if not candidate.exists():
            continue
        for raw in candidate.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values.setdefault(key.strip(), value.strip())
    return values


def resolve(value: str, env_map: dict[str, str]) -> str:
    def _sub(match: re.Match[str]) -> str:
        return env_map.get(match.group(1), match.group(0))

    return _VAR_PATTERN.sub(_sub, value)


def main() -> int:
    root = Path.cwd()
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "docker-compose.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    env_map = load_env_map(root)
    errors: list[str] = []

    services = data.get("services") or {}
    if set(services) != EXPECTED_SERVICES:
        errors.append(f"services mismatch: {sorted(services)} != {sorted(EXPECTED_SERVICES)}")

    for name in ("db", "backend"):
        service = services.get(name, {})
        if "healthcheck" not in service:
            errors.append(f"{name}: missing healthcheck")
        if not service.get("restart"):
            errors.append(f"{name}: missing restart policy")

    for name, service in services.items():
        if not (service.get("build") or service.get("image")):
            errors.append(f"{name}: needs build or image")

    backend_env = (services.get("backend") or {}).get("environment") or {}
    db_url = resolve(str(backend_env.get("DATABASE_URL", "")), env_map)
    if "localhost" in db_url or "127.0.0.1" in db_url:
        errors.append("backend DATABASE_URL resolves to localhost — must use the service name 'db'")
    if "@db:" not in db_url:
        errors.append(f"backend DATABASE_URL does not target the 'db' service (resolved: {db_url})")

    for name, service in services.items():
        for key, value in (service.get("environment") or {}).items():
            if key in SECRET_KEYS and value and not _VAR_PATTERN.fullmatch(str(value)):
                errors.append(f"{name}: {key} looks hard-coded — must come from environment variables")

    if not (data.get("volumes") or {}):
        errors.append("no named volumes declared (pgdata expected)")

    if errors:
        print("compose validation FAILED:")
        for err in errors:
            print(" -", err)
        return 1

    print("compose validation PASSED")
    print(" services:", ", ".join(sorted(services)))
    print(" volumes:", ", ".join(sorted((data.get("volumes") or {}).keys())))
    print(" db url target:", db_url.split("@")[-1] if "@" in db_url else db_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())