"""Módulo de estatísticas do banco de dados PostgreSQL.

Este módulo fornece uma interface para consultar estatísticas e métricas do sistema,
incluindo totais de relés, funções de proteção, parâmetros, além de agregações por
fabricante, tipo de relé e classe de tensão.

Exemplo:
    >>> from src.python.utils.database_stats import DatabaseStats
    >>> db_stats = DatabaseStats()
    >>> total = db_stats.get_total_relays()
    >>> print(f"Total de relés: {total}")

Atributos:
    db_config (dict): Configuração de conexão com PostgreSQL
    schema (str): Nome do schema no banco de dados
"""

import psycopg2
from typing import Dict, List, Any, Optional
from datetime import datetime


class DatabaseStats:
    """Cliente para consulta de estatísticas do banco de dados de relés.
    
    Esta classe encapsula todas as operações de consulta de métricas e estatísticas
    do sistema de relés de proteção, fornecendo métodos para obter totais, resumos
    agregados e status geral do banco de dados.
    
    Attributes:
        db_config (dict): Dicionário com parâmetros de conexão PostgreSQL
        schema (str): Nome do schema onde residem as tabelas do sistema
    """
    
    def __init__(
        self,
        db_host: str = 'localhost',
        db_port: int = 5432,
        db_name: str = 'protecai_db',
        db_user: str = 'protecai',
        db_password: str = 'protecai',
        db_schema: str = 'protec_ai'
    ) -> None:
        """Inicializa o cliente de estatísticas do banco de dados.
        
        Args:
            db_host: Endereço do servidor PostgreSQL (padrão: 'localhost')
            db_port: Porta do servidor PostgreSQL (padrão: 5432)
            db_name: Nome do banco de dados (padrão: 'protecai_db')
            db_user: Usuário para autenticação (padrão: 'protecai')
            db_password: Senha para autenticação (padrão: 'protecai')
            db_schema: Schema do banco de dados (padrão: 'protec_ai')
        """
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        self.schema = db_schema
    
    def get_connection(self) -> psycopg2.extensions.connection:
        """Estabelece conexão com o banco de dados PostgreSQL.
        
        Returns:
            Objeto de conexão psycopg2 ativo.
            
        Raises:
            psycopg2.OperationalError: Se não conseguir conectar ao banco.
        """
        return psycopg2.connect(**self.db_config)
    
    def get_total_relays(self) -> int:
        """Retorna o número total de relés cadastrados no sistema.
        
        Returns:
            Quantidade total de registros na tabela de relés.
            
        Raises:
            psycopg2.Error: Em caso de erro na consulta ao banco.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {self.schema}.relays")
                return cur.fetchone()[0]
    
    def get_total_protections(self) -> int:
        """Retorna o número total de funções de proteção cadastradas.
        
        Returns:
            Quantidade total de registros na tabela de funções de proteção.
            
        Raises:
            psycopg2.Error: Em caso de erro na consulta ao banco.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {self.schema}.protection_functions")
                return cur.fetchone()[0]
    
    def get_total_parameters(self) -> int:
        """Retorna o número total de parâmetros configurados no sistema.
        
        Returns:
            Quantidade total de registros na tabela de parâmetros.
            
        Raises:
            psycopg2.Error: Em caso de erro na consulta ao banco.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {self.schema}.parameters")
                return cur.fetchone()[0]
    
    def get_manufacturers_summary(self) -> List[Dict[str, Any]]:
        """Retorna resumo agregado por fabricante de relés.
        
        Consulta o banco e retorna estatísticas agrupadas por fabricante,
        incluindo total de relés e modelos diferentes cadastrados.
        
        Returns:
            Lista de dicionários contendo:
                - name (str): Nome do fabricante
                - total_relays (int): Total de relés do fabricante
                - total_models (int): Total de modelos diferentes
            
        Raises:
            psycopg2.Error: Em caso de erro na consulta ao banco.
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
        """Retorna resumo agregado por tipo de relé.
        
        Consulta o banco e retorna estatísticas agrupadas por tipo de aplicação
        do relé (Motor, Overcurrent, Voltage, etc.).
        
        Returns:
            Lista de dicionários contendo:
                - type (str): Tipo do relé
                - count (int): Quantidade deste tipo
            
        Raises:
            psycopg2.Error: Em caso de erro na consulta ao banco.
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
        """Retorna resumo agregado por classe de tensão.
        
        Consulta o banco e retorna estatísticas agrupadas por classe de tensão
        em kV dos relés cadastrados.
        
        Returns:
            Lista de dicionários contendo:
                - voltage_class (float): Classe de tensão em kV
                - count (int): Quantidade de relés nesta classe
            
        Raises:
            psycopg2.Error: Em caso de erro na consulta ao banco.
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
        """Retorna status completo do banco de dados com todas as estatísticas.
        
        Consolida todas as métricas disponíveis em um único dicionário,
        incluindo totais e resumos agregados.
        
        Returns:
            Dicionário contendo:
                - total_relays (int): Total de relés
                - total_protections (int): Total de funções de proteção
                - total_parameters (int): Total de parâmetros
                - manufacturers (List[Dict]): Resumo por fabricante
                - relay_types (List[Dict]): Resumo por tipo
                - voltage_classes (List[Dict]): Resumo por tensão
                - timestamp (str): Data/hora da consulta
            
        Raises:
            psycopg2.Error: Em caso de erro nas consultas ao banco.
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
        """Verifica se a conexão com o banco de dados está disponível.
        
        Tenta executar uma query simples para validar conectividade e
        disponibilidade do servidor PostgreSQL.
        
        Returns:
            True se conexão estabelecida com sucesso, False caso contrário.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception:
            return False
