"""Database manager for the DALL-E Image Generator application."""

import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

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
        
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
        logger.info(f"Database initialized at {self.db_path.absolute()}")
    
    def connect(self):
        """Connect to SQLite database."""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info("Connected to database")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
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
            
            # Batch Generations table
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
            
            # Generation History table
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
            
            # Usage Stats table
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
            
            self.conn.commit()
            return prompt_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding prompt: {str(e)}")
            self.conn.rollback()
            raise
    
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
                (prompt_id, batch_id, image_path, generation_date, parameters,
                 token_usage, cost, user_rating, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    generation_dict['prompt_id'],
                    generation_dict['batch_id'],
                    generation_dict['image_path'],
                    generation_dict['generation_date'],
                    json.dumps(generation_dict['parameters']),
                    generation_dict['token_usage'],
                    generation_dict['cost'],
                    generation_dict['user_rating'],
                    generation_dict['description']
                )
            )
            
            generation_id = self.cursor.lastrowid
            self.conn.commit()
            
            # Update usage stats
            self.update_usage_stats(
                generation_dict['token_usage'],
                generation_dict['cost']
            )
            
            logger.info(f"Added new generation (ID: {generation_id})")
            return generation_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding generation: {str(e)}")
            self.conn.rollback()
            raise
    
    def update_usage_stats(self, tokens: int, cost: float):
        """Update daily usage statistics.
        
        Args:
            tokens: Number of tokens used
            cost: Cost of the generation
        """
        try:
            today = datetime.now().date().isoformat()
            
            # Try to update existing stats for today
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
            
            # If no row was updated, insert new stats
            if self.cursor.rowcount == 0:
                self.cursor.execute(
                    """
                    INSERT INTO usage_stats 
                    (date, total_tokens, total_cost, generations_count)
                    VALUES (?, ?, ?, 1)
                    """,
                    (today, tokens, cost)
                )
            
            self.conn.commit()
            logger.info(f"Updated usage stats for {today}")
            
        except sqlite3.Error as e:
            logger.error(f"Error updating usage stats: {str(e)}")
            self.conn.rollback()
            raise

    def get_generation_count(self) -> int:
        """Get total number of generations.
        
        Returns:
            int: Total number of generations
        """
        try:
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
            query = """
                SELECT gh.*, ph.prompt_text
                FROM generation_history gh
                LEFT JOIN prompt_history ph ON gh.prompt_id = ph.id
            """
            params = []
            
            if search:
                query += " WHERE ph.prompt_text LIKE ? OR gh.description LIKE ?"
                params.extend([f"%{search}%", f"%{search}%"])
            
            query += " ORDER BY gh.generation_date DESC LIMIT ? OFFSET ?"
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
            self.cursor.execute(
                """
                SELECT gh.*, ph.prompt_text
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
            self.conn.commit()
            logger.info(f"Updated rating for generation {generation_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Error updating generation rating: {str(e)}")
            self.conn.rollback()
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
                self.conn.commit()
                logger.info(f"Deleted generation {generation_id}")
                
                # Return image path for cleanup
                return row["image_path"]
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting generation: {str(e)}")
            self.conn.rollback()
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
            self.conn.commit()
            
            logger.info(f"Added template with ID: {template_id}")
            return template_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding template: {str(e)}")
            self.conn.rollback()
            raise DatabaseError("Failed to add template") from e
            
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
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Updated template {template_id}")
                return True
            else:
                logger.warning(f"No template found with ID {template_id}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            self.conn.rollback()
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
            
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Deleted template with ID: {template_id}")
                return True
            else:
                logger.warning(f"No template found with ID {template_id}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting template: {str(e)}")
            self.conn.rollback()
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
            now = datetime.now().isoformat()
            values_json = json.dumps(values)
            
            # Check if variable already exists
            self.cursor.execute("SELECT id FROM template_variables WHERE name = ?", (name,))
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing variable
                self.cursor.execute(
                    """
                    UPDATE template_variables SET value_list = ?, last_used = ? WHERE id = ?
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
                    (name, value_list, creation_date, last_used) 
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
            raise DatabaseError("Failed to add template variable") from e
    
    def get_template_variables(self) -> List[Dict[str, Any]]:
        """Get all template variables from the database.
        
        Returns:
            List[Dict[str, Any]]: List of template variable dictionaries
        """
        try:
            self.cursor.execute("SELECT * FROM template_variables ORDER BY name")
            results = self.cursor.fetchall()
            
            variables = []
            for row in results:
                # Convert JSON string to Python object
                values = json.loads(row['value_list']) if row['value_list'] else []
                
                variables.append({
                    'id': row['id'],
                    'name': row['name'],
                    'values': values,
                    'creation_date': row['creation_date'],
                    'last_used': row['last_used'],
                    'usage_count': row['usage_count']
                })
            
            return variables
            
        except sqlite3.Error as e:
            logger.error(f"Error getting template variables: {str(e)}")
            raise DatabaseError("Failed to get template variables") from e
    
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
            self.conn.commit()
            
            logger.info(f"Deleted template variable '{variable['name']}' (ID: {variable_id})")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting template variable: {str(e)}")
            self.conn.rollback()
            raise DatabaseError("Failed to delete template variable") from e 
