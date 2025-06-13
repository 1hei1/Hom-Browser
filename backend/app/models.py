from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base # Changed

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profiles = relationship("Profile", back_populates="group")

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True) # Made name nullable as per schema
    type = Column(String, nullable=False) # 'HTTP', 'SOCKS5'
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profiles = relationship("Profile", back_populates="custom_proxy")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_launch_time = Column(DateTime(timezone=True), nullable=True)

    # Basic Settings
    os_platform = Column(String, nullable=True) # 'windows', 'linux', 'macos'
    os_version = Column(String, nullable=True)
    browser_version = Column(String, nullable=True)
    proxy_config_type = Column(String, default='default') # 'default', 'none', 'custom'
    custom_proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=True)
    cookies = Column(Text, nullable=True)

    # Advanced Settings (Fingerprint Configuration)
    startup_homepage = Column(Text, nullable=True)

    user_agent_mode = Column(String, default='default') # 'default', 'custom', 'random' (random might be via seed)
    user_agent_custom = Column(Text, nullable=True) # Actual UA string if mode is 'custom'. Old 'user_agent' field.

    sec_ch_ua_mode = Column(String, default='default') # 'default', 'custom', 'random'
    sec_ch_ua_custom = Column(Text, nullable=True) # Actual Sec-CH-UA string if mode is 'custom'. Old 'sec_ch_ua' field.

    webgl_image_mode = Column(String, default='default') # 'default', 'custom', 'random'
    # webgl_image_custom_hash = Column(String, nullable=True) # If 'custom' for image hash - Add if explicitly needed

    webgl_metadata_mode = Column(String, default='default') # 'default', 'custom', 'random'
    webgl_vendor = Column(String, nullable=True) # Effective if webgl_metadata_mode is 'custom'
    webgl_renderer = Column(String, nullable=True) # Effective if webgl_metadata_mode is 'custom'

    audiocontext_mode = Column(String, default='default') # 'default', 'noise', 'off'
    clientrects_mode = Column(String, default='default') # 'default', 'noise', 'off'
    speech_voices_mode = Column(String, default='default') # 'default', 'custom'
    speech_voices_custom_data = Column(Text, nullable=True) # For custom speech voices config, JSON or similar
    cpu_cores = Column(Integer, nullable=True)
    memory_gb = Column(Integer, nullable=True)
    device_name = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)

    # Switches
    do_not_track = Column(Boolean, default=False)
    ssl_cipher_suites_mode = Column(String, default='default') # 'default', 'strict', 'custom'
    ssl_custom_suites_data = Column(Text, nullable=True) # For custom SSL cipher suites list
    port_scan_protection = Column(Boolean, default=True)
    hardware_acceleration = Column(Boolean, default=True)
    scan_port_whitelist = Column(Text, nullable=True) # Comma-separated ports

    # Misc
    custom_launch_parameters = Column(Text, nullable=True)
    fingerprint_seed = Column(Integer, nullable=True)

    # Language and Timezone for command generator
    language = Column(String, nullable=True) # e.g., en-US
    accept_language = Column(String, nullable=True) # e.g., en-US,en;q=0.9
    timezone = Column(String, nullable=True) # e.g., America/Los_Angeles

    group = relationship("Group", back_populates="profiles")
    custom_proxy = relationship("Proxy", back_populates="profiles")


class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=True)
    source_path = Column(Text, nullable=True) # Path to .crx file or identifier from a store
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # If plugins can be associated with profiles, a relationship would be needed here.
    # For now, keeping it simple as per initial DDL which didn't show direct profile links.
