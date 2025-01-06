from typing import Any
from pydantic import BaseModel, Field, field_validator

class PickingRequest(BaseModel):
    product_list: dict[str, int] = Field(
        ..., 
        description='Dictionary of SKU:quantity pairs'
    )
    
    config: dict[str, Any] = Field(
        default_factory=dict,
        description='Additional configuration parameters for the optimize method'
    )

    @field_validator('product_list')
    def validate_quantities(cls, v):
        if not all(isinstance(qty, int) and qty > 0 for qty in v.values()):
            raise ValueError('All quantities must be positive integers')
        return v

class LatestOrderConfig(BaseModel):
    config: dict[str, Any] = Field(
        default_factory=dict,
        description='Additional configuration parameters for the optimize method'
    )