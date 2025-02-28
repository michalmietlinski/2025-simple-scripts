"""Usage tracking utilities for the OpenAI Image Generator."""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
import json

from ..core.database import DatabaseManager

logger = logging.getLogger(__name__)

class UsageTracker:
    """Tracks API usage, costs, and generation statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the usage tracker.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        logger.info("Usage tracker initialized")
    
    def record_usage(self, tokens: int, model: str, size: str, cost: Optional[float] = None):
        """Record API usage for an image generation.
        
        Args:
            tokens: Number of tokens used
            model: Model used (e.g., "dall-e-3")
            size: Image size (e.g., "1024x1024")
            cost: Optional cost override (calculated if not provided)
        """
        # Calculate cost if not provided
        if cost is None:
            cost = self._calculate_cost(tokens, model, size)
        
        # Update usage stats in database
        self.db_manager.update_usage_stats(tokens, cost)
        
        logger.info(f"Recorded usage: {tokens} tokens, ${cost:.4f} for {model} at {size}")
    
    def _calculate_cost(self, tokens: int, model: str, size: str) -> float:
        """Calculate the cost of generation based on model and size.
        
        Args:
            tokens: Number of tokens used
            model: Model used
            size: Image size
            
        Returns:
            Estimated cost in USD
        """
        # Base rates (as of 2024)
        rates = {
            "dall-e-3": {
                "1024x1024": 0.040,  # $0.040 per image
                "1792x1024": 0.080,  # $0.080 per image
                "1024x1792": 0.080,  # $0.080 per image
            },
            "dall-e-2": {
                "1024x1024": 0.020,  # $0.020 per image
                "512x512": 0.018,    # $0.018 per image
                "256x256": 0.016,    # $0.016 per image
            }
        }
        
        # Get base rate for model and size
        model_rates = rates.get(model.lower(), rates.get("dall-e-3", {}))
        base_rate = model_rates.get(size, 0.040)  # Default to DALL-E 3 1024x1024 rate
        
        # For token-based models, add token cost
        token_cost = tokens * 0.00002  # $0.02 per 1000 tokens
        
        return base_rate + token_cost
    
    def get_daily_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily usage statistics for the last N days.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of daily usage statistics
        """
        # Get usage stats from database
        stats = self.db_manager.get_usage_stats(days)
        
        # Format for display
        formatted_stats = []
        for stat in stats:
            formatted_stats.append({
                "date": stat["date"],
                "images": stat["generations_count"],
                "tokens": stat["total_tokens"],
                "cost": f"${stat['total_cost']:.2f}"
            })
        
        return formatted_stats
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of usage statistics.
        
        Returns:
            Dictionary with usage summary
        """
        # Get all-time stats
        stats = self.db_manager.get_usage_stats()
        
        # Calculate totals
        total_images = sum(stat["generations_count"] for stat in stats)
        total_tokens = sum(stat["total_tokens"] for stat in stats)
        total_cost = sum(stat["total_cost"] for stat in stats)
        
        # Calculate monthly average (if we have data)
        months = len(set(stat["date"][:7] for stat in stats))  # Count unique year-month combinations
        monthly_avg_cost = total_cost / max(1, months)
        
        return {
            "total_images": total_images,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "monthly_avg_cost": monthly_avg_cost,
            "first_date": stats[0]["date"] if stats else None,
            "last_date": stats[-1]["date"] if stats else None
        }
    
    def get_model_distribution(self) -> Dict[str, int]:
        """Get distribution of models used in generations.
        
        Returns:
            Dictionary mapping model names to generation counts
        """
        # Get the list of tuples from the database
        model_tuples = self.db_manager.get_model_distribution()
        
        # Convert to dictionary
        return dict(model_tuples)
    
    def get_size_distribution(self) -> Dict[str, int]:
        """Get distribution of generations by image size.
        
        Returns:
            Dictionary mapping image sizes to generation counts
        """
        return self.db_manager.get_size_distribution() 
