"""
CFBD API Error Taxonomy

Consistent exception classes for CFBD API errors.
Allows callers to distinguish between different error types
and handle them appropriately.
"""


class CFBDClientError(Exception):
    """Base exception for all CFBD client errors"""
    
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        """
        Initialize CFBD client error.
        
        Args:
            message: Error message
            status_code: HTTP status code (if available)
            response_body: Response body (if available)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
    
    def __str__(self) -> str:
        if self.status_code:
            return f"{self.message} (HTTP {self.status_code})"
        return self.message


class CFBDAuthenticationError(CFBDClientError):
    """Authentication error (401) - Invalid or missing API key"""
    
    def __init__(self, message: str = "Authentication failed - check API key", response_body: str = None):
        super().__init__(message, status_code=401, response_body=response_body)


class CFBDForbiddenError(CFBDClientError):
    """Forbidden error (403) - API key lacks required permissions"""
    
    def __init__(self, message: str = "Access forbidden - check API key permissions", response_body: str = None):
        super().__init__(message, status_code=403, response_body=response_body)


class CFBDNotFoundError(CFBDClientError):
    """Not found error (404) - Resource does not exist"""
    
    def __init__(self, message: str = "Resource not found", response_body: str = None):
        super().__init__(message, status_code=404, response_body=response_body)


class CFBDRateLimitError(CFBDClientError):
    """Rate limit error (429) - Too many requests"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: float = None, response_body: str = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying (from Retry-After header)
            response_body: Response body (if available)
        """
        super().__init__(message, status_code=429, response_body=response_body)
        self.retry_after = retry_after
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.retry_after:
            return f"{base_msg} - Retry after {self.retry_after}s"
        return base_msg


class CFBDServerError(CFBDClientError):
    """Server error (5xx) - CFBD API server issue"""
    
    def __init__(self, message: str = "Server error", status_code: int = 500, response_body: str = None):
        """
        Initialize server error.
        
        Args:
            message: Error message
            status_code: HTTP status code (500, 502, 503, etc.)
            response_body: Response body (if available)
        """
        if not (500 <= status_code < 600):
            raise ValueError(f"Server error status code must be 5xx, got {status_code}")
        super().__init__(message, status_code=status_code, response_body=response_body)


def convert_api_exception(exception) -> CFBDClientError:
    """
    Convert CFBD ApiException to appropriate CFBDClientError subclass.
    
    Args:
        exception: ApiException from cfbd.rest
        
    Returns:
        Appropriate CFBDClientError subclass
    """
    from cfbd.rest import ApiException
    
    if not isinstance(exception, ApiException):
        return CFBDClientError(str(exception))
    
    status = exception.status
    message = str(exception.reason) if hasattr(exception, 'reason') else str(exception)
    
    # Parse Retry-After header for 429 errors
    retry_after = None
    if status == 429 and hasattr(exception, 'headers') and exception.headers:
        headers = exception.headers
        if isinstance(headers, dict):
            for key, value in headers.items():
                if key.lower() == 'retry-after':
                    try:
                        retry_after = float(value)
                    except (ValueError, TypeError):
                        pass
                    break
        elif hasattr(headers, 'get'):
            retry_after_value = headers.get('Retry-After') or headers.get('retry-after')
            if retry_after_value:
                try:
                    retry_after = float(retry_after_value)
                except (ValueError, TypeError):
                    pass
    
    # Map status codes to error types
    if status == 401:
        return CFBDAuthenticationError(message, response_body=getattr(exception, 'body', None))
    elif status == 403:
        return CFBDForbiddenError(message, response_body=getattr(exception, 'body', None))
    elif status == 404:
        return CFBDNotFoundError(message, response_body=getattr(exception, 'body', None))
    elif status == 429:
        return CFBDRateLimitError(message, retry_after=retry_after, response_body=getattr(exception, 'body', None))
    elif 500 <= status < 600:
        return CFBDServerError(message, status_code=status, response_body=getattr(exception, 'body', None))
    else:
        # Other 4xx errors
        return CFBDClientError(message, status_code=status, response_body=getattr(exception, 'body', None))
