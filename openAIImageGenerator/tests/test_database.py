import os
import logging
import sys
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def test_database():
    """Test the database implementation."""
    logger.info("Starting database test...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Test prompt operations
    logger.info("Testing prompt operations...")
    
    # Add a prompt
    prompt_text = "A beautiful sunset over the ocean with palm trees"
    prompt_id = db_manager.add_prompt(prompt_text, tags=["sunset", "ocean", "nature"])
    logger.info(f"Added prompt with ID: {prompt_id}")
    
    # Add a template prompt
    template_text = "A {animal} in a {environment} with {weather} weather"
    template_vars = ["animal", "environment", "weather"]
    template_id = db_manager.add_prompt(
        template_text, 
        is_template=True, 
        template_variables=template_vars,
        tags=["template", "animal"]
    )
    logger.info(f"Added template prompt with ID: {template_id}")
    
    # Get prompt history
    prompts = db_manager.get_prompt_history(limit=10)
    logger.info(f"Retrieved {len(prompts)} prompts from history")
    for prompt in prompts:
        prompt_obj = Prompt.from_dict(prompt)
        logger.info(f"  - {prompt_obj}")
    
    # Test template variable operations
    logger.info("Testing template variable operations...")
    
    # Add template variables
    animal_id = db_manager.add_template_variable("animal", ["cat", "dog", "elephant", "tiger", "lion"])
    environment_id = db_manager.add_template_variable("environment", ["forest", "desert", "jungle", "mountains", "ocean"])
    weather_id = db_manager.add_template_variable("weather", ["sunny", "rainy", "cloudy", "snowy", "stormy"])
    
    logger.info(f"Added template variables with IDs: {animal_id}, {environment_id}, {weather_id}")
    
    # Get template variables
    variables = db_manager.get_template_variables()
    logger.info(f"Retrieved {len(variables)} template variables")
    for var in variables:
        var_obj = TemplateVariable.from_dict(var)
        logger.info(f"  - {var_obj}")
    
    # Test batch generation operations
    logger.info("Testing batch generation operations...")
    
    # Create a batch
    combinations = [
        {"animal": "cat", "environment": "forest", "weather": "sunny"},
        {"animal": "dog", "environment": "beach", "weather": "cloudy"},
        {"animal": "elephant", "environment": "jungle", "weather": "rainy"}
    ]
    
    batch_id = db_manager.create_batch(template_id, total_images=3, variable_combinations=combinations)
    logger.info(f"Created batch with ID: {batch_id}")
    
    # Update batch status
    db_manager.update_batch_status(batch_id, "in_progress")
    logger.info("Updated batch status to 'in_progress'")
    
    # Test generation operations
    logger.info("Testing generation operations...")
    
    # Add generations
    for i in range(3):
        # Simulate image path
        image_path = f"outputs/2025-02-26/test_image_{i+1}.png"
        
        # Simulate parameters
        parameters = {
            "size": "1024x1024",
            "model": "dall-e-3",
            "quality": "standard",
            "style": "vivid"
        }
        
        # Add generation
        generation_id = db_manager.add_generation(
            prompt_id=prompt_id if i == 0 else template_id,
            batch_id=batch_id if i > 0 else None,
            image_path=image_path,
            parameters=parameters,
            token_usage=100 + i * 10,
            cost=0.002 + i * 0.0005,
            description=f"Test generation {i+1}"
        )
        
        logger.info(f"Added generation with ID: {generation_id}")
    
    # Complete the batch
    db_manager.update_batch_status(batch_id, "completed")
    logger.info("Updated batch status to 'completed'")
    
    # Get generation history
    generations = db_manager.get_generation_history(limit=10)
    logger.info(f"Retrieved {len(generations)} generations from history")
    for gen in generations:
        gen_obj = Generation.from_dict(gen)
        logger.info(f"  - {gen_obj}")
    
    # Test usage stats operations
    logger.info("Testing usage stats operations...")
    
    # Get usage stats
    stats = db_manager.get_usage_stats()
    logger.info(f"Retrieved {len(stats)} usage stat records")
    for stat in stats:
        stat_obj = UsageStat.from_dict(stat)
        logger.info(f"  - {stat_obj}")
    
    # Get total usage
    total = db_manager.get_total_usage()
    logger.info(f"Total usage: {total['total_tokens']} tokens, ${total['total_cost']:.4f}, {total['total_generations']} generations")
    
    # Close database connection
    db_manager.close()
    logger.info("Database test completed successfully!")

if __name__ == "__main__":
    test_database() 
