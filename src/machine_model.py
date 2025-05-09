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

    # Operating system description (can contain a version but must start with a known OS name)
    os: str

    # Machine status (must be either "UP" or "DOWN")
    status: Literal["UP", "DOWN"]

    # Validator to ensure the 'name' field is not empty or just whitespace
    @field_validator("name")
    @classmethod
    def name_cannot_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v

    # Validator to ensure the 'os' field starts with a known operating system name
    @field_validator("os")
    @classmethod
    def os_must_be_valid(cls, v):
        if not isinstance(v, str):
            raise ValueError("Operating system must be a string.")

        allowed_os = {"linux", "windows", "ubuntu", "centos", "debian", "redhat", "macos", "arch", "fedora", "ios"}
        cleaned = v.strip().lower()

        # Check if the input starts with any of the allowed OS names
        if not any(cleaned == os_name or cleaned.startswith(os_name + ' ') for os_name in allowed_os):
            raise ValueError(f"Invalid operating system. Please choose from: {', '.join(sorted(allowed_os))}")

        return v

    # Validator to ensure the 'status' field is valid
    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v):
        if v not in {"UP", "DOWN"}:
            raise ValueError("Status must be either 'UP' or 'DOWN'")
        return v
