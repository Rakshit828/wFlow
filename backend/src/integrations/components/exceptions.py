class CredentialsNotFoundError(Exception):
    """Raised when no stored/decodable credentials exist for the given user/service."""
    pass 

class CredentialsRevokedError(Exception):
    """Raised when stored/decodable credentials is revoked."""
    pass 

class ConnectionError(Exception):
    pass 
