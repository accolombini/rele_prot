"""
Database Repository - Data Access Layer
Handles all database operations with transaction management
"""

import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from .models import (
    Base, Manufacturer, RelayModel, Substation, Relay,
    CurrentTransformer, VoltageTransformer, AnsiFunction,
    ProtectionFunction, Parameter, ProcessingLog
)


class DatabaseRepository:
    """Repository pattern for database operations"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize database connection"""
        if connection_string is None:
            # Load from environment or default
            db_host = os.getenv('POSTGRES_HOST', 'localhost')
            db_port = os.getenv('POSTGRES_PORT', '5432')
            db_name = os.getenv('POSTGRES_DB', 'protecai_db')
            db_user = os.getenv('POSTGRES_USER', 'protecai')
            db_password = os.getenv('POSTGRES_PASSWORD', 'protecai_2025')
            
            connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        self.engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
    
    # ==================== MANUFACTURER OPERATIONS ====================
    
    def get_or_create_manufacturer(self, name: str, country: Optional[str] = None) -> Manufacturer:
        """Get existing manufacturer or create new one"""
        with self.get_session() as session:
            manufacturer = session.query(Manufacturer).filter_by(name=name).first()
            if not manufacturer:
                manufacturer = Manufacturer(name=name, country=country)
                session.add(manufacturer)
                session.flush()
            return manufacturer
    
    # ==================== RELAY MODEL OPERATIONS ====================
    
    def get_or_create_relay_model(
        self, 
        manufacturer_id: int,
        model_name: str,
        model_series: Optional[str] = None,
        software_version: Optional[str] = None
    ) -> RelayModel:
        """Get existing relay model or create new one"""
        with self.get_session() as session:
            relay_model = session.query(RelayModel).filter_by(
                manufacturer_id=manufacturer_id,
                model_name=model_name
            ).first()
            
            if not relay_model:
                relay_model = RelayModel(
                    manufacturer_id=manufacturer_id,
                    model_name=model_name,
                    model_series=model_series,
                    software_version=software_version
                )
                session.add(relay_model)
                session.flush()
            
            return relay_model
    
    # ==================== SUBSTATION OPERATIONS ====================
    
    def get_or_create_substation(
        self,
        code: str,
        name: Optional[str] = None,
        voltage_level_kv: Optional[float] = None,
        location: Optional[str] = None
    ) -> Substation:
        """Get existing substation or create new one"""
        with self.get_session() as session:
            substation = session.query(Substation).filter_by(code=code).first()
            if not substation:
                substation = Substation(
                    code=code,
                    name=name,
                    voltage_level_kv=voltage_level_kv,
                    location=location
                )
                session.add(substation)
                session.flush()
            return substation
    
    # ==================== ANSI FUNCTION OPERATIONS ====================
    
    def get_ansi_function_by_code(self, ansi_code: str) -> Optional[AnsiFunction]:
        """Get ANSI function by code"""
        with self.get_session() as session:
            return session.query(AnsiFunction).filter_by(ansi_code=ansi_code).first()
    
    # ==================== RELAY OPERATIONS ====================
    
    def create_relay(self, relay_data: Dict[str, Any]) -> Relay:
        """Create a new relay record"""
        with self.get_session() as session:
            relay = Relay(**relay_data)
            session.add(relay)
            session.flush()
            return relay
    
    def get_relay_by_serial(self, serial_number: str) -> Optional[Relay]:
        """Get relay by serial number"""
        with self.get_session() as session:
            return session.query(Relay).filter_by(serial_number=serial_number).first()
    
    # ==================== CT/VT OPERATIONS ====================
    
    def add_current_transformer(self, relay_id: int, ct_data: Dict[str, Any]):
        """Add CT to relay"""
        with self.get_session() as session:
            ct = CurrentTransformer(relay_id=relay_id, **ct_data)
            session.add(ct)
    
    def add_voltage_transformer(self, relay_id: int, vt_data: Dict[str, Any]):
        """Add VT to relay"""
        with self.get_session() as session:
            vt = VoltageTransformer(relay_id=relay_id, **vt_data)
            session.add(vt)
    
    # ==================== PROTECTION FUNCTION OPERATIONS ====================
    
    def add_protection_function(
        self,
        relay_id: int,
        ansi_function_id: int,
        function_data: Dict[str, Any]
    ) -> ProtectionFunction:
        """Add protection function to relay"""
        with self.get_session() as session:
            prot_func = ProtectionFunction(
                relay_id=relay_id,
                ansi_function_id=ansi_function_id,
                **function_data
            )
            session.add(prot_func)
            session.flush()
            return prot_func
    
    def add_parameter(self, protection_function_id: int, param_data: Dict[str, Any]):
        """Add parameter to protection function"""
        with self.get_session() as session:
            parameter = Parameter(
                protection_function_id=protection_function_id,
                **param_data
            )
            session.add(parameter)
    
    # ==================== PROCESSING LOG OPERATIONS ====================
    
    def check_file_processed(self, file_hash: str) -> bool:
        """Check if file was already processed"""
        with self.get_session() as session:
            return session.query(ProcessingLog).filter_by(file_hash=file_hash).first() is not None
    
    def log_processing(self, log_data: Dict[str, Any]):
        """Log file processing"""
        with self.get_session() as session:
            log_entry = ProcessingLog(**log_data)
            session.add(log_entry)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        with self.get_session() as session:
            total = session.query(ProcessingLog).count()
            success = session.query(ProcessingLog).filter_by(status='SUCCESS').count()
            errors = session.query(ProcessingLog).filter_by(status='ERROR').count()
            duplicates = session.query(ProcessingLog).filter_by(status='DUPLICATE').count()
            
            return {
                'total': total,
                'success': success,
                'errors': errors,
                'duplicates': duplicates
            }
