import secrets
import hashlib

API_KEY_PREFIX = "rag_"

def generate_api_key() -> str:
    """
    Generates a secure, random API key.
    Returned ONLY once to the user.
    """
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """
    Hashes the API key for safe storage.
    Raw API keys are NEVER stored.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()
