"""
Log Obfuscator for Home Assistant Sentry

Provides obfuscation of sensitive data in log files including:
- IP addresses (middle two segments)
- API keys and tokens
- URL parameters
- Authorization headers
"""
import logging
import re


class LogObfuscator:
    """Obfuscates sensitive data in log messages"""
    
    # Regex patterns for sensitive data
    # IP address: Match IPv4 addresses and obfuscate middle two octets
    IP_PATTERN = re.compile(r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b')
    
    # API keys and tokens: Common patterns for keys/tokens (typically 8+ alphanumeric characters)
    API_KEY_PATTERN = re.compile(
        r'\b(?:api[_-]?key|token|authorization|password|secret|apikey)["\s:=]+([a-zA-Z0-9_\-]{8,})',
        re.IGNORECASE
    )
    
    # Bearer tokens in Authorization headers
    BEARER_TOKEN_PATTERN = re.compile(
        r'(Bearer\s+)([a-zA-Z0-9_\-\.]+)',
        re.IGNORECASE
    )
    
    # URL parameters that may contain sensitive data
    URL_PARAM_PATTERN = re.compile(
        r'([?&](?:api[_-]?key|token|password|secret|auth)[=])([^&\s]+)',
        re.IGNORECASE
    )
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the obfuscator
        
        Args:
            enabled: Whether obfuscation is enabled (default: True)
        """
        self.enabled = enabled
    
    def obfuscate_ip(self, text: str) -> str:
        """
        Obfuscate IP addresses by replacing middle two segments with ***
        
        Examples:
            192.168.1.100 -> 192.***.***.**100
            10.0.0.5 -> 10.***.***.**5
            
        Args:
            text: Text containing IP addresses
            
        Returns:
            Text with obfuscated IP addresses
        """
        if not self.enabled:
            return text
        
        def replace_ip(match):
            # Keep first octet, obfuscate second and third, keep last octet
            return f"{match.group(1)}.***.***.{match.group(4)}"
        
        return self.IP_PATTERN.sub(replace_ip, text)
    
    def obfuscate_api_key(self, text: str) -> str:
        """
        Obfuscate API keys and tokens
        
        Examples:
            api_key=abc123def456ghi789 -> api_key=abc***ghi789
            token: xyz123456789012345 -> token: xyz***345
            
        Args:
            text: Text containing API keys/tokens
            
        Returns:
            Text with obfuscated keys/tokens
        """
        if not self.enabled:
            return text
        
        def replace_key(match):
            key = match.group(1)
            if len(key) <= 6:
                # Short keys - show first 3 chars
                return match.group(0).replace(key, f"{key[:3]}***")
            else:
                # Longer keys - show first 3 and last 3 chars
                return match.group(0).replace(key, f"{key[:3]}***{key[-3:]}")
        
        return self.API_KEY_PATTERN.sub(replace_key, text)
    
    def obfuscate_bearer_token(self, text: str) -> str:
        """
        Obfuscate Bearer tokens in Authorization headers
        
        Examples:
            Bearer eyJhbGciOiJIUzI1... -> Bearer eyJ***I1...
            authorization: Bearer abc123 -> authorization: Bearer abc***23
            
        Args:
            text: Text containing Bearer tokens
            
        Returns:
            Text with obfuscated Bearer tokens
        """
        if not self.enabled:
            return text
        
        def replace_bearer(match):
            token = match.group(2)
            if len(token) <= 6:
                return f"{match.group(1)}{token[:3]}***"
            else:
                return f"{match.group(1)}{token[:3]}***{token[-2:]}"
        
        return self.BEARER_TOKEN_PATTERN.sub(replace_bearer, text)
    
    def obfuscate_url_params(self, text: str) -> str:
        """
        Obfuscate sensitive URL parameters
        
        Examples:
            ?api_key=secret123 -> ?api_key=sec***23
            &token=abc123def456 -> &token=abc***456
            
        Args:
            text: Text containing URLs with sensitive parameters
            
        Returns:
            Text with obfuscated URL parameters
        """
        if not self.enabled:
            return text
        
        def replace_param(match):
            value = match.group(2)
            if len(value) <= 6:
                return f"{match.group(1)}{value[:3]}***"
            else:
                return f"{match.group(1)}{value[:3]}***{value[-3:]}"
        
        return self.URL_PARAM_PATTERN.sub(replace_param, text)
    
    def obfuscate(self, text: str) -> str:
        """
        Apply all obfuscation rules to the text
        
        Args:
            text: Text to obfuscate
            
        Returns:
            Obfuscated text with sensitive data masked
        """
        if not self.enabled:
            return text
        
        # Apply all obfuscation rules in sequence
        text = self.obfuscate_ip(text)
        text = self.obfuscate_bearer_token(text)
        text = self.obfuscate_api_key(text)
        text = self.obfuscate_url_params(text)
        
        return text


class ObfuscatingFormatter(logging.Formatter):
    """Custom logging formatter that obfuscates sensitive data"""
    
    def __init__(self, fmt=None, datefmt=None, obfuscator=None):
        """
        Initialize the formatter with an obfuscator
        
        Args:
            fmt: Log format string
            datefmt: Date format string
            obfuscator: LogObfuscator instance (if None, creates one with enabled=True)
        """
        super().__init__(fmt, datefmt)
        self.obfuscator = obfuscator or LogObfuscator(enabled=True)
    
    def format(self, record):
        """
        Format the log record and obfuscate sensitive data
        
        Args:
            record: LogRecord to format
            
        Returns:
            Formatted and obfuscated log message
        """
        # Format the message normally
        original_message = super().format(record)
        
        # Apply obfuscation
        return self.obfuscator.obfuscate(original_message)
