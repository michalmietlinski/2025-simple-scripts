"""Database manager for the DALL-E Image Generator application."""

import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path

from ..utils.error_handler import DatabaseError

from .data_models import (
    Prompt, 
    TemplateVariable, 
    BatchGeneration, 
    Generation, 
    UsageStat
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations."""
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
        logger.info(f"Database initialized at {self.db_path.absolute()}")
    
    def connect(self):
        """Connect to SQLite database."""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            logger.info("Connected to database")
        except sqlite3.Error as e:
            error_msg = f"Error connecting to database: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def ensure_connection(self):
        """Ensure database connection is open."""
        try:
            # Try a simple query to check connection
            self.cursor.execute("SELECT 1")
        except (sqlite3.Error, AttributeError):
            logger.info("Reconnecting to database")
            self.connect()
    
    def close(self):
        """Close the database connection."""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            # Prompt History table
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
            
            # Template Variables table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS template_variables (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                value_list TEXT NOT NULL,
                creation_date TIMESTAMP NOT NULL,
                last_used TIMESTAMP NOT NULL,
                usage_count INTEGER DEFAULT 1
            )
            ''')
            
            # Generation History table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY,
                prompt_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                parameters TEXT NOT NULL,
                token_usage INTEGER NOT NULL,
                cost REAL NOT NULL,
                creation_date TIMESTAMP NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompt_history (id)
            )
            ''')
            
            # Usage Statistics table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_statistics (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL UNIQUE,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                total_cost REAL NOT NULL DEFAULT 0,
                generations_count INTEGER NOT NULL DEFAULT 0
            )
            ''')
            
            self.connection.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            error_msg = f"Error creating database tables: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def add_prompt(self, prompt: Prompt) -> int:
        """Add or update a prompt in history.
        
        Args:
            prompt: Prompt object to add/update
            
        Returns:
            int: ID of the prompt
        """
        try:
            # Check if prompt exists
            self.cursor.execute(
                "SELECT id, usage_count FROM prompt_history WHERE prompt_text = ?",
                (prompt.prompt_text,)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing prompt
                prompt_id = existing['id']
                usage_count = existing['usage_count'] + 1
                
                self.cursor.execute(
                    "UPDATE prompt_history SET last_used = ?, usage_count = ? WHERE id = ?",
                    (datetime.now().isoformat(), usage_count, prompt_id)
                )
                logger.info(f"Updated existing prompt (ID: {prompt_id})")
            else:
                # Insert new prompt
                prompt_dict = prompt.to_dict()
                self.cursor.execute(
                    """
                    INSERT INTO prompt_history 
                    (prompt_text, creation_date, last_used, favorite, tags, 
                     usage_count, average_rating, is_template, template_variables)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        prompt_dict['prompt_text'],
                        prompt_dict['creation_date'],
                        prompt_dict['last_used'],
                        prompt_dict['favorite'],
                        ','.join(prompt_dict['tags']),
                        prompt_dict['usage_count'],
                        prompt_dict['average_rating'],
                        prompt_dict['is_template'],
                        json.dumps(prompt_dict['template_variables'])
                    )
                )
                prompt_id = self.cursor.lastrowid
                logger.info(f"Added new prompt (ID: {prompt_id})")
            
            self.connection.commit()
            return prompt_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding prompt: {str(e)}")
            self.connection.rollback()
            raise
    
    def save_prompt(self, prompt_text: str, is_template: bool = False, template_variables: Optional[List[str]] = None) -> int:
        """Save a prompt to the database.
        
        Args:
            prompt_text: The text of the prompt
            is_template: Whether this is a template prompt
            template_variables: List of template variable names if is_template is True
            
        Returns:
            int: ID of the saved prompt
        """
        try:
            # Ensure connection is open
            self.ensure_connection()
            
            # Create a Prompt object
            prompt = Prompt(
                prompt_text=prompt_text,
                is_template=is_template,
                template_variables=template_variables or []
            )
            
            # Use the add_prompt method to save it
            return self.add_prompt(prompt)
            
        except sqlite3.Error as e:
            logger.error(f"Error saving prompt: {str(e)}")
            raise DatabaseError("Failed to save prompt") from e
    
    def get_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """Get a specific prompt by ID.
        
        Args:
            prompt_id: ID of the prompt to retrieve
            
        Returns:
            Optional[Prompt]: Prompt object if found, None otherwise
        """
        try:
            self.cursor.execute("SELECT * FROM prompt_history WHERE id = ?", (prompt_id,))
            row = self.cursor.fetchone()
            return Prompt.from_dict(dict(row)) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error getting prompt: {str(e)}")
            raise
    
    def get_prompt_history(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        favorites_only: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Prompt]:
        """Get prompt history with optional filtering.
        
        Args:
            limit: Maximum number of prompts to return
            offset: Number of prompts to skip
            search: Search term to filter prompts
            favorites_only: Only return favorite prompts
            tags: Filter by tags
            
        Returns:
            List[Prompt]: List of matching prompts
        """
        try:
            query = "SELECT * FROM prompt_history"
            params = []
            where_clauses = []
            
            if search:
                where_clauses.append("prompt_text LIKE ?")
                params.append(f"%{search}%")
            
            if favorites_only:
                where_clauses.append("favorite = 1")
            
            if tags:
                tag_clauses = []
                for tag in tags:
                    tag_clauses.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                where_clauses.append("(" + " OR ".join(tag_clauses) + ")")
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY last_used DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            self.cursor.execute(query, params)
            return [Prompt.from_dict(dict(row)) for row in self.cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting prompt history: {str(e)}")
            raise
    
    def add_generation(self, generation: Generation) -> int:
        """Add a new generation to history.
        
        Args:
            generation: Generation object to add
            
        Returns:
            int: ID of the new generation
        """
        try:
            generation_dict = generation.to_dict()
            self.cursor.execute(
                """
                INSERT INTO generation_history
                (prompt_id, image_path, parameters, token_usage, cost, creation_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    generation_dict['prompt_id'],
                    generation_dict['image_path'],
                    json.dumps(generation_dict['parameters']),
                    generation_dict['token_usage'],
                    generation_dict['cost'],
                    generation_dict['generation_date']
                )
            )
            
            generation_id = self.cursor.lastrowid
            self.connection.commit()
            
            # Update usage stats
            self.update_usage_stats(
                generation_dict['token_usage'],
                generation_dict['cost']
            )
            
            logger.info(f"Added new generation (ID: {generation_id})")
            return generation_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding generation: {str(e)}")
            self.connection.rollback()
            raise
    
    def update_usage_stats(self, tokens: int, cost: float):
        """Update usage statistics for the current day.
        
        Args:
            tokens: Number of tokens used
            cost: Cost of the generation
        """
        try:
            self.ensure_connection()
            
            # Get today's date in ISO format
            today = datetime.now().date().isoformat()
            
            # Try to update the new table first
            try:
                # Check if we already have a record for today
                self.cursor.execute(
                    """
                    SELECT id, total_tokens, total_cost, generations_count
                    FROM usage_statistics
                    WHERE date = ?
                    """,
                    (today,)
                )
                
                row = self.cursor.fetchone()
                
                if row:
                    # Update existing record
                    self.cursor.execute(
                        """
                        UPDATE usage_statistics
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
                        INSERT INTO usage_statistics
                        (date, total_tokens, total_cost, generations_count)
                        VALUES (?, ?, ?, 1)
                        """,
                        (today, tokens, cost)
                    )
                    
                self.connection.commit()
                logger.info(f"Updated usage stats: {tokens} tokens, ${cost:.4f}")
                
            except sqlite3.OperationalError as e:
                # If the new table doesn't exist, try the old table name
                if "no such table: usage_statistics" in str(e):
                    logger.warning("usage_statistics table not found, trying usage_stats")
                    
                    # Check if we already have a record for today
                    self.cursor.execute(
                        """
                        SELECT id, total_tokens, total_cost, generations_count
                        FROM usage_stats
                        WHERE date = ?
                        """,
                        (today,)
                    )
                    
                    row = self.cursor.fetchone()
                    
                    if row:
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
                        
                    self.connection.commit()
                    logger.info(f"Updated usage stats (old table): {tokens} tokens, ${cost:.4f}")
                else:
                    # If it's a different error, re-raise it
                    raise
                
        except sqlite3.Error as e:
            logger.error(f"Error updating usage stats: {str(e)}")
            self.connection.rollback()
            raise DatabaseError(f"Failed to update usage statistics: {str(e)}")

    def get_generation_count(self) -> int:
        """Get total number of generations.
        
        Returns:
            int: Total number of generations
        """
        try:
            # Ensure connection is open
            self.ensure_connection()
            
            self.cursor.execute("SELECT COUNT(*) FROM generation_history")
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Error getting generation count: {str(e)}")
            raise DatabaseError("Failed to get generation count") from e

    def get_generations(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Generation]:
        """Get generation history with optional filtering.
        
        Args:
            limit: Maximum number of generations to return
            offset: Number of generations to skip
            search: Optional search term for filtering
            
        Returns:
            List[Generation]: List of matching generations
        """
        try:
            # Ensure connection is open
            self.ensure_connection()
            
            # Use creation_date from DB but alias it as generation_date for the model
            query = """
                SELECT 
                    gh.id, 
                    gh.prompt_id, 
                    gh.image_path, 
                    gh.parameters, 
                    gh.token_usage, 
                    gh.cost, 
                    gh.creation_date as generation_date,
                    ph.prompt_text
                FROM generation_history gh
                LEFT JOIN prompt_history ph ON gh.prompt_id = ph.id
            """
            params = []
            
            if search:
                query += " WHERE ph.prompt_text LIKE ? OR gh.parameters LIKE ?"
                params.extend([f"%{search}%", f"%{search}%"])
            
            query += " ORDER BY gh.creation_date DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            self.cursor.execute(query, params)
            return [Generation.from_dict(dict(row)) for row in self.cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting generations: {str(e)}")
            raise DatabaseError("Failed to get generations") from e

    def get_generation(self, generation_id: int) -> Optional[Generation]:
        """Get a specific generation by ID.
        
        Args:
            generation_id: ID of the generation to retrieve
            
        Returns:
            Optional[Generation]: Generation if found, None otherwise
        """
        try:
            # Ensure connection is open
            self.ensure_connection()
            
            # Use creation_date from DB but alias it as generation_date for the model
            self.cursor.execute(
                """
                SELECT 
                    gh.id, 
                    gh.prompt_id, 
                    gh.image_path, 
                    gh.parameters, 
                    gh.token_usage, 
                    gh.cost, 
                    gh.creation_date as generation_date,
                    ph.prompt_text
                FROM generation_history gh
                LEFT JOIN prompt_history ph ON gh.prompt_id = ph.id
                WHERE gh.id = ?
                """,
                (generation_id,)
            )
            row = self.cursor.fetchone()
            return Generation.from_dict(dict(row)) if row else None
            
        except sqlite3.Error as e:
            logger.error(f"Error getting generation: {str(e)}")
            raise DatabaseError("Failed to get generation") from e

    def update_generation_rating(self, generation_id: int, rating: int):
        """Update the rating for a generation.
        
        Args:
            generation_id: ID of the generation to update
            rating: New rating value (1-5)
        """
        try:
            self.cursor.execute(
                "UPDATE generation_history SET user_rating = ? WHERE id = ?",
                (rating, generation_id)
            )
            self.connection.commit()
            logger.info(f"Updated rating for generation {generation_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Error updating generation rating: {str(e)}")
            self.connection.rollback()
            raise DatabaseError("Failed to update rating") from e

    def delete_generation(self, generation_id: int):
        """Delete a generation and its associated files.
        
        Args:
            generation_id: ID of the generation to delete
        """
        try:
            # Get image path before deleting
            self.cursor.execute(
                "SELECT image_path FROM generation_history WHERE id = ?",
                (generation_id,)
            )
            row = self.cursor.fetchone()
            
            if row:
                # Delete from database
                self.cursor.execute(
                    "DELETE FROM generation_history WHERE id = ?",
                    (generation_id,)
                )
                self.connection.commit()
                logger.info(f"Deleted generation {generation_id}")
                
                # Return image path for cleanup
                return row["image_path"]
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting generation: {str(e)}")
            self.connection.rollback()
            raise DatabaseError("Failed to delete generation") from e

    # Template Methods
    
    def add_template(self, template_text: str, variables: List[str] = None) -> int:
        """Add a new template to the database.
        
        Args:
            template_text: The template text
            variables: List of variable names in the template
            
        Returns:
            int: The ID of the newly created template
        """
        try:
            now = datetime.now().isoformat()
            
            # Convert variables list to JSON
            variables_json = json.dumps(variables) if variables else None
            
            self.cursor.execute(
                """
                INSERT INTO prompt_history 
                (prompt_text, template_variables, creation_date, last_used, is_template) 
                VALUES (?, ?, ?, ?, 1)
                """,
                (template_text, variables_json, now, now)
            )
            
            template_id = self.cursor.lastrowid
            self.connection.commit()
            
            logger.info(f"Added template with ID: {template_id}")
            return template_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding template: {str(e)}")
            self.connection.rollback()
            raise DatabaseError("Failed to add template") from e
    
    def clone_template(self, template_id: int) -> int:
        """Clone an existing template.
        
        Args:
            template_id: The ID of the template to clone
            
        Returns:
            int: The ID of the newly created template clone
        """
        try:
            # Get the template to clone
            self.cursor.execute(
                """
                SELECT prompt_text, template_variables
                FROM prompt_history
                WHERE id = ? AND is_template = 1
                """,
                (template_id,)
            )
            
            row = self.cursor.fetchone()
            if not row:
                logger.warning(f"No template found with ID {template_id}")
                raise DatabaseError(f"Template with ID {template_id} not found")
            
            template_text, variables_json = row
            
            # Parse variables
            variables = json.loads(variables_json) if variables_json else []
            
            # Create a new template with the same content
            now = datetime.now().isoformat()
            
            # Add "Copy" to the template name
            template_text = f"{template_text} (Copy)"
            
            self.cursor.execute(
                """
                INSERT INTO prompt_history 
                (prompt_text, template_variables, creation_date, last_used, is_template) 
                VALUES (?, ?, ?, ?, 1)
                """,
                (template_text, variables_json, now, now)
            )
            
            new_template_id = self.cursor.lastrowid
            self.connection.commit()
            
            logger.info(f"Cloned template {template_id} to new template {new_template_id}")
            return new_template_id
            
        except sqlite3.Error as e:
            logger.error(f"Error cloning template {template_id}: {str(e)}")
            self.connection.rollback()
            raise DatabaseError(f"Failed to clone template {template_id}") from e
            
    def update_template(self, template_id: int, template_text: str = None, variables: List[str] = None) -> bool:
        """Update an existing template.
        
        Args:
            template_id: The ID of the template to update
            template_text: The new template text
            variables: List of variable names in the template
            
        Returns:
            bool: True if successful
        """
        try:
            # Build SET clause based on provided fields
            set_clauses = []
            params = []
            
            if template_text is not None:
                set_clauses.append("prompt_text = ?")
                params.append(template_text)
                
            if variables is not None:
                set_clauses.append("template_variables = ?")
                params.append(json.dumps(variables))
                
            if not set_clauses:
                logger.warning(f"No valid fields provided to update template {template_id}")
                return False
                
            # Update last_used timestamp
            set_clauses.append("last_used = ?")
            params.append(datetime.now().isoformat())
            
            # Add template_id to params
            params.append(template_id)
            
            query = f"UPDATE prompt_history SET {', '.join(set_clauses)} WHERE id = ? AND is_template = 1"
            self.cursor.execute(query, params)
            self.connection.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Updated template {template_id}")
                return True
            else:
                logger.warning(f"No template found with ID {template_id}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            self.connection.rollback()
            raise DatabaseError(f"Failed to update template {template_id}") from e
            
    def delete_template(self, template_id: int) -> bool:
        """Delete a template from the database.
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            bool: True if successful
        """
        try:
            self.cursor.execute(
                "DELETE FROM prompt_history WHERE id = ? AND is_template = 1", 
                (template_id,)
            )
            
            self.connection.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Deleted template with ID: {template_id}")
                return True
            else:
                logger.warning(f"No template found with ID {template_id}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting template: {str(e)}")
            self.connection.rollback()
            raise DatabaseError("Failed to delete template") from e
    
    def get_template_history(self, template_id: int = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get template history from the database.
        
        Args:
            template_id: ID of a specific template to retrieve
            limit: Maximum number of templates to return
            
        Returns:
            List[Dict[str, Any]]: List of template dictionaries
        """
        try:
            # Ensure connection is open
            self.ensure_connection()
            
            query = """
                SELECT p.id, p.prompt_text, p.template_variables, p.creation_date, p.favorite
                FROM prompt_history p
                WHERE p.is_template = 1
            """
            
            params = []
            
            if template_id:
                query += " AND p.id = ?"
                params.append(template_id)
                
            query += " ORDER BY p.creation_date DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
                
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            templates = []
            for row in results:
                # Parse variables
                variables = []
                if row['template_variables']:
                    try:
                        variables = json.loads(row['template_variables'])
                    except json.JSONDecodeError:
                        pass
                
                templates.append({
                    'id': row['id'],
                    'text': row['prompt_text'],
                    'variables': variables,
                    'creation_date': row['creation_date'],
                    'favorite': bool(row['favorite'])
                })
            
            return templates
            
        except sqlite3.Error as e:
            logger.error(f"Error getting template history: {str(e)}")
            raise DatabaseError("Failed to get template history") from e
    
    def add_template_variable(self, name: str, values: List[str]) -> int:
        """Add a new template variable.
        
        Args:
            name: Variable name
            values: Possible values for the variable
            
        Returns:
            int: The ID of the variable
        """
        try:
            self.ensure_connection()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            values_json = json.dumps(values)
            
            # Check if variable already exists
            self.cursor.execute(
                "SELECT id FROM template_variables WHERE name = ?", 
                (name,)
            )
            result = self.cursor.fetchone()
            
            if result:
                # Update existing variable
                variable_id = result[0]
                self.cursor.execute(
                    """
                    UPDATE template_variables 
                    SET value_list = ?, last_used = ?, usage_count = usage_count + 1 
                    WHERE id = ?
                    """, 
                    (values_json, current_time, variable_id)
                )
            else:
                # Insert new variable
                self.cursor.execute(
                    """
                    INSERT INTO template_variables 
                    (name, value_list, creation_date, last_used, usage_count) 
                    VALUES (?, ?, ?, ?, ?)
                    """, 
                    (name, values_json, current_time, current_time, 1)
                )
                variable_id = self.cursor.lastrowid
                
            self.connection.commit()
            return variable_id
            
        except sqlite3.Error as e:
            error_msg = f"Error adding template variable: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def get_template_variables(self) -> List[TemplateVariable]:
        """Get all template variables.
        
        Returns:
            List[TemplateVariable]: List of template variables
        """
        try:
            self.ensure_connection()
            self.cursor.execute(
                """
                SELECT id, name, value_list, creation_date, last_used, usage_count 
                FROM template_variables
                ORDER BY usage_count DESC
                """
            )
            rows = self.cursor.fetchall()
            
            variables = []
            for row in rows:
                variable = TemplateVariable(
                    id=row[0],
                    name=row[1],
                    values=json.loads(row[2]),
                    creation_date=row[3],
                    last_used=row[4],
                    usage_count=row[5]
                )
                variables.append(variable)
                
            return variables
            
        except sqlite3.Error as e:
            error_msg = f"Error getting template variables: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def delete_template_variable(self, variable_id: int) -> bool:
        """Delete a template variable.
        
        Args:
            variable_id: ID of the variable to delete
            
        Returns:
            bool: True if successful
        """
        try:
            # Get variable name for logging
            self.cursor.execute("SELECT name FROM template_variables WHERE id = ?", (variable_id,))
            variable = self.cursor.fetchone()
            
            if not variable:
                logger.warning(f"Attempted to delete non-existent template variable with ID {variable_id}")
                return False
            
            # Delete the variable
            self.cursor.execute("DELETE FROM template_variables WHERE id = ?", (variable_id,))
            
            # Commit the changes
            self.connection.commit()
            
            logger.info(f"Deleted template variable '{variable['name']}' (ID: {variable_id})")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting template variable: {str(e)}")
            self.connection.rollback()
            raise DatabaseError("Failed to delete template variable") from e

    def get_usage_stats(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get usage statistics for the specified number of days.
        
        Args:
            days: Optional number of days to retrieve (None for all)
            
        Returns:
            List of usage statistics
        """
        try:
            self.ensure_connection()
            
            # First try with the new table name
            try:
                if days:
                    # Get stats for the last N days
                    query = """
                    SELECT date, total_tokens, total_cost, generations_count 
                    FROM usage_statistics 
                    WHERE date >= date('now', ?) 
                    ORDER BY date
                    """
                    self.cursor.execute(query, (f'-{days} days',))
                else:
                    # Get all stats
                    query = """
                    SELECT date, total_tokens, total_cost, generations_count 
                    FROM usage_statistics 
                    ORDER BY date
                    """
                    self.cursor.execute(query)
                
                # Fetch results
                results = []
                
                for row in self.cursor.fetchall():
                    results.append({
                        'date': row[0],
                        'total_tokens': row[1],
                        'total_cost': row[2],
                        'generations_count': row[3]
                    })
                
                return results
            
            except sqlite3.OperationalError as e:
                # If the new table doesn't exist, try the old table name
                if "no such table: usage_statistics" in str(e):
                    logger.warning("usage_statistics table not found, trying usage_stats")
                    
                    if days:
                        # Get stats for the last N days
                        query = """
                        SELECT date, total_tokens, total_cost, generations_count 
                        FROM usage_stats 
                        WHERE date >= date('now', ?) 
                        ORDER BY date
                        """
                        self.cursor.execute(query, (f'-{days} days',))
                    else:
                        # Get all stats
                        query = """
                        SELECT date, total_tokens, total_cost, generations_count 
                        FROM usage_stats 
                        ORDER BY date
                        """
                        self.cursor.execute(query)
                    
                    # Fetch results
                    results = []
                    
                    for row in self.cursor.fetchall():
                        results.append({
                            'date': row[0],
                            'total_tokens': row[1],
                            'total_cost': row[2],
                            'generations_count': row[3]
                        })
                    
                    return results
                else:
                    # If it's a different error, re-raise it
                    raise
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get usage stats: {str(e)}")
            raise DatabaseError(f"Failed to get usage statistics: {str(e)}")
        finally:
            # Don't close the connection here as it might be needed later
            pass
    
    def get_model_distribution(self) -> List[Tuple[str, int]]:
        """
        Get distribution of models used in generations.
        
        Returns:
            List[Tuple[str, int]]: List of (model_name, count) tuples, sorted by count descending
        """
        try:
            self.ensure_connection()
            
            # SQLite doesn't have json_extract by default in older versions
            # Use a different approach to extract model from JSON
            self.cursor.execute(
                """
                SELECT parameters, COUNT(*) as count
                FROM generation_history
                GROUP BY parameters
                ORDER BY count DESC
                """
            )
            
            model_counts = {}
            
            for row in self.cursor.fetchall():
                parameters = json.loads(row[0])
                model = parameters.get('model', 'unknown')
                count = row[1]
                
                if model in model_counts:
                    model_counts[model] += count
                else:
                    model_counts[model] = count
            
            # Convert to list of tuples and sort by count
            distribution = [(model, count) for model, count in model_counts.items()]
            distribution.sort(key=lambda x: x[1], reverse=True)
            
            return distribution
            
        except sqlite3.Error as e:
            error_msg = f"Error getting model distribution: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def get_size_distribution(self) -> Dict[str, int]:
        """Get distribution of generations by image size.
        
        Returns:
            Dictionary mapping image sizes to generation counts
        """
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            
            # Get all generations with parameters
            query = "SELECT parameters FROM generation_history"
            cursor.execute(query)
            
            # Process results manually
            result = {}
            for row in cursor.fetchall():
                try:
                    params = json.loads(row[0])
                    size = params.get('size')
                    if size:
                        result[size] = result.get(size, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Sort by count (descending)
            result = dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
            return result
            
        except Exception as e:
            logger.error(f"Failed to get size distribution: {str(e)}")
            raise DatabaseError("Failed to get size distribution", {"error": str(e)})
        finally:
            self.close()

    def save_template_variable(self, name: str, values: List[str]) -> int:
        """Save a template variable to the database.
        
        Args:
            name: The name of the template variable
            values: List of possible values for the variable
            
        Returns:
            int: The ID of the saved template variable
        """
        try:
            self.ensure_connection()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            values_json = json.dumps(values)
            
            # Check if variable already exists
            self.cursor.execute(
                "SELECT id FROM template_variables WHERE name = ?", 
                (name,)
            )
            result = self.cursor.fetchone()
            
            if result:
                # Update existing variable
                variable_id = result[0]
                self.cursor.execute(
                    """
                    UPDATE template_variables 
                    SET value_list = ?, last_used = ?, usage_count = usage_count + 1 
                    WHERE id = ?
                    """, 
                    (values_json, current_time, variable_id)
                )
            else:
                # Insert new variable
                self.cursor.execute(
                    """
                    INSERT INTO template_variables 
                    (name, value_list, creation_date, last_used, usage_count) 
                    VALUES (?, ?, ?, ?, ?)
                    """, 
                    (name, values_json, current_time, current_time, 1)
                )
                variable_id = self.cursor.lastrowid
                
            self.connection.commit()
            return variable_id
            
        except sqlite3.Error as e:
            error_msg = f"Error saving template variable: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def save_generation(
        self,
        prompt_id: int,
        image_path: str,
        parameters: Dict[str, Any],
        token_usage: int,
        cost: float,
        user_rating: int = 0,
        description: Optional[str] = None
    ) -> int:
        """Save a generation record to the database.

        Args:
            prompt_id: ID of the prompt used
            image_path: Path to the generated image
            parameters: Generation parameters (model, size, etc.)
            token_usage: Number of tokens used
            cost: Cost of the generation
            user_rating: User rating (0-5)
            description: Optional description

        Returns:
            int: ID of the saved generation
        """
        try:
            # Ensure connection is open
            self.ensure_connection()
            current_time = datetime.now().isoformat()

            # Insert generation record
            self.cursor.execute(
                """
                INSERT INTO generation_history
                (prompt_id, image_path, parameters, token_usage, cost, creation_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    prompt_id,
                    image_path,
                    json.dumps(parameters),
                    token_usage,
                    cost,
                    current_time
                )
            )
            generation_id = self.cursor.lastrowid

            # Update usage stats
            self.update_usage_stats(token_usage, cost)

            self.connection.commit()
            logger.info(f"Saved generation record (ID: {generation_id})")
            return generation_id

        except sqlite3.Error as e:
            error_msg = f"Error saving generation: {str(e)}"
            logger.error(error_msg)
            self.connection.rollback()
            raise DatabaseError(error_msg)

    def get_generation_history(self, limit: int = 100) -> List[Dict]:
        """
        Get generation history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: List of generation records
        """
        try:
            self.ensure_connection()
            # Use creation_date from DB but map it to generation_date in the result
            self.cursor.execute(
                """
                    SELECT 
                    g.id, g.prompt_id, g.image_path, g.parameters, 
                    g.token_usage, g.cost, g.creation_date,
                    p.prompt_text
                FROM generation_history g
                JOIN prompt_history p ON g.prompt_id = p.id
                ORDER BY g.creation_date DESC
                    LIMIT ?
                """,
                (limit,)
            )
            
            rows = self.cursor.fetchall()
            generations = []
            
            for row in rows:
                generation = {
                    'id': row[0],
                    'prompt_id': row[1],
                    'image_path': row[2],
                    'parameters': json.loads(row[3]),
                    'token_usage': row[4],
                    'cost': row[5],
                    'generation_date': row[6],  # Map creation_date from DB to generation_date for the model
                    'prompt_text': row[7]
                }
                generations.append(generation)
                
            return generations
            
        except sqlite3.Error as e:
            error_msg = f"Error getting generation history: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_total_usage(self) -> Dict[str, Any]:
        """Get total usage statistics.
        
        Returns:
            Dictionary with total tokens, cost, days, and generations
        """
        try:
            self.ensure_connection()
            
            # Try with the new table name first
            try:
                query = """
                    SELECT SUM(total_tokens) as total_tokens, 
                           SUM(total_cost) as total_cost,
                           COUNT(*) as total_days,
                           (SELECT COUNT(*) FROM generation_history) as total_generations
                    FROM usage_statistics
                """
                self.cursor.execute(query)
                result = self.cursor.fetchone()
                
                if result:
                    return {
                        "total_tokens": result[0] or 0,
                        "total_cost": result[1] or 0,
                        "total_days": result[2] or 0,
                        "total_generations": result[3] or 0
                    }
                
            except sqlite3.OperationalError as e:
                # If the new table doesn't exist, try the old table name
                if "no such table: usage_statistics" in str(e):
                    logger.warning("usage_statistics table not found, trying usage_stats")
                    
                    query = """
                        SELECT SUM(total_tokens) as total_tokens, 
                               SUM(total_cost) as total_cost,
                               COUNT(*) as total_days,
                               (SELECT COUNT(*) FROM generation_history) as total_generations
                        FROM usage_stats
                    """
                    self.cursor.execute(query)
                    result = self.cursor.fetchone()
                    
                    if result:
                        return {
                            "total_tokens": result[0] or 0,
                            "total_cost": result[1] or 0,
                            "total_days": result[2] or 0,
                            "total_generations": result[3] or 0
                        }
                else:
                    # If it's a different error, re-raise it
                    raise
            
            # If we get here, either both tables don't exist or they're empty
            return {
                "total_tokens": 0,
                "total_cost": 0,
                "total_days": 0,
                "total_generations": 0
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error getting total usage: {str(e)}")
            return {
                "total_tokens": 0,
                "total_cost": 0,
                "total_days": 0,
                "total_generations": 0
            } 
