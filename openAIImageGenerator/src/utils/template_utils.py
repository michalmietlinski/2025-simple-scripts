"""Template processing utilities."""

import re
import logging
import random
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class TemplateProcessor:
    """Handles template processing and variable substitution."""
    
    def __init__(self, db_manager: Any = None):
        """Initialize template processor.
        
        Args:
            db_manager: Optional database manager for variable lookup
        """
        self.db_manager = db_manager
        self.variable_pattern = r'\{\{([^{}]+)\}\}'
        logger.debug("Template processor initialized")
    
    def extract_variables(self, template_text: str) -> List[str]:
        """Extract variable names from template text.
        
        Args:
            template_text: Template text
            
        Returns:
            List of variable names
        """
        # Find all occurrences of {{variable_name}}
        matches = re.findall(self.variable_pattern, template_text)
        
        # Return unique variable names
        return list(set(matches))
    
    def validate_template(self, template_text: str) -> Tuple[bool, str]:
        """Validate template syntax.
        
        Args:
            template_text: Template text
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check for balanced braces
            open_count = template_text.count("{{")
            close_count = template_text.count("}}")
            
            if open_count != close_count:
                return False, f"Unbalanced braces: {open_count} opening vs {close_count} closing"
            
            # Check for empty variables
            if re.search(r'\{\{\s*\}\}', template_text):
                return False, "Empty variable names are not allowed"
            
            # Check for nested variables
            if re.search(r'\{\{[^}]*\{\{', template_text):
                return False, "Nested variables are not allowed"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Template validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def substitute_variables(
        self,
        template_text: str,
        variable_values: Dict[str, str] = None,
        use_random: bool = False
    ) -> str:
        """Substitute variables in template text.
        
        Args:
            template_text: Template text
            variable_values: Dictionary of variable values
            use_random: Whether to use random values from database
            
        Returns:
            Processed text with variables substituted
        """
        try:
            # Extract variables
            variables = self.extract_variables(template_text)
            
            if not variables:
                return template_text
            
            # Initialize result with template text
            result = template_text
            variable_values = variable_values or {}
            
            # Process each variable
            for var_name in variables:
                # Get variable value
                value = None
                
                # Check provided values first
                if var_name in variable_values:
                    value = variable_values[var_name]
                
                # If not provided and random is enabled, try database
                elif use_random and self.db_manager:
                    value = self._get_random_value(var_name)
                
                # If still no value, use placeholder
                if value is None:
                    value = f"[{var_name}]"
                
                # Replace in template
                result = result.replace(f"{{{{{var_name}}}}}", value)
            
            return result
            
        except Exception as e:
            logger.error(f"Variable substitution error: {str(e)}")
            return template_text
    
    def _get_random_value(self, variable_name: str) -> Optional[str]:
        """Get random value for variable from database.
        
        Args:
            variable_name: Variable name
            
        Returns:
            Random value or None if not found
        """
        try:
            if not self.db_manager:
                return None
            
            # Get all variables
            variables = self.db_manager.get_template_variables()
            
            # Find matching variable
            for var in variables:
                if var["name"] == variable_name and var["values"]:
                    # Return random value
                    return random.choice(var["values"])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get random value: {str(e)}")
            return None
    
    def create_variable_combinations(
        self,
        variables: List[str],
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Create combinations of variable values for batch processing.
        
        Args:
            variables: List of variable names
            limit: Maximum number of combinations
            
        Returns:
            List of variable value dictionaries
        """
        try:
            if not variables or not self.db_manager:
                return []
            
            # Get all variables from database
            all_variables = self.db_manager.get_template_variables()
            
            # Filter to requested variables and collect values
            var_values = {}
            for var_name in variables:
                for var in all_variables:
                    if var["name"] == var_name and var["values"]:
                        var_values[var_name] = var["values"]
                        break
                
                # If variable not found, use placeholder
                if var_name not in var_values:
                    var_values[var_name] = [f"[{var_name}]"]
            
            # Generate combinations
            combinations = self._generate_combinations(var_values, limit)
            
            return combinations
            
        except Exception as e:
            logger.error(f"Failed to create variable combinations: {str(e)}")
            return []
    
    def _generate_combinations(
        self,
        var_values: Dict[str, List[str]],
        limit: int
    ) -> List[Dict[str, str]]:
        """Generate combinations of variable values.
        
        Args:
            var_values: Dictionary of variable names to possible values
            limit: Maximum number of combinations
            
        Returns:
            List of variable value dictionaries
        """
        # Handle empty case
        if not var_values:
            return []
        
        # Start with first variable
        var_names = list(var_values.keys())
        result = [{var_names[0]: value} for value in var_values[var_names[0]]]
        
        # Add each variable
        for i in range(1, len(var_names)):
            var_name = var_names[i]
            values = var_values[var_name]
            
            # Create new combinations
            new_result = []
            for combo in result:
                for value in values:
                    # Create new combination with this value
                    new_combo = combo.copy()
                    new_combo[var_name] = value
                    new_result.append(new_combo)
                    
                    # Check limit
                    if len(new_result) >= limit:
                        break
                
                # Check limit
                if len(new_result) >= limit:
                    break
            
            result = new_result[:limit]
        
        return result 
