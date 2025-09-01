"""
File handling utilities
"""

import os
import aiofiles
import hashlib
from pathlib import Path
from typing import Optional, BinaryIO
import magic
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """Utility class for handling file operations"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Allowed file types with their MIME types
        self.allowed_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
    
    async def save_file(self, file_content: bytes, filename: str) -> str:
        """Save file content to disk and return file path"""
        try:
            # Create unique filename to avoid conflicts
            file_path = self.upload_dir / self._generate_unique_filename(filename)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info(f"File saved: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {str(e)}")
            raise
    
    async def read_file(self, file_path: str) -> bytes:
        """Read file content from disk"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            return content
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise
    
    def validate_file_type(self, filename: str, file_content: bytes) -> bool:
        """Validate file type using both extension and content"""
        try:
            # Check extension
            file_extension = Path(filename).suffix.lower()
            if file_extension not in self.allowed_types:
                return False
            
            # Check MIME type
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
                expected_mime = self.allowed_types[file_extension]
                
                # Some flexibility for different MIME type variations
                if file_extension == '.pdf' and mime_type.startswith('application/pdf'):
                    return True
                elif file_extension == '.doc' and mime_type in ['application/msword', 'application/x-msword']:
                    return True
                elif file_extension == '.docx' and 'wordprocessingml' in mime_type:
                    return True
                    
                return mime_type == expected_mime
                
            except Exception:
                # If magic detection fails, rely on extension
                return True
            
        except Exception as e:
            logger.error(f"Error validating file type for {filename}: {str(e)}")
            return False
    
    def validate_file_size(self, file_content: bytes, max_size: int) -> bool:
        """Validate file size"""
        return len(file_content) <= max_size
    
    def get_file_info(self, filename: str, file_content: bytes) -> dict:
        """Get file information"""
        file_path = Path(filename)
        
        return {
            "filename": filename,
            "extension": file_path.suffix.lower(),
            "size_bytes": len(file_content),
            "size_mb": round(len(file_content) / (1024 * 1024), 2),
            "hash": self.calculate_file_hash(file_content)
        }
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename to avoid conflicts"""
        file_path = Path(original_filename)
        stem = file_path.stem
        suffix = file_path.suffix
        
        # Add timestamp and hash for uniqueness
        import time
        timestamp = int(time.time())
        hash_part = hashlib.md5(original_filename.encode()).hexdigest()[:8]
        
        return f"{stem}_{timestamp}_{hash_part}{suffix}"
    
    async def cleanup_old_files(self, days_old: int = 7):
        """Clean up files older than specified days"""
        try:
            import time
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            cleaned_count = 0
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")
            return 0
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "upload_directory": str(self.upload_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "upload_directory": str(self.upload_dir),
                "error": str(e)
            }