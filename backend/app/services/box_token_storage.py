"""Where the backend's own Box OAuth token is kept (see docs/DECISIONS.md #10).

`file` (default) keeps it in BOX_TOKEN_STORAGE_PATH — fine locally. `database`
keeps it in the `box_tokens` table, for hosts whose disk is wiped on every
deploy (Render's free tier). Run scripts/box_oauth_setup.py with the same
DATABASE_URL and BOX_TOKEN_STORAGE=database to authorize a deployment.
"""

import json

from box_sdk_gen import AccessToken, FileTokenStorage, TokenStorage
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.db import get_sessionmaker
from app.models import BoxToken

# Single row: CDX has exactly one backend Box connection.
_ROW_ID = "backend"


class DatabaseTokenStorage(TokenStorage):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def store(self, token: AccessToken) -> None:
        with self._session_factory() as session:
            session.merge(BoxToken(id=_ROW_ID, token_json=json.dumps(token.to_dict())))
            session.commit()

    def get(self) -> AccessToken | None:
        with self._session_factory() as session:
            row = session.get(BoxToken, _ROW_ID)
            return AccessToken.from_dict(json.loads(row.token_json)) if row else None

    def clear(self) -> None:
        with self._session_factory() as session:
            row = session.get(BoxToken, _ROW_ID)
            if row:
                session.delete(row)
                session.commit()


def make_backend_token_storage(settings: Settings) -> TokenStorage:
    if settings.box_token_storage == "database":
        return DatabaseTokenStorage(get_sessionmaker())
    return FileTokenStorage(settings.box_token_storage_path)
