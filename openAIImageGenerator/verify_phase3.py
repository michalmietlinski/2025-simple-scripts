#!/usr/bin/env python
import os
import sys
import logging
import sqlite3
from datetime import datetime, timedelta
from utils.database_manager import DatabaseManager
from utils.data_models import Prompt, Generation, TemplateVariable, BatchGeneration, UsageStat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_database_structure():
    """Verify the database structure matches the expected schema."""
    logger.info("Verifying database structure...")
    
    # Get database path
    db_manager = DatabaseManager()
    db_path = db_manager.db_path
    db_manager.close()
    
    # Connect directly to check schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Expected tables
    expected_tables = [
        'prompt_history', 
        'template_variables', 
        'batch_generations', 
        'generation_history', 
        'usage_stats'
    ]
    
    # Check if all expected tables exist
    missing_tables = [table for table in expected_tables if table not in tables]
    if missing_tables:
        logger.error(f"Missing tables: {missing_tables}")
        return False
    
    # Check table schemas
    table_schemas = {}
    for table in expected_tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        table_schemas[table] = [col[1] for col in columns]  # col[1] is the column name
    
    # Expected columns for each table
    expected_schemas = {
        'prompt_history': ['id', 'prompt_text', 'creation_date', 'last_used', 'favorite', 
                          'tags', 'usage_count', 'average_rating', 'is_template', 'template_variables'],
        'template_variables': ['id', 'name', 'value_list', 'creation_date', 'last_used', 'usage_count'],
        'batch_generations': ['id', 'template_prompt_id', 'start_time', 'end_time', 'total_images', 
                             'completed_images', 'status', 'variable_combinations'],
        'generation_history': ['id', 'prompt_id', 'batch_id', 'image_path', 'generation_date', 
                              'parameters', 'token_usage', 'cost', 'user_rating', 'description'],
        'usage_stats': ['id', 'date', 'total_tokens', 'total_cost', 'generations_count']
    }
    
    # Check if all expected columns exist
    schema_errors = []
    for table, expected_columns in expected_schemas.items():
        if table not in table_schemas:
            continue
            
        actual_columns = table_schemas[table]
        missing_columns = [col for col in expected_columns if col not in actual_columns]
        
        if missing_columns:
            schema_errors.append(f"Table '{table}' missing columns: {missing_columns}")
    
    if schema_errors:
        for error in schema_errors:
            logger.error(error)
        return False
    
    logger.info("Database structure verification passed!")
    return True

def verify_data_models():
    """Verify the data models work correctly."""
    logger.info("Verifying data models...")
    
    # Test Prompt model
    prompt = Prompt(
        id=1,
        prompt_text="Test prompt",
        creation_date=datetime.now().isoformat(),
        favorite=True,
        tags=["test", "verification"],
        is_template=False
    )
    
    prompt_dict = prompt.to_dict()
    prompt2 = Prompt.from_dict(prompt_dict)
    
    if prompt.prompt_text != prompt2.prompt_text or prompt.favorite != prompt2.favorite:
        logger.error("Prompt model serialization/deserialization failed")
        return False
    
    # Test Generation model
    generation = Generation(
        id=1,
        prompt_id=1,
        image_path="test/path.png",
        generation_date=datetime.now().isoformat(),
        parameters={"size": "1024x1024", "model": "dall-e-3"},
        token_usage=100,
        cost=0.002
    )
    
    gen_dict = generation.to_dict()
    generation2 = Generation.from_dict(gen_dict)
    
    if generation.image_path != generation2.image_path or generation.token_usage != generation2.token_usage:
        logger.error("Generation model serialization/deserialization failed")
        return False
    
    # Test TemplateVariable model
    template_var = TemplateVariable(
        id=1,
        name="color",
        values=["red", "green", "blue"],
        creation_date=datetime.now().isoformat()
    )
    
    var_dict = template_var.to_dict()
    template_var2 = TemplateVariable.from_dict(var_dict)
    
    if template_var.name != template_var2.name or template_var.values != template_var2.values:
        logger.error("TemplateVariable model serialization/deserialization failed")
        return False
    
    logger.info("Data models verification passed!")
    return True

def verify_database_operations():
    """Verify basic database operations work correctly."""
    logger.info("Verifying database operations...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        # Test adding a prompt
        prompt_text = "Verification test prompt"
        prompt_id = db_manager.add_prompt(prompt_text, tags=["test", "verification"])
        logger.info(f"Added test prompt with ID: {prompt_id}")
        
        # Test retrieving the prompt
        prompts = db_manager.get_prompt_history(limit=1, prompt_id=prompt_id)
        if not prompts or prompts[0]['prompt_text'] != prompt_text:
            logger.error("Failed to retrieve added prompt")
            return False
        
        # Test updating the prompt
        success = db_manager.update_prompt(prompt_id, favorite=True)
        if not success:
            logger.error("Failed to update prompt")
            return False
        
        # Verify the update
        prompts = db_manager.get_prompt_history(limit=1, prompt_id=prompt_id)
        if not prompts or not prompts[0]['favorite']:
            logger.error("Prompt update verification failed")
            return False
        
        # Test adding a generation
        image_path = "test/verification_image.png"
        parameters = {"size": "1024x1024", "model": "dall-e-3", "quality": "standard"}
        generation_id = db_manager.add_generation(
            prompt_id=prompt_id,
            image_path=image_path,
            parameters=parameters,
            token_usage=50,
            cost=0.001,
            description="Verification test"
        )
        logger.info(f"Added test generation with ID: {generation_id}")
        
        # Test retrieving the generation
        generations = db_manager.get_generation_history(limit=1, generation_id=generation_id)
        if not generations or generations[0]['image_path'] != image_path:
            logger.error("Failed to retrieve added generation")
            return False
        
        # Test usage stats
        stats = db_manager.get_usage_stats()
        if not stats:
            logger.error("Failed to retrieve usage stats")
            return False
        
        # Test total usage
        total = db_manager.get_total_usage()
        if 'total_tokens' not in total or 'total_cost' not in total:
            logger.error("Failed to retrieve total usage")
            return False
        
        logger.info("Database operations verification passed!")
        return True
    
    except Exception as e:
        logger.error(f"Database operations verification failed: {str(e)}")
        return False
    finally:
        db_manager.close()

def run_verification():
    """Run all verification tests."""
    logger.info("Starting Phase 3 verification...")
    
    # Verify database structure
    structure_ok = verify_database_structure()
    
    # Verify data models
    models_ok = verify_data_models()
    
    # Verify database operations
    operations_ok = verify_database_operations()
    
    # Overall result
    if structure_ok and models_ok and operations_ok:
        logger.info("✅ Phase 3 verification PASSED!")
        return True
    else:
        logger.error("❌ Phase 3 verification FAILED!")
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1) 
