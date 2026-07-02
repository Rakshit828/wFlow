class CredentialsNotFoundError(Exception):
    """Raised when no stored/decodable credentials exist for the given user/service."""
    pass 


class ConnectionError(Exception):
    pass 
