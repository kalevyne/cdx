from pydantic import BaseModel


class SessionUser(BaseModel):
    """The engineer logged in to the dashboard, as identified by Box. Stored in
    the signed session cookie — never put Box tokens or secrets here."""

    box_user_id: str
    name: str
    login: str
