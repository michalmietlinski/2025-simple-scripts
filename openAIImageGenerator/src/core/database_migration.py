"""Database migration utilities for the OpenAI Image Generator."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handles database schema migrations."""
    
    def __init__(self, db_path: Path):
        """Initialize the database migration utility.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Connect to the database."""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if the table exists, False otherwise
        """
        try:
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return bool(self.cursor.fetchone())
        except sqlite3.Error as e:
            logger.error(f"Error checking if table exists: {str(e)}")
            return False
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            bool: True if the column exists, False otherwise
        """
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()
            return any(column['name'] == column_name for column in columns)
        except sqlite3.Error as e:
            logger.error(f"Error checking if column exists: {str(e)}")
            return False
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get the schema of a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column definitions
        """
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting table schema: {str(e)}")
            return []
    
    def create_version_table(self):
        """Create the schema_version table if it doesn't exist."""
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY,
                version INTEGER NOT NULL,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Check if we need to insert initial version
            self.cursor.execute("SELECT COUNT(*) FROM schema_version")
            count = self.cursor.fetchone()[0]
            
            if count == 0:
                self.cursor.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (1,)
                )
                
            self.connection.commit()
            logger.info("Schema version table created/verified")
        except sqlite3.Error as e:
            logger.error(f"Error creating version table: {str(e)}")
            self.connection.rollback()
            raise
    
    def get_current_version(self) -> int:
        """Get the current schema version.
        
        Returns:
            int: Current schema version
        """
        try:
            self.cursor.execute(
                "SELECT MAX(version) FROM schema_version"
            )
            result = self.cursor.fetchone()
            return result[0] if result and result[0] else 0
        except sqlite3.Error as e:
            logger.error(f"Error getting schema version: {str(e)}")
            return 0
    
    def update_version(self, new_version: int):
        """Update the schema version.
        
        Args:
            new_version: New schema version
        """
        try:
            self.cursor.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (new_version,)
            )
            self.connection.commit()
            logger.info(f"Schema version updated to {new_version}")
        except sqlite3.Error as e:
            logger.error(f"Error updating schema version: {str(e)}")
            self.connection.rollback()
            raise
    
    def migrate_usage_stats_table(self):
        """Migrate from usage_stats to usage_statistics table.
        
        This handles the specific case where we need to migrate from the old
        usage_stats table to the new usage_statistics table.
        """
        try:
            # Check if old table exists
            if not self.table_exists("usage_stats"):
                logger.info("No usage_stats table found, no migration needed")
                return
            
            # Check if new table already exists
            if self.table_exists("usage_statistics"):
                logger.info("usage_statistics table already exists")
            else:
                # Create the new table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_statistics (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL UNIQUE,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    total_cost REAL NOT NULL DEFAULT 0,
                    generations_count INTEGER NOT NULL DEFAULT 0
                )
                ''')
                logger.info("Created usage_statistics table")
            
            # Copy data from old table to new table
            self.cursor.execute('''
            INSERT OR IGNORE INTO usage_statistics 
                (date, total_tokens, total_cost, generations_count)
            SELECT 
                date, total_tokens, total_cost, generations_count 
            FROM usage_stats
            ''')
            
            rows_copied = self.cursor.rowcount
            logger.info(f"Copied {rows_copied} rows from usage_stats to usage_statistics")
            
            # Drop the old table
            self.cursor.execute("DROP TABLE usage_stats")
            logger.info("Dropped usage_stats table")
            
            self.connection.commit()
            logger.info("Usage stats table migration completed successfully")
        except sqlite3.Error as e:
            logger.error(f"Error migrating usage stats table: {str(e)}")
            self.connection.rollback()
            raise
    
    def run_migrations(self):
        """Run all necessary migrations based on current schema version."""
        try:
            self.connect()
            
            # Create version table if it doesn't exist
            self.create_version_table()
            
            current_version = self.get_current_version()
            logger.info(f"Current schema version: {current_version}")
            
            # Run migrations based on version
            if current_version < 2:
                logger.info("Running migration to version 2")
                self.migrate_usage_stats_table()
                self.update_version(2)
            
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Error running migrations: {str(e)}")
            raise
        finally:
            self.close()


def migrate_database(db_path: Path):
    """Run database migrations.
    
    Args:
        db_path: Path to the database file
    """
    try:
        migration = DatabaseMigration(db_path)
        migration.run_migrations()
        logger.info("Database migration completed successfully")
    except Exception as e:
        logger.error(f"Database migration failed: {str(e)}")
        raise 
