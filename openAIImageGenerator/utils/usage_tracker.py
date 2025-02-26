import logging
import json
from datetime import datetime, date
import os
import sqlite3
from config import APP_CONFIG

logger = logging.getLogger(__name__)

class UsageTracker:
    """Tracks API usage and costs."""
    
    def __init__(self):
        """Initialize the usage tracker."""
        self.db_file = APP_CONFIG["db_file"]
        self.ensure_db()
        logger.info("Usage tracker initialized")
    
    def ensure_db(self):
        """Ensure the database exists and has the required tables."""
        # Make sure the data directory exists
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create usage_stats table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_stats (
            id INTEGER PRIMARY KEY,
            date DATE UNIQUE,
            total_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            generations_count INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_usage(self, tokens, cost=None):
        """Record API usage."""
        # Calculate cost if not provided (approximate)
        if cost is None:
            # Approximate cost for DALL-E 3
            cost = tokens * 0.00002  # $0.02 per 1000 tokens
        
        today = date.today().isoformat()
        
        # Connect to the database
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Check if we have a record for today
        cursor.execute("SELECT * FROM usage_stats WHERE date = ?", (today,))
        record = cursor.fetchone()
        
        if record:
            # Update existing record
            cursor.execute("""
            UPDATE usage_stats 
            SET total_tokens = total_tokens + ?, 
                total_cost = total_cost + ?,
                generations_count = generations_count + 1
            WHERE date = ?
            """, (tokens, cost, today))
        else:
            # Create new record
            cursor.execute("""
            INSERT INTO usage_stats (date, total_tokens, total_cost, generations_count)
            VALUES (?, ?, ?, 1)
            """, (today, tokens, cost))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded usage: {tokens} tokens, ${cost:.4f}")
    
    def get_usage_stats(self, start_date=None, end_date=None):
        """Get usage statistics for a date range."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        query = "SELECT * FROM usage_stats"
        params = []
        
        if start_date or end_date:
            query += " WHERE "
            
            if start_date:
                query += "date >= ?"
                params.append(start_date)
                
                if end_date:
                    query += " AND "
            
            if end_date:
                query += "date <= ?"
                params.append(end_date)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries
        columns = ["id", "date", "total_tokens", "total_cost", "generations_count"]
        result = []
        for record in records:
            result.append(dict(zip(columns, record)))
        
        return result 
