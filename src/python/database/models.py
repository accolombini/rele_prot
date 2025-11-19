"""
SQLAlchemy Models for ProtecAI Database
3NF Normalized Structure
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean, 
    Date, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Manufacturer(Base):
    __tablename__ = 'manufacturers'
    __table_args__ = {'schema': 'protec_ai'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    country = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    relay_models = relationship("RelayModel", back_populates="manufacturer")


class RelayModel(Base):
    __tablename__ = 'relay_models'
    __table_args__ = (
        UniqueConstraint('manufacturer_id', 'model_name', name='uq_manufacturer_model'),
        {'schema': 'protec_ai'}
    )
    
    id = Column(Integer, primary_key=True)
    manufacturer_id = Column(Integer, ForeignKey('protec_ai.manufacturers.id'), nullable=False)
    model_name = Column(String(50), nullable=False)
    model_series = Column(String(50))
    software_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    manufacturer = relationship("Manufacturer", back_populates="relay_models")
    relays = relationship("Relay", back_populates="relay_model")


class Substation(Base):
    __tablename__ = 'substations'
    __table_args__ = {'schema': 'protec_ai'}
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True)
    name = Column(String(200))
    voltage_level_kv = Column(Numeric(10, 2))
    location = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    relays = relationship("Relay", back_populates="substation")


class Relay(Base):
    __tablename__ = 'relays'
    __table_args__ = {'schema': 'protec_ai'}
    
    id = Column(Integer, primary_key=True)
    relay_model_id = Column(Integer, ForeignKey('protec_ai.relay_models.id'), nullable=False)
    substation_id = Column(Integer, ForeignKey('protec_ai.substations.id'))
    serial_number = Column(String(100))
    plant_reference = Column(String(100))
    model_number = Column(String(100))
    bay_identifier = Column(String(50))
    element_identifier = Column(String(50))
    parametrization_date = Column(Date)
    frequency_hz = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    relay_model = relationship("RelayModel", back_populates="relays")
    substation = relationship("Substation", back_populates="relays")
    current_transformers = relationship("CurrentTransformer", back_populates="relay", cascade="all, delete-orphan")
    voltage_transformers = relationship("VoltageTransformer", back_populates="relay", cascade="all, delete-orphan")
    protection_functions = relationship("ProtectionFunction", back_populates="relay", cascade="all, delete-orphan")


class CurrentTransformer(Base):
    __tablename__ = 'current_transformers'
    __table_args__ = {'schema': 'protec_ai'}
    
    id = Column(Integer, primary_key=True)
    relay_id = Column(Integer, ForeignKey('protec_ai.relays.id'), nullable=False)
    tc_type = Column(String(50), nullable=False)  # 'Phase', 'Ground', 'Residual', 'SEF'
    primary_rating_a = Column(Numeric(10, 2), nullable=False)
    secondary_rating_a = Column(Numeric(10, 2), nullable=False)
    ratio = Column(String(50))
    burden = Column(String(50))
    accuracy_class = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    relay = relationship("Relay", back_populates="current_transformers")


class VoltageTransformer(Base):
    __tablename__ = 'voltage_transformers'
    __table_args__ = {'schema': 'protec_ai'}
    
    id = Column(Integer, primary_key=True)
    relay_id = Column(Integer, ForeignKey('protec_ai.relays.id'), nullable=False)
    vt_type = Column(String(50), nullable=False)  # 'Main', 'Auxiliary', 'Ground'
    primary_rating_v = Column(Numeric(10, 2), nullable=False)
    secondary_rating_v = Column(Numeric(10, 2), nullable=False)
    ratio = Column(String(50))
    connection_type = Column(String(50))
    location = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    relay = relationship("Relay", back_populates="voltage_transformers")


class AnsiFunction(Base):
    __tablename__ = 'ansi_functions'
    __table_args__ = {'schema': 'protec_ai'}
    
    id = Column(Integer, primary_key=True)
    ansi_code = Column(String(10), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    protection_functions = relationship("ProtectionFunction", back_populates="ansi_function")


class ProtectionFunction(Base):
    __tablename__ = 'protection_functions'
    __table_args__ = (
        UniqueConstraint('relay_id', 'ansi_function_id', 'function_label', 'setting_group', 
                        name='uq_relay_ansi_label_group'),
        {'schema': 'protec_ai'}
    )
    
    id = Column(Integer, primary_key=True)
    relay_id = Column(Integer, ForeignKey('protec_ai.relays.id'), nullable=False)
    ansi_function_id = Column(Integer, ForeignKey('protec_ai.ansi_functions.id'), nullable=False)
    function_label = Column(String(100))
    is_enabled = Column(Boolean, nullable=False, default=False)
    setting_group = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    relay = relationship("Relay", back_populates="protection_functions")
    ansi_function = relationship("AnsiFunction", back_populates="protection_functions")
    parameters = relationship("Parameter", back_populates="protection_function", cascade="all, delete-orphan")


class Parameter(Base):
    __tablename__ = 'parameters'
    __table_args__ = {'schema': 'protec_ai'}
    
    id = Column(Integer, primary_key=True)
    protection_function_id = Column(Integer, ForeignKey('protec_ai.protection_functions.id'), nullable=False)
    parameter_code = Column(String(50), nullable=False)
    parameter_name = Column(String(200), nullable=False)
    parameter_value = Column(Text, nullable=False)
    parameter_unit = Column(String(50))
    parameter_type = Column(String(50))  # 'setpoint', 'delay', 'curve', 'logic', 'mode'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    protection_function = relationship("ProtectionFunction", back_populates="parameters")


class ProcessingLog(Base):
    __tablename__ = 'processing_log'
    __table_args__ = {'schema': 'protec_ai'}
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(20), nullable=False)  # 'PDF', 'S40'
    file_hash = Column(String(64), nullable=False, unique=True)
    manufacturer = Column(String(100))
    relay_model = Column(String(50))
    status = Column(String(50), nullable=False)  # 'SUCCESS', 'ERROR', 'DUPLICATE', 'SKIPPED'
    error_message = Column(Text)
    records_inserted = Column(Integer, default=0)
    processed_at = Column(DateTime, default=datetime.utcnow)
