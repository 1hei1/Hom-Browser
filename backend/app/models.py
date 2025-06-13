from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base # Adjusted import path

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
    user_agent = Column(Text, nullable=True)
    sec_ch_ua = Column(Text, nullable=True)
    webgl_image_mode = Column(String, default='default')
    webgl_vendor = Column(String, nullable=True)
    webgl_renderer = Column(String, nullable=True)
    audiocontext_mode = Column(String, default='default')
    clientrects_mode = Column(String, default='default')
    speech_voices_mode = Column(String, default='default')
    cpu_cores = Column(Integer, nullable=True)
    memory_gb = Column(Integer, nullable=True)
    device_name = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)

    # Switches
    do_not_track = Column(Boolean, default=False)
    ssl_cipher_suites_mode = Column(String, default='default')
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
