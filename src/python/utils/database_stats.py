"""
Módulo para consultar estatísticas do banco de dados PostgreSQL.
Fornece informações sobre relés, proteções, parâmetros, fabricantes, etc.
"""

import psycopg2
from typing import Dict, List, Any
from datetime import datetime


class DatabaseStats:
    """Classe para obter estatísticas do banco de dados"""
    
    def __init__(
        self,
        db_host: str = 'localhost',
        db_port: int = 5432,
        db_name: str = 'protecai_db',
        db_user: str = 'protecai',
        db_password: str = 'protecai',
        db_schema: str = 'protec_ai'
    ):
        """
        Inicializa conexão com banco de dados
        
        Args:
            db_host: Host do PostgreSQL
            db_port: Porta do PostgreSQL
            db_name: Nome do banco de dados
            db_user: Usuário do banco
            db_password: Senha do usuário
            db_schema: Schema do banco
        """
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        self.schema = db_schema
    
    def get_connection(self):
        """Cria e retorna conexão com banco de dados"""
        return psycopg2.connect(**self.db_config)
    
    def get_total_relays(self) -> int:
        """Retorna total de relés no banco"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {self.schema}.relays")
                return cur.fetchone()[0]
    
    def get_total_protections(self) -> int:
        """Retorna total de funções de proteção"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {self.schema}.protection_functions")
                return cur.fetchone()[0]
    
    def get_total_parameters(self) -> int:
        """Retorna total de parâmetros"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {self.schema}.parameters")
                return cur.fetchone()[0]
    
    def get_manufacturers_summary(self) -> List[Dict[str, Any]]:
        """
        Retorna resumo por fabricante
        
        Returns:
            Lista de dicts com {name, total_relays, models}
        """
        query = f"""
        SELECT 
            m.name as manufacturer,
            COUNT(DISTINCT r.id) as total_relays,
            COUNT(DISTINCT rm.id) as total_models
        FROM {self.schema}.manufacturers m
        LEFT JOIN {self.schema}.relay_models rm ON m.id = rm.manufacturer_id
        LEFT JOIN {self.schema}.relays r ON rm.id = r.relay_model_id
        GROUP BY m.name
        ORDER BY total_relays DESC
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                results = []
                for row in cur.fetchall():
                    results.append({
                        'name': row[0],
                        'total_relays': row[1],
                        'total_models': row[2]
                    })
                return results
    
    def get_relay_types_summary(self) -> List[Dict[str, Any]]:
        """
        Retorna resumo por tipo de relé
        
        Returns:
            Lista de dicts com {type, count}
        """
        query = f"""
        SELECT 
            relay_type,
            COUNT(*) as total
        FROM {self.schema}.relays
        WHERE relay_type IS NOT NULL
        GROUP BY relay_type
        ORDER BY total DESC
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                results = []
                for row in cur.fetchall():
                    results.append({
                        'type': row[0],
                        'count': row[1]
                    })
                return results
    
    def get_voltage_classes_summary(self) -> List[Dict[str, Any]]:
        """
        Retorna resumo por classe de tensão
        
        Returns:
            Lista de dicts com {voltage_class, count}
        """
        query = f"""
        SELECT 
            voltage_class_kv,
            COUNT(*) as total
        FROM {self.schema}.relays
        WHERE voltage_class_kv IS NOT NULL
        GROUP BY voltage_class_kv
        ORDER BY voltage_class_kv
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                results = []
                for row in cur.fetchall():
                    results.append({
                        'voltage_class': row[0],
                        'count': row[1]
                    })
                return results
    
    def get_database_status(self) -> Dict[str, Any]:
        """
        Retorna status geral do banco de dados
        
        Returns:
            Dict com estatísticas completas
        """
        return {
            'total_relays': self.get_total_relays(),
            'total_protections': self.get_total_protections(),
            'total_parameters': self.get_total_parameters(),
            'manufacturers': self.get_manufacturers_summary(),
            'relay_types': self.get_relay_types_summary(),
            'voltage_classes': self.get_voltage_classes_summary(),
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
    
    def check_connection(self) -> bool:
        """
        Verifica se conexão com banco está ativa
        
        Returns:
            True se conectado, False caso contrário
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception:
            return False
