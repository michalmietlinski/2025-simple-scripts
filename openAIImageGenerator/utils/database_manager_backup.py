import os
import sqlite3
import json
import logging
from datetime import datetime
from config import APP_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for the DALL-E Image Generator application."""
    
    def __init__(self, db_path=None):
        """Initialize the database manager.
        
        Args:
            db_path (str, optional): Path to the SQLite database file. 
                                    Defaults to data/dalle_generator.db.
        """
        self.db_path = db_path or os.path.join(APP_CONFIG.get("data_dir", "data"), "dalle_generator.db")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize the database
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
        logger.info(f"Database initialized at {os.path.abspath(self.db_path)}")
    
    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            logger.info("Connected to database")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("Database connection closed")
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            # Create prompt_history table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY,
                prompt_text TEXT NOT NULL,
                creation_date TIMESTAMP NOT NULL,
                last_used TIMESTAMP NOT NULL,
                favorite BOOLEAN DEFAULT 0,
                tags TEXT,
                usage_count INTEGER DEFAULT 1,
                average_rating FLOAT DEFAULT 0,
                is_template BOOLEAN DEFAULT 0,
                template_variables TEXT
            )
            ''')
            
            # Create template_variables table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS template_variables (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                "values" TEXT NOT NULL,
                creation_date TIMESTAMP NOT NULL,
                last_used TIMESTAMP NOT NULL,
                usage_count INTEGER DEFAULT 1
            )
            ''')
            
            # Create batch_generations table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_generations (
                id INTEGER PRIMARY KEY,
                template_prompt_id INTEGER,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                total_images INTEGER NOT NULL,
                completed_images INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                variable_combinations TEXT,
                FOREIGN KEY (template_prompt_id) REFERENCES prompt_history (id)
            )
            ''')
            
            # Create generation_history table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY,
                prompt_id INTEGER,
                batch_id INTEGER,
                image_path TEXT NOT NULL,
                generation_date TIMESTAMP NOT NULL,
                parameters TEXT NOT NULL,
                token_usage INTEGER NOT NULL,
                cost FLOAT NOT NULL,
                user_rating INTEGER DEFAULT 0,
                description TEXT,
                FOREIGN KEY (prompt_id) REFERENCES prompt_history (id),
                FOREIGN KEY (batch_id) REFERENCES batch_generations (id)
            )
            ''')
            
            # Create usage_stats table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                total_tokens INTEGER NOT NULL,
                total_cost FLOAT NOT NULL,
                generations_count INTEGER NOT NULL
            )
            ''')
            
            self.conn.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    # Prompt History Methods
    
    def add_prompt(self, prompt_text, is_template=False, template_variables=None, tags=None):
        """Add a new prompt to the history.
        
        Args:
            prompt_text (str): The prompt text
            is_template (bool, optional): Whether this is a template prompt. Defaults to False.
            template_variables (list, optional): List of variable names if this is a template. Defaults to None.
            tags (list, optional): List of tags for the prompt. Defaults to None.
            
        Returns:
            int: The ID of the newly created prompt
        """
        try:
            # Check if prompt already exists
            self.cursor.execute(
                "SELECT id, usage_count FROM prompt_history WHERE prompt_text = ?", 
                (prompt_text,)
            )
            existing = self.cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if existing:
                # Update existing prompt
                prompt_id = existing['id']
                usage_count = existing['usage_count'] + 1
                
                self.cursor.execute(
                    "UPDATE prompt_history SET last_used = ?, usage_count = ? WHERE id = ?",
                    (now, usage_count, prompt_id)
                )
                logger.info(f"Updated existing prompt (ID: {prompt_id}), usage count: {usage_count}")
            else:
                # Insert new prompt
                template_vars_json = json.dumps(template_variables) if template_variables else None
                tags_str = ",".join(tags) if tags else None
                
                self.cursor.execute(
                    """
                    INSERT INTO prompt_history 
                    (prompt_text, creation_date, last_used, is_template, template_variables, tags) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (prompt_text, now, now, is_template, template_vars_json, tags_str)
                )
                prompt_id = self.cursor.lastrowid
                logger.info(f"Added new prompt to history (ID: {prompt_id})")
            
            self.conn.commit()
            return prompt_id
        except sqlite3.Error as e:
            logger.error(f"Error adding prompt to history: {str(e)}")
            self.conn.rollback()
            raise
    
    def get_prompt_history(self, limit=50, offset=0, search=None, favorites_only=False, tags=None):
        """Get prompt history with optional filtering.
        
        Args:
            limit (int, optional): Maximum number of prompts to return. Defaults to 50.
            offset (int, optional): Offset for pagination. Defaults to 0.
            search (str, optional): Search term to filter prompts. Defaults to None.
            favorites_only (bool, optional): Only return favorite prompts. Defaults to False.
            tags (list, optional): Filter by tags. Defaults to None.
            
        Returns:
            list: List of prompt dictionaries
        """
        try:
            query = "SELECT * FROM prompt_history"
            params = []
            
            # Build WHERE clause based on filters
            where_clauses = []
            
            if search:
                where_clauses.append("prompt_text LIKE ?")
                params.append(f"%{search}%")
            
            if favorites_only:
                where_clauses.append("favorite = 1")
            
            if tags:
                # For each tag, check if it's in the comma-separated tags field
                tag_clauses = []
                for tag in tags:
                    tag_clauses.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                
                where_clauses.append("(" + " OR ".join(tag_clauses) + ")")
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add ordering and pagination
            query += " ORDER BY last_used DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            self.cursor.execute(query, params)
            results = [dict(row) for row in self.cursor.fetchall()]
            
            # Process results
            for row in results:
                # Convert template_variables from JSON string to Python object
                if row['template_variables']:
                    row['template_variables'] = json.loads(row['template_variables'])
                
                # Convert tags from comma-separated string to list
                if row['tags']:
                    row['tags'] = row['tags'].split(',')
                else:
                    row['tags'] = []
            
            return results
        except sqlite3.Error as e:
            logger.error(f"Error retrieving prompt history: {str(e)}")
            raise
    
    def update_prompt(self, prompt_id, **kwargs):
        """Update a prompt in the history.
        
        Args:
            prompt_id (int): The ID of the prompt to update
            **kwargs: Fields to update (prompt_text, favorite, tags, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Build SET clause based on provided fields
            set_clauses = []
            params = []
            
            for key, value in kwargs.items():
                if key in ['prompt_text', 'favorite', 'average_rating', 'is_template']:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
                elif key == 'tags' and isinstance(value, list):
                    set_clauses.append("tags = ?")
                    params.append(",".join(value))
                elif key == 'template_variables' and (isinstance(value, list) or isinstance(value, dict)):
                    set_clauses.append("template_variables = ?")
                    params.append(json.dumps(value))
            
            if not set_clauses:
                logger.warning(f"No valid fields provided to update prompt {prompt_id}")
                return False
            
            # Add prompt_id to params
            params.append(prompt_id)
            
            query = f"UPDATE prompt_history SET {', '.join(set_clauses)} WHERE id = ?"
            self.cursor.execute(query, params)
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Updated prompt {prompt_id}")
                return True
            else:
                logger.warning(f"No prompt found with ID {prompt_id}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error updating prompt {prompt_id}: {str(e)}")
            self.conn.rollback()
            return False
    
    # Generation History Methods
    
    def add_generation(self, prompt_id, image_path, parameters, token_usage, cost, description=None, batch_id=None):
        """Record a new image generation.
        
        Args:
            prompt_id (int): The ID of the prompt used
            image_path (str): Path to the saved image
            parameters (dict): Generation parameters (size, quality, etc.)
            token_usage (int): Number of tokens used
            cost (float): Estimated cost of the generation
            description (str, optional): Optional description. Defaults to None.
            batch_id (int, optional): Batch ID if part of a batch generation. Defaults to None.
            
        Returns:
            int: The ID of the newly created generation record
        """
        try:
            now = datetime.now().isoformat()
            parameters_json = json.dumps(parameters)
            
            self.cursor.execute(
                """
                INSERT INTO generation_history 
                (prompt_id, batch_id, image_path, generation_date, parameters, token_usage, cost, description) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (prompt_id, batch_id, image_path, now, parameters_json, token_usage, cost, description)
            )
            generation_id = self.cursor.lastrowid
            
            # Update usage stats for the day
            self.update_usage_stats(token_usage, cost)
            
            # If part of a batch, update the batch progress
            if batch_id:
                self.cursor.execute(
                    "UPDATE batch_generations SET completed_images = completed_images + 1 WHERE id = ?",
                    (batch_id,)
                )
                
                # Check if batch is complete
                self.cursor.execute(
                    "SELECT completed_images, total_images FROM batch_generations WHERE id = ?",
                    (batch_id,)
                )
                batch = self.cursor.fetchone()
                
                if batch and batch['completed_images'] >= batch['total_images']:
                    # Mark batch as complete
                    self.cursor.execute(
                        "UPDATE batch_generations SET status = 'completed', end_time = ? WHERE id = ?",
                        (now, batch_id)
                    )
            
            self.conn.commit()
            logger.info(f"Added generation record (ID: {generation_id})")
            return generation_id
        except sqlite3.Error as e:
            logger.error(f"Error adding generation record: {str(e)}")
            self.conn.rollback()
            raise
    
    def get_generation_history(self, limit=20, offset=0, prompt_id=None, batch_id=None, date_from=None, date_to=None):
        """Get generation history with optional filtering.
        
        Args:
            limit (int, optional): Maximum number of records to return. Defaults to 20.
            offset (int, optional): Offset for pagination. Defaults to 0.
            prompt_id (int, optional): Filter by prompt ID. Defaults to None.
            batch_id (int, optional): Filter by batch ID. Defaults to None.
            date_from (str, optional): Filter by date range (start). Defaults to None.
            date_to (str, optional): Filter by date range (end). Defaults to None.
            
        Returns:
            list: List of generation dictionaries
        """
        try:
            query = """
            SELECT g.*, p.prompt_text 
            FROM generation_history g
            LEFT JOIN prompt_history p ON g.prompt_id = p.id
            """
            params = []
            
            # Build WHERE clause based on filters
            where_clauses = []
            
            if prompt_id:
                where_clauses.append("g.prompt_id = ?")
                params.append(prompt_id)
            
            if batch_id:
                where_clauses.append("g.batch_id = ?")
                params.append(batch_id)
            
            if date_from:
                where_clauses.append("g.generation_date >= ?")
                params.append(date_from)
            
            if date_to:
                where_clauses.append("g.generation_date <= ?")
                params.append(date_to)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add ordering and pagination
            query += " ORDER BY g.generation_date DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            self.cursor.execute(query, params)
            results = [dict(row) for row in self.cursor.fetchall()]
            
            # Process results
            for row in results:
                # Convert parameters from JSON string to Python object
                if row['parameters']:
                    row['parameters'] = json.loads(row['parameters'])
            
            return results
        except sqlite3.Error as e:
            logger.error(f"Error retrieving generation history: {str(e)}")
            raise
    
    # Template Variables Methods
    
    def add_template_variable(self, name, values):
        """Add a new template variable.
        
        Args:
            name (str): Variable name
            values (list): Possible values for the variable
            
        Returns:
            int: The ID of the newly created variable
        """
        try:
            now = datetime.now().isoformat()
            values_json = json.dumps(values)
            
            # Check if variable already exists
            self.cursor.execute("SELECT id FROM template_variables WHERE name = ?", (name,))
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing variable
                self.cursor.execute(
                    """
                    UPDATE template_variables SET "values" = ?, last_used = ? WHERE id = ?
                    """,
                    (values_json, now, existing['id'])
                )
                variable_id = existing['id']
                logger.info(f"Updated existing template variable '{name}' (ID: {variable_id})")
            else:
                # Insert new variable
                self.cursor.execute(
                    """
                    INSERT INTO template_variables 
                    (name, "values", creation_date, last_used) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, values_json, now, now)
                )
                variable_id = self.cursor.lastrowid
                logger.info(f"Added new template variable '{name}' (ID: {variable_id})")
            
            self.conn.commit()
            return variable_id
        except sqlite3.Error as e:
            logger.error(f"Error adding template variable: {str(e)}")
            self.conn.rollback()
            raise
    
    def get_template_variables(self):
        """Get all template variables.
        
        Returns:
            list: List of template variable dictionaries
        """
        try:
            self.cursor.execute("SELECT * FROM template_variables ORDER BY name")
            results = [dict(row) for row in self.cursor.fetchall()]
            
            # Process results
            for row in results:
                # Convert values from JSON string to Python object
                if row['values']:
                    row['values'] = json.loads(row['values'])
            
            return results
        except sqlite3.Error as e:
            logger.error(f"Error retrieving template variables: {str(e)}")
            raise
    
    # Batch Generation Methods
    
    def create_batch(self, template_prompt_id, total_images, variable_combinations=None):
        """Create a new batch generation job.
        
        Args:
            template_prompt_id (int): The ID of the template prompt
            total_images (int): Total number of images to generate
            variable_combinations (list, optional): List of variable combinations. Defaults to None.
            
        Returns:
            int: The ID of the newly created batch
        """
        try:
            now = datetime.now().isoformat()
            combinations_json = json.dumps(variable_combinations) if variable_combinations else None
            
            self.cursor.execute(
                """
                INSERT INTO batch_generations 
                (template_prompt_id, start_time, total_images, status, variable_combinations) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (template_prompt_id, now, total_images, 'pending', combinations_json)
            )
            batch_id = self.cursor.lastrowid
            self.conn.commit()
            
            logger.info(f"Created batch generation job (ID: {batch_id})")
            return batch_id
        except sqlite3.Error as e:
            logger.error(f"Error creating batch generation job: {str(e)}")
            self.conn.rollback()
            raise
    
    def update_batch_status(self, batch_id, status, end_time=None):
        """Update the status of a batch generation job.
        
        Args:
            batch_id (int): The ID of the batch
            status (str): New status ('pending', 'in_progress', 'completed', 'failed')
            end_time (str, optional): End time if completed or failed. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if end_time is None and status in ['completed', 'failed']:
                end_time = datetime.now().isoformat()
            
            if end_time:
                self.cursor.execute(
                    "UPDATE batch_generations SET status = ?, end_time = ? WHERE id = ?",
                    (status, end_time, batch_id)
                )
            else:
                self.cursor.execute(
                    "UPDATE batch_generations SET status = ? WHERE id = ?",
                    (status, batch_id)
                )
            
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Updated batch {batch_id} status to '{status}'")
                return True
            else:
                logger.warning(f"No batch found with ID {batch_id}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error updating batch status: {str(e)}")
            self.conn.rollback()
            return False
    
    # Usage Stats Methods
    
    def update_usage_stats(self, tokens, cost):
        """Update usage statistics for the current day.
        
        Args:
            tokens (int): Number of tokens used
            cost (float): Cost of the generation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            today = datetime.now().date().isoformat()
            
            # Check if we already have a record for today
            self.cursor.execute("SELECT * FROM usage_stats WHERE date = ?", (today,))
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing record
                self.cursor.execute(
                    """
                    UPDATE usage_stats 
                    SET total_tokens = total_tokens + ?, 
                        total_cost = total_cost + ?,
                        generations_count = generations_count + 1
                    WHERE date = ?
                    """,
                    (tokens, cost, today)
                )
            else:
                # Insert new record
                self.cursor.execute(
                    """
                    INSERT INTO usage_stats 
                    (date, total_tokens, total_cost, generations_count) 
                    VALUES (?, ?, ?, 1)
                    """,
                    (today, tokens, cost)
                )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating usage stats: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_usage_stats(self, days=30):
        """Get usage statistics for a specified number of days.
        
        Args:
            days (int, optional): Number of days to retrieve. Defaults to 30.
            
        Returns:
            list: List of usage stat dictionaries
        """
        try:
            self.cursor.execute(
                "SELECT * FROM usage_stats ORDER BY date DESC LIMIT ?",
                (days,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving usage stats: {str(e)}")
            raise
    
    def get_total_usage(self):
        """Get total usage statistics.
        
        Returns:
            dict: Dictionary with total tokens, cost, and generations
        """
        try:
            self.cursor.execute(
                """
                SELECT 
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost) as total_cost,
                    SUM(generations_count) as total_generations
                FROM usage_stats
                """
            )
            result = self.cursor.fetchone()
            
            if result:
                return dict(result)
            else:
                return {
                    'total_tokens': 0,
                    'total_cost': 0,
                    'total_generations': 0
                }
        except sqlite3.Error as e:
            logger.error(f"Error retrieving total usage: {str(e)}")
            raise 
