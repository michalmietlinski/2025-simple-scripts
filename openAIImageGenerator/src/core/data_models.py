"""Data models for the DALL-E Image Generator application."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
import json

@dataclass
class Prompt:
    """Model for prompt history entries."""
    id: Optional[int] = None
    prompt_text: str = ""
    creation_date: str = ""
    last_used: str = ""
    favorite: bool = False
    tags: List[str] = None
    usage_count: int = 1
    average_rating: float = 0.0
    is_template: bool = False
    template_variables: List[str] = None

    def __post_init__(self):
        """Initialize default values."""
        self.tags = self.tags or []
        self.template_variables = self.template_variables or []
        if not self.creation_date:
            self.creation_date = datetime.now().isoformat()
        if not self.last_used:
            self.last_used = datetime.now().isoformat()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prompt':
        """Create from dictionary."""
        template_vars = data.get('template_variables')
        if isinstance(template_vars, str):
            template_vars = json.loads(template_vars)

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class TemplateVariable:
    """Model for template variables."""
    id: Optional[int] = None
    name: str = ""
    values: List[str] = None
    creation_date: str = ""
    last_used: str = ""
    usage_count: int = 1

    def __post_init__(self):
        """Initialize default values."""
        self.values = self.values or []
        if not self.creation_date:
            self.creation_date = datetime.now().isoformat()
        if not self.last_used:
            self.last_used = datetime.now().isoformat()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateVariable':
        """Create from dictionary."""
        values = data.get('values')
        if isinstance(values, str):
            values = json.loads(values)

        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            values=values,
            creation_date=data.get('creation_date'),
            last_used=data.get('last_used'),
            usage_count=data.get('usage_count', 1)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class BatchGeneration:
    """Model for batch generation jobs."""
    id: Optional[int] = None
    template_prompt_id: Optional[int] = None
    start_time: str = ""
    end_time: Optional[str] = None
    total_images: int = 0
    completed_images: int = 0
    status: str = "pending"
    variable_combinations: List[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values."""
        self.variable_combinations = self.variable_combinations or []
        if not self.start_time:
            self.start_time = datetime.now().isoformat()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchGeneration':
        """Create from dictionary."""
        combinations = data.get('variable_combinations')
        if isinstance(combinations, str):
            combinations = json.loads(combinations)

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class Generation:
    """Model for individual image generations."""
    id: Optional[int] = None
    prompt_id: Optional[int] = None
    batch_id: Optional[int] = None
    image_path: str = ""
    generation_date: str = ""
    parameters: Dict[str, Any] = None
    token_usage: int = 0
    cost: float = 0.0
    user_rating: int = 0
    description: Optional[str] = None
    prompt_text: Optional[str] = None

    def __post_init__(self):
        """Initialize default values."""
        self.parameters = self.parameters or {}
        if not self.generation_date:
            self.generation_date = datetime.now().isoformat()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Generation':
        """Create from dictionary."""
        parameters = data.get('parameters')
        if isinstance(parameters, str):
            parameters = json.loads(parameters)

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class UsageStat:
    """Model for daily usage statistics."""
    id: Optional[int] = None
    date: str = ""
    total_tokens: int = 0
    total_cost: float = 0.0
    generations_count: int = 0

    def __post_init__(self):
        """Initialize default values."""
        if not self.date:
            self.date = datetime.now().date().isoformat()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageStat':
        """Create from dictionary."""
        return cls(
            id=data.get('id'),
            date=data.get('date'),
            total_tokens=data.get('total_tokens', 0),
            total_cost=data.get('total_cost', 0.0),
            generations_count=data.get('generations_count', 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self) 
