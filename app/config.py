import os


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Environment variable {name} is required. Set it in your .env file."
        )
    return value


PARTY_PASSWORD = _require_env("PARTY_PASSWORD")
SECRET_KEY = _require_env("SECRET_KEY")
PARTY_NAME = os.environ.get("PARTY_NAME", "LAN Party")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/data/lanplan.db")
