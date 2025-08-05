"""
File utility functions for the workplace relations scraper.
"""

import os
import hashlib
from typing import Optional, List
from urllib.parse import urlparse


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        Sanitize filename for safe filesystem storage.
        
        Args:
            filename: Original filename
            max_length: Maximum length for filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed"
        
        # Remove or replace invalid characters
        keepchars = (' ', '.', '_', '-')
        sanitized = ''.join(c for c in filename if c.isalnum() or c in keepchars)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed"
        
        # Limit length
        if len(sanitized) > max_length:
            name, ext = os.path.splitext(sanitized)
            max_name_length = max_length - len(ext)
            sanitized = name[:max_name_length] + ext
        
        return sanitized
    
    @staticmethod
    def get_file_extension(url: str, content_type: Optional[str] = None) -> str:
        """
        Determine file extension from URL and content type.
        
        Args:
            url: File URL
            content_type: HTTP content type
            
        Returns:
            File extension (without dot)
        """
        # Try to get extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        if path.endswith('.pdf'):
            return 'pdf'
        elif path.endswith('.docx'):
            return 'docx'
        elif path.endswith('.doc'):
            return 'doc'
        elif path.endswith('.html') or path.endswith('.htm'):
            return 'html'
        
        # Try to get extension from content type
        if content_type:
            content_type_lower = content_type.lower()
            if 'pdf' in content_type_lower:
                return 'pdf'
            elif 'docx' in content_type_lower:
                return 'docx'
            elif 'msword' in content_type_lower:
                return 'doc'
            elif 'html' in content_type_lower:
                return 'html'
        
        # Default to html for web content
        return 'html'
    
    @staticmethod
    def calculate_file_hash(content: bytes, algorithm: str = 'sha256') -> str:
        """
        Calculate hash of file content.
        
        Args:
            content: File content as bytes
            algorithm: Hash algorithm to use
            
        Returns:
            Hexadecimal hash string
        """
        if algorithm == 'sha256':
            return hashlib.sha256(content).hexdigest()
        elif algorithm == 'md5':
            return hashlib.md5(content).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """
        Ensure directory exists, create if it doesn't.
        
        Args:
            directory_path: Path to directory
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes or None if file doesn't exist
        """
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return None
        except Exception:
            return None
    
    @staticmethod
    def list_files_in_directory(directory_path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        List files in directory with optional extension filter.
        
        Args:
            directory_path: Path to directory
            extensions: List of file extensions to include (without dot)
            
        Returns:
            List of file paths
        """
        if not os.path.exists(directory_path):
            return []
        
        files = []
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                if extensions:
                    file_ext = os.path.splitext(filename)[1][1:].lower()
                    if file_ext in extensions:
                        files.append(file_path)
                else:
                    files.append(file_path)
        
        return files
    
    @staticmethod
    def is_valid_file_type(filename: str, allowed_extensions: List[str]) -> bool:
        """
        Check if file has allowed extension.
        
        Args:
            filename: Filename to check
            allowed_extensions: List of allowed extensions (without dot)
            
        Returns:
            True if file type is allowed, False otherwise
        """
        file_ext = os.path.splitext(filename)[1][1:].lower()
        return file_ext in allowed_extensions 