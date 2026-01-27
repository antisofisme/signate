"""
ATLAS_SEMAR Backend - Centralized API Routes Definition
Follows PANDAWA Clean Architecture standards (CORE-STD-01)
"""


class APIRoutes:
    """Centralized API route definitions"""

    # API prefix
    PREFIX = "/api/v1"

    # Assistant module routes
    ASSISTANT = f"{PREFIX}/assistant"
    ASSISTANT_VOICE = f"{ASSISTANT}/voice"
    ASSISTANT_STT = f"{ASSISTANT}/stt"
    ASSISTANT_COMMANDS = f"{ASSISTANT}/commands"
    ASSISTANT_SESSION = f"{ASSISTANT}/session"

    # Authentication routes
    AUTH = f"{PREFIX}/auth"
    AUTH_LOGIN = f"{AUTH}/login"
    AUTH_REGISTER = f"{AUTH}/register"


routes = APIRoutes()
