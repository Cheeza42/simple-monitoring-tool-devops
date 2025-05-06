# Imports from pydantic provide core functionality for data validation models,
# including base model definition, IP address validation, and custom field validators.
from pydantic import BaseModel, IPvAnyAddress, field_validator

# Import from typing to restrict field values to specific literal options (like enums)
from typing import Literal

# VMInstance defines the structure and validation rules for a virtual machine instance
class VMInstance(BaseModel):
    # Name of the VM (must be a non-empty string)
    name: str

    # IP address of the VM (must be a valid IPv4 or IPv6 address)
    ip: IPvAnyAddress

    # Operating system description (must be a non-empty string)
    os: str

    # Machine status (must be either "UP" or "DOWN")
    status: Literal["UP", "DOWN"]

    # Validator to ensure the 'name' field is not empty or just whitespace
    @field_validator("name")
    def name_cannot_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v

    # Validator to ensure the 'os' field is not empty or just whitespace
    @field_validator("os")
    def os_cannot_be_empty(cls, v):
        if not v.strip():
            raise ValueError("OS cannot be empty")
        return v
