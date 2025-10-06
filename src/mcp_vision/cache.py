import hashlib
import logging
import os
import sqlite3
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class OCRCache:
    """SQLite-based cache for OCR results"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize the OCR cache database
        
        Args:
            db_path: Path to the SQLite database file (default: data/ocr_cache.db)
        """
        if db_path is None:
            # Default to data/ocr_cache.db, creating directory if needed
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "ocr_cache.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ocr_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_hash TEXT NOT NULL UNIQUE,
                        file_path TEXT,
                        ocr_result TEXT NOT NULL,
                        min_confidence REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_hash 
                    ON ocr_cache(file_hash)
                """)
                
                conn.commit()
                logger.info(f"OCR cache database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize cache database: {e}")
            raise
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA256 hash of a file or cache key
        
        Args:
            file_path: Path to the file (local path or URL), or a cache key
            
        Returns:
            SHA256 hash as hex string, or None if file cannot be accessed
        """
        try:
            if file_path.startswith("http://") or file_path.startswith("https://"):
                # For URLs, hash the URL itself as the identifier
                # In a production environment, you might want to download and hash the content
                return hashlib.sha256(file_path.encode()).hexdigest()
            elif "_pages_" in file_path and "_conf_" in file_path:
                # This is a PDF cache key, hash it directly
                return hashlib.sha256(file_path.encode()).hexdigest()
            else:
                # For local files, hash the file content
                if not os.path.isfile(file_path):
                    logger.warning(f"File not found: {file_path}")
                    return None
                
                hash_sha256 = hashlib.sha256()
                with open(file_path, "rb") as f:
                    # Read file in chunks to handle large files efficiently
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_sha256.update(chunk)
                return hash_sha256.hexdigest()
                
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def get(self, file_path: str, min_confidence: float = 0.0) -> Optional[str]:
        """
        Retrieve OCR result from cache
        
        Args:
            file_path: Path to the file (local path or URL)
            min_confidence: Minimum confidence threshold used for OCR
            
        Returns:
            Cached OCR result if found, None otherwise
        """
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            return None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ocr_result FROM ocr_cache 
                    WHERE file_hash = ? AND min_confidence = ?
                """, (file_hash, min_confidence))
                
                result = cursor.fetchone()
                if result:
                    # Update access time
                    cursor.execute("""
                        UPDATE ocr_cache 
                        SET accessed_at = CURRENT_TIMESTAMP 
                        WHERE file_hash = ? AND min_confidence = ?
                    """, (file_hash, min_confidence))
                    conn.commit()
                    
                    logger.info(f"Cache hit for {file_path}")
                    return result[0]
                else:
                    logger.info(f"Cache miss for {file_path}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def put(self, file_path: str, ocr_result: str, min_confidence: float = 0.0):
        """
        Store OCR result in cache
        
        Args:
            file_path: Path to the file (local path or URL)
            ocr_result: OCR result to cache
            min_confidence: Minimum confidence threshold used for OCR
        """
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            logger.warning(f"Cannot cache result for {file_path}: unable to calculate hash")
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Use INSERT OR REPLACE to handle duplicates
                cursor.execute("""
                    INSERT OR REPLACE INTO ocr_cache 
                    (file_hash, file_path, ocr_result, min_confidence, accessed_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (file_hash, file_path, ocr_result, min_confidence))
                
                conn.commit()
                logger.info(f"Cached OCR result for {file_path}")
                
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
    
    def clear(self):
        """Clear all cached entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ocr_cache")
                conn.commit()
                logger.info("Cache cleared successfully")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Tuple[int, float]:
        """
        Get cache statistics
        
        Returns:
            Tuple of (number of entries, database size in MB)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count entries
                cursor.execute("SELECT COUNT(*) FROM ocr_cache")
                count = cursor.fetchone()[0]
                
                # Get database size
                db_size = os.path.getsize(self.db_path) / (1024 * 1024)  # Convert to MB
                
                return count, db_size
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return 0, 0.0


# Global cache instance
_cache = None


def get_cache(db_path: str = None) -> OCRCache:
    """
    Get the global cache instance, initializing if necessary
    
    Args:
        db_path: Path to the SQLite database file (default: data/ocr_cache.db)
        
    Returns:
        OCRCache instance
    """
    global _cache
    if _cache is None:
        _cache = OCRCache(db_path)
    return _cache