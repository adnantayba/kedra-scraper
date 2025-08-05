"""
Validation utility functions for the workplace relations scraper.
"""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import os


class ValidationUtils:
    """Utility class for data validation."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if valid URL, False otherwise
        """
        if not url:
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email string to validate
            
        Returns:
            True if valid email, False otherwise
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_date_string(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
        """
        Validate date string format.
        
        Args:
            date_str: Date string to validate
            format_str: Expected date format
            
        Returns:
            True if valid date string, False otherwise
        """
        if not date_str:
            return False
        
        try:
            from datetime import datetime
            datetime.strptime(date_str, format_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_identifier(identifier: str) -> bool:
        """
        Validate document identifier.
        
        Args:
            identifier: Identifier string to validate
            
        Returns:
            True if valid identifier, False otherwise
        """
        if not identifier:
            return False
        
        # Check if identifier contains only alphanumeric characters, spaces, and common punctuation
        pattern = r'^[a-zA-Z0-9\s\-_.,()]+$'
        return bool(re.match(pattern, identifier))
    
    @staticmethod
    def is_valid_filename(filename: str) -> bool:
        """
        Validate filename for filesystem safety.
        
        Args:
            filename: Filename to validate
            
        Returns:
            True if valid filename, False otherwise
        """
        if not filename:
            return False
        
        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        return not any(char in filename for char in invalid_chars)
    
    @staticmethod
    def validate_document_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate document data and return validation errors.
        
        Args:
            data: Document data dictionary
            
        Returns:
            Dictionary with field names as keys and lists of error messages as values
        """
        errors = {}
        
        # Validate required fields
        required_fields = ['identifier', 'body', 'partition_date']
        for field in required_fields:
            if not data.get(field):
                errors[field] = [f"{field} is required"]
        
        # Validate identifier
        if data.get('identifier') and not ValidationUtils.is_valid_identifier(data['identifier']):
            if 'identifier' not in errors:
                errors['identifier'] = []
            errors['identifier'].append("Invalid identifier format")
        
        # Validate URL if present
        if data.get('link_to_doc') and not ValidationUtils.is_valid_url(data['link_to_doc']):
            if 'link_to_doc' not in errors:
                errors['link_to_doc'] = []
            errors['link_to_doc'].append("Invalid URL format")
        
        # Validate date if present
        if data.get('published_date'):
            if not ValidationUtils.is_valid_date_string(data['published_date'], "%d/%m/%Y"):
                if 'published_date' not in errors:
                    errors['published_date'] = []
                errors['published_date'].append("Invalid date format (expected DD/MM/YYYY)")
        
        # Validate file path if present
        if data.get('file_path') and not ValidationUtils.is_valid_filename(os.path.basename(data['file_path'])):
            if 'file_path' not in errors:
                errors['file_path'] = []
            errors['file_path'].append("Invalid filename")
        
        return errors
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string value.
        
        Args:
            value: String to sanitize
            max_length: Maximum length (truncate if longer)
            
        Returns:
            Sanitized string
        """
        if not value:
            return ""
        
        # Remove leading/trailing whitespace
        sanitized = value.strip()
        
        # Remove null characters
        sanitized = sanitized.replace('\x00', '')
        
        # Truncate if too long
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def is_valid_file_size(size_bytes: int, max_size_mb: int = 100) -> bool:
        """
        Validate file size.
        
        Args:
            size_bytes: File size in bytes
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            True if valid size, False otherwise
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        return 0 <= size_bytes <= max_size_bytes
    
    @staticmethod
    def is_valid_file_type(file_type: str, allowed_types: List[str]) -> bool:
        """
        Validate file type.
        
        Args:
            file_type: File type to validate
            allowed_types: List of allowed file types
            
        Returns:
            True if valid file type, False otherwise
        """
        return file_type.lower() in [t.lower() for t in allowed_types] 