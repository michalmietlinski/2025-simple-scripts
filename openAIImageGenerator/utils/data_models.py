import json
from datetime import datetime

class Prompt:
    """Model class for prompt history entries."""
    
    def __init__(self, id=None, prompt_text="", creation_date=None, last_used=None, 
                 favorite=False, tags=None, usage_count=1, average_rating=0.0, 
                 is_template=False, template_variables=None):
        """Initialize a Prompt object.
        
        Args:
            id (int, optional): Prompt ID. Defaults to None.
            prompt_text (str, optional): The prompt text. Defaults to "".
            creation_date (str, optional): Creation date (ISO format). Defaults to current time.
            last_used (str, optional): Last used date (ISO format). Defaults to current time.
            favorite (bool, optional): Whether this is a favorite prompt. Defaults to False.
            tags (list, optional): List of tags. Defaults to None.
            usage_count (int, optional): Number of times used. Defaults to 1.
            average_rating (float, optional): Average user rating. Defaults to 0.0.
            is_template (bool, optional): Whether this is a template prompt. Defaults to False.
            template_variables (list, optional): List of template variable names. Defaults to None.
        """
        self.id = id
        self.prompt_text = prompt_text
        self.creation_date = creation_date or datetime.now().isoformat()
        self.last_used = last_used or datetime.now().isoformat()
        self.favorite = favorite
        self.tags = tags or []
        self.usage_count = usage_count
        self.average_rating = average_rating
        self.is_template = is_template
        self.template_variables = template_variables or []
    
    @classmethod
    def from_dict(cls, data):
        """Create a Prompt object from a dictionary.
        
        Args:
            data (dict): Dictionary containing prompt data
            
        Returns:
            Prompt: A new Prompt object
        """
        # Handle template_variables (convert from JSON string if needed)
        template_vars = data.get('template_variables')
        if isinstance(template_vars, str):
            try:
                template_vars = json.loads(template_vars)
            except:
                template_vars = []
        
        # Handle tags (convert from comma-separated string if needed)
        tags = data.get('tags')
        if isinstance(tags, str):
            tags = tags.split(',') if tags else []
        
        return cls(
            id=data.get('id'),
            prompt_text=data.get('prompt_text', ''),
            creation_date=data.get('creation_date'),
            last_used=data.get('last_used'),
            favorite=bool(data.get('favorite', 0)),
            tags=tags,
            usage_count=data.get('usage_count', 1),
            average_rating=data.get('average_rating', 0.0),
            is_template=bool(data.get('is_template', 0)),
            template_variables=template_vars
        )
    
    def to_dict(self):
        """Convert the Prompt object to a dictionary.
        
        Returns:
            dict: Dictionary representation of the Prompt
        """
        return {
            'id': self.id,
            'prompt_text': self.prompt_text,
            'creation_date': self.creation_date,
            'last_used': self.last_used,
            'favorite': self.favorite,
            'tags': self.tags,
            'usage_count': self.usage_count,
            'average_rating': self.average_rating,
            'is_template': self.is_template,
            'template_variables': self.template_variables
        }
    
    def __str__(self):
        """String representation of the Prompt.
        
        Returns:
            str: String representation
        """
        return f"Prompt(id={self.id}, text='{self.prompt_text[:30]}...', tags={self.tags})"


class TemplateVariable:
    """Model class for template variables."""
    
    def __init__(self, id=None, name="", values=None, creation_date=None, 
                 last_used=None, usage_count=1):
        """Initialize a TemplateVariable object.
        
        Args:
            id (int, optional): Variable ID. Defaults to None.
            name (str, optional): Variable name. Defaults to "".
            values (list, optional): List of possible values. Defaults to None.
            creation_date (str, optional): Creation date (ISO format). Defaults to current time.
            last_used (str, optional): Last used date (ISO format). Defaults to current time.
            usage_count (int, optional): Number of times used. Defaults to 1.
        """
        self.id = id
        self.name = name
        self.values = values or []
        self.creation_date = creation_date or datetime.now().isoformat()
        self.last_used = last_used or datetime.now().isoformat()
        self.usage_count = usage_count
    
    @classmethod
    def from_dict(cls, data):
        """Create a TemplateVariable object from a dictionary.
        
        Args:
            data (dict): Dictionary containing variable data
            
        Returns:
            TemplateVariable: A new TemplateVariable object
        """
        # Handle values (convert from JSON string if needed)
        values = data.get('values')
        if isinstance(values, str):
            try:
                values = json.loads(values)
            except:
                values = []
        
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            values=values,
            creation_date=data.get('creation_date'),
            last_used=data.get('last_used'),
            usage_count=data.get('usage_count', 1)
        )
    
    def to_dict(self):
        """Convert the TemplateVariable object to a dictionary.
        
        Returns:
            dict: Dictionary representation of the TemplateVariable
        """
        return {
            'id': self.id,
            'name': self.name,
            'values': self.values,
            'creation_date': self.creation_date,
            'last_used': self.last_used,
            'usage_count': self.usage_count
        }
    
    def __str__(self):
        """String representation of the TemplateVariable.
        
        Returns:
            str: String representation
        """
        return f"TemplateVariable(id={self.id}, name='{self.name}', values_count={len(self.values)})"


class BatchGeneration:
    """Model class for batch generation jobs."""
    
    def __init__(self, id=None, template_prompt_id=None, start_time=None, end_time=None,
                 total_images=0, completed_images=0, status="pending", variable_combinations=None):
        """Initialize a BatchGeneration object.
        
        Args:
            id (int, optional): Batch ID. Defaults to None.
            template_prompt_id (int, optional): Template prompt ID. Defaults to None.
            start_time (str, optional): Start time (ISO format). Defaults to current time.
            end_time (str, optional): End time (ISO format). Defaults to None.
            total_images (int, optional): Total images to generate. Defaults to 0.
            completed_images (int, optional): Completed images count. Defaults to 0.
            status (str, optional): Status ('pending', 'in_progress', 'completed', 'failed'). Defaults to "pending".
            variable_combinations (list, optional): List of variable combinations. Defaults to None.
        """
        self.id = id
        self.template_prompt_id = template_prompt_id
        self.start_time = start_time or datetime.now().isoformat()
        self.end_time = end_time
        self.total_images = total_images
        self.completed_images = completed_images
        self.status = status
        self.variable_combinations = variable_combinations or []
    
    @classmethod
    def from_dict(cls, data):
        """Create a BatchGeneration object from a dictionary.
        
        Args:
            data (dict): Dictionary containing batch data
            
        Returns:
            BatchGeneration: A new BatchGeneration object
        """
        # Handle variable_combinations (convert from JSON string if needed)
        combinations = data.get('variable_combinations')
        if isinstance(combinations, str):
            try:
                combinations = json.loads(combinations)
            except:
                combinations = []
        
        return cls(
            id=data.get('id'),
            template_prompt_id=data.get('template_prompt_id'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            total_images=data.get('total_images', 0),
            completed_images=data.get('completed_images', 0),
            status=data.get('status', 'pending'),
            variable_combinations=combinations
        )
    
    def to_dict(self):
        """Convert the BatchGeneration object to a dictionary.
        
        Returns:
            dict: Dictionary representation of the BatchGeneration
        """
        return {
            'id': self.id,
            'template_prompt_id': self.template_prompt_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_images': self.total_images,
            'completed_images': self.completed_images,
            'status': self.status,
            'variable_combinations': self.variable_combinations
        }
    
    def __str__(self):
        """String representation of the BatchGeneration.
        
        Returns:
            str: String representation
        """
        return f"BatchGeneration(id={self.id}, status='{self.status}', progress={self.completed_images}/{self.total_images})"


class Generation:
    """Model class for image generation history."""
    
    def __init__(self, id=None, prompt_id=None, batch_id=None, image_path="", 
                 generation_date=None, parameters=None, token_usage=0, cost=0.0,
                 user_rating=0, description=None, prompt_text=None):
        """Initialize a Generation object.
        
        Args:
            id (int, optional): Generation ID. Defaults to None.
            prompt_id (int, optional): Prompt ID. Defaults to None.
            batch_id (int, optional): Batch ID. Defaults to None.
            image_path (str, optional): Path to the generated image. Defaults to "".
            generation_date (str, optional): Generation date (ISO format). Defaults to current time.
            parameters (dict, optional): Generation parameters. Defaults to None.
            token_usage (int, optional): Token usage. Defaults to 0.
            cost (float, optional): Generation cost. Defaults to 0.0.
            user_rating (int, optional): User rating (0-5). Defaults to 0.
            description (str, optional): Image description. Defaults to None.
            prompt_text (str, optional): Prompt text (for convenience). Defaults to None.
        """
        self.id = id
        self.prompt_id = prompt_id
        self.batch_id = batch_id
        self.image_path = image_path
        self.generation_date = generation_date or datetime.now().isoformat()
        self.parameters = parameters or {}
        self.token_usage = token_usage
        self.cost = cost
        self.user_rating = user_rating
        self.description = description
        self.prompt_text = prompt_text
    
    @classmethod
    def from_dict(cls, data):
        """Create a Generation object from a dictionary.
        
        Args:
            data (dict): Dictionary containing generation data
            
        Returns:
            Generation: A new Generation object
        """
        # Handle parameters (convert from JSON string if needed)
        parameters = data.get('parameters')
        if isinstance(parameters, str):
            try:
                parameters = json.loads(parameters)
            except:
                parameters = {}
        
        return cls(
            id=data.get('id'),
            prompt_id=data.get('prompt_id'),
            batch_id=data.get('batch_id'),
            image_path=data.get('image_path', ''),
            generation_date=data.get('generation_date'),
            parameters=parameters,
            token_usage=data.get('token_usage', 0),
            cost=data.get('cost', 0.0),
            user_rating=data.get('user_rating', 0),
            description=data.get('description'),
            prompt_text=data.get('prompt_text')
        )
    
    def to_dict(self):
        """Convert the Generation object to a dictionary.
        
        Returns:
            dict: Dictionary representation of the Generation
        """
        return {
            'id': self.id,
            'prompt_id': self.prompt_id,
            'batch_id': self.batch_id,
            'image_path': self.image_path,
            'generation_date': self.generation_date,
            'parameters': self.parameters,
            'token_usage': self.token_usage,
            'cost': self.cost,
            'user_rating': self.user_rating,
            'description': self.description,
            'prompt_text': self.prompt_text
        }
    
    def __str__(self):
        """String representation of the Generation.
        
        Returns:
            str: String representation
        """
        return f"Generation(id={self.id}, date='{self.generation_date}', tokens={self.token_usage})"


class UsageStat:
    """Model class for usage statistics."""
    
    def __init__(self, id=None, date=None, total_tokens=0, total_cost=0.0, generations_count=0):
        """Initialize a UsageStat object.
        
        Args:
            id (int, optional): Stat ID. Defaults to None.
            date (str, optional): Date (ISO format). Defaults to current date.
            total_tokens (int, optional): Total tokens used. Defaults to 0.
            total_cost (float, optional): Total cost. Defaults to 0.0.
            generations_count (int, optional): Number of generations. Defaults to 0.
        """
        self.id = id
        self.date = date or datetime.now().date().isoformat()
        self.total_tokens = total_tokens
        self.total_cost = total_cost
        self.generations_count = generations_count
    
    @classmethod
    def from_dict(cls, data):
        """Create a UsageStat object from a dictionary.
        
        Args:
            data (dict): Dictionary containing usage data
            
        Returns:
            UsageStat: A new UsageStat object
        """
        return cls(
            id=data.get('id'),
            date=data.get('date'),
            total_tokens=data.get('total_tokens', 0),
            total_cost=data.get('total_cost', 0.0),
            generations_count=data.get('generations_count', 0)
        )
    
    def to_dict(self):
        """Convert the UsageStat object to a dictionary.
        
        Returns:
            dict: Dictionary representation of the UsageStat
        """
        return {
            'id': self.id,
            'date': self.date,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'generations_count': self.generations_count
        }
    
    def __str__(self):
        """String representation of the UsageStat.
        
        Returns:
            str: String representation
        """
        return f"UsageStat(date='{self.date}', tokens={self.total_tokens}, cost=${self.total_cost:.4f}, count={self.generations_count})" 
