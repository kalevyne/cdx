"""One-time OAuth 2.0 authorization for the CDX Box connection.

Run this once, logged in as whichever Box account should own the connection
(e.g. your Berkeley Box account, so CDX inherits its access to CalSol's
folders). Opens the Box consent screen, catches the redirect on a local
server, and exchanges the resulting code for tokens saved to
`settings.box_token_storage_path`. Re-run it if that token file is ever lost
or the authorization is revoked. See backend/README.md for the full flow.
"""

from __future__ import annotations

import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from box_sdk_gen import BoxOAuth, FileTokenStorage, GetAuthorizeUrlOptions, OAuthConfig

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    auth = BoxOAuth(
        OAuthConfig(
            client_id=settings.box_client_id,
            client_secret=settings.box_client_secret,
            token_storage=FileTokenStorage(settings.box_token_storage_path),
        )
    )

    redirect = urlparse(settings.box_redirect_uri)
    authorization_code: list[str] = []

    class _CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            code = parse_qs(urlparse(self.path).query).get("code", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            if code:
                authorization_code.append(code)
                self.wfile.write(b"Authorized. Close this tab and return to the terminal.")
            else:
                self.wfile.write(b"No authorization code received.")

        def log_message(self, *args: object) -> None:
            pass

    authorize_url = auth.get_authorize_url(
        options=GetAuthorizeUrlOptions(redirect_uri=settings.box_redirect_uri)
    )
    print(f"Opening {authorize_url}")
    print("Log in with whichever Box account should own this connection, then approve access.")
    webbrowser.open(authorize_url)

    server = HTTPServer((redirect.hostname, redirect.port), _CallbackHandler)
    server.handle_request()

    if not authorization_code:
        raise SystemExit(
            "No authorization code received — check the redirect URI in "
            "BOX_REDIRECT_URI matches the app's Redirect URI in Box's Developer Console."
        )

    auth.get_tokens_authorization_code_grant(authorization_code[0])
    print(f"Authorized. Token saved to {settings.box_token_storage_path}.")


if __name__ == "__main__":
    main()
