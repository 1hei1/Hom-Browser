from typing import Optional, List, TypeVar, Generic
from pydantic import BaseModel
from datetime import datetime

# Base Pydantic models for common fields
class ProfileBase(BaseModel):
    name: str
    group_id: Optional[int] = None
    notes: Optional[str] = None
    os_platform: Optional[str] = None
    os_version: Optional[str] = None
    browser_version: Optional[str] = None
    proxy_config_type: Optional[str] = 'default'
    custom_proxy_id: Optional[int] = None
    cookies: Optional[str] = None
    startup_homepage: Optional[str] = None
    user_agent: Optional[str] = None
    sec_ch_ua: Optional[str] = None
    webgl_image_mode: Optional[str] = 'default'
    webgl_vendor: Optional[str] = None
    webgl_renderer: Optional[str] = None
    audiocontext_mode: Optional[str] = 'default'
    clientrects_mode: Optional[str] = 'default'
    speech_voices_mode: Optional[str] = 'default'
    cpu_cores: Optional[int] = None
    memory_gb: Optional[int] = None
    device_name: Optional[str] = None
    mac_address: Optional[str] = None
    do_not_track: Optional[bool] = False
    ssl_cipher_suites_mode: Optional[str] = 'default'
    port_scan_protection: Optional[bool] = True
    hardware_acceleration: Optional[bool] = True
    scan_port_whitelist: Optional[str] = None
    custom_launch_parameters: Optional[str] = None
    fingerprint_seed: Optional[int] = None
    language: Optional[str] = None
    accept_language: Optional[str] = None
    timezone: Optional[str] = None

class ProfileCreate(ProfileBase):
    name: str # Name is required for creation

class ProfileUpdate(BaseModel): # Inherit directly from BaseModel for full optionality
    name: Optional[str] = None
    group_id: Optional[int] = None
    notes: Optional[str] = None
    os_platform: Optional[str] = None
    os_version: Optional[str] = None
    browser_version: Optional[str] = None
    proxy_config_type: Optional[str] = None
    custom_proxy_id: Optional[int] = None
    cookies: Optional[str] = None
    startup_homepage: Optional[str] = None
    user_agent: Optional[str] = None
    sec_ch_ua: Optional[str] = None
    webgl_image_mode: Optional[str] = None
    webgl_vendor: Optional[str] = None
    webgl_renderer: Optional[str] = None
    audiocontext_mode: Optional[str] = None
    clientrects_mode: Optional[str] = None
    speech_voices_mode: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[int] = None
    device_name: Optional[str] = None
    mac_address: Optional[str] = None
    do_not_track: Optional[bool] = None
    ssl_cipher_suites_mode: Optional[str] = None
    port_scan_protection: Optional[bool] = None
    hardware_acceleration: Optional[bool] = None
    scan_port_whitelist: Optional[str] = None
    custom_launch_parameters: Optional[str] = None
    fingerprint_seed: Optional[int] = None
    language: Optional[str] = None
    accept_language: Optional[str] = None
    timezone: Optional[str] = None

class Profile(ProfileBase): # Profile inherits from ProfileBase, so name is required
    id: int
    created_at: datetime
    last_launch_time: Optional[datetime] = None
    proxy_config_type: str # Not optional for response
    webgl_image_mode: str # Not optional for response
    audiocontext_mode: str # Not optional for response
    clientrects_mode: str # Not optional for response
    speech_voices_mode: str # Not optional for response
    do_not_track: bool # Not optional for response
    ssl_cipher_suites_mode: str # Not optional for response
    port_scan_protection: bool # Not optional for response
    hardware_acceleration: bool # Not optional for response


    class Config:
        orm_mode = True

class ProfileSimple(BaseModel): # For lists, maybe less detail
    id: int
    name: str
    group_id: Optional[int] = None
    last_launch_time: Optional[datetime] = None

    class Config:
        orm_mode = True

class ProfileLaunchResponse(BaseModel):
    message: str
    profile_id: int
    command: Optional[str] = None # For debugging/logging, maybe not for production

# Schemas for Group
class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    name: Optional[str] = None # Allow name to be optional for partial updates

class Group(GroupBase):
    id: int
    created_at: datetime
    profile_count: Optional[int] = None # Added for API response

    class Config:
        orm_mode = True

# Schemas for Proxy
class ProxyBase(BaseModel):
    name: Optional[str] = None
    type: str # 'HTTP', 'SOCKS5'
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None

class ProxyCreate(ProxyBase):
    type: str # Required for creation
    host: str # Required for creation
    port: int # Required for creation

class ProxyUpdate(BaseModel): # Inherit directly from BaseModel for full optionality
    name: Optional[str] = None
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None

class Proxy(ProxyBase): # Proxy inherits from ProxyBase, so type, host, port are required
    id: int
    created_at: datetime
    usage_count: Optional[int] = None # Added for API response

    class Config:
        orm_mode = True


class BatchDeletePayload(BaseModel):
    ids: List[int]

class BatchDeleteErrorDetail(BaseModel):
    id: int
    error: str

class BatchDeleteResponse(BaseModel):
    message: str
    deleted_count: int
    errors: List[BatchDeleteErrorDetail]

# Generic response for lists with pagination
DataT = TypeVar('DataT')

class PaginatedResponse(BaseModel, Generic[DataT]):
    items: List[DataT]
    total: int
    page: int
    page_size: int
    pages: int


# Schemas for Plugin
class PluginBase(BaseModel):
    name: str
    version: Optional[str] = None
    source_path: Optional[str] = None # Path to .crx or similar
    enabled: bool = True

class PluginCreate(PluginBase):
    pass

class PluginUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    source_path: Optional[str] = None
    enabled: Optional[bool] = None

class Plugin(PluginBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
