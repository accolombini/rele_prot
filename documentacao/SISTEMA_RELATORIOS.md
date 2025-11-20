# Sistema de Relatórios - ProtecAI

## 📋 Visão Geral

Sistema completo de geração de relatórios em **CSV**, **Excel (XLSX)** e **PDF** com cabeçalho e rodapé padronizados Petrobras.

## 🎨 Padrão Visual

### Cabeçalho
```
■ ENGENHARIA DE PROTEÇÃO PETROBRAS
[Título do Relatório]
```

### Rodapé
```
Gerado em: DD/MM/YYYY HH:MM | [Título do Relatório] | Pag. N
```

### Cores
- **Azul Petrobras**: `#002366` (RGB: 0, 51, 102)
- **Amarelo Petrobras**: `#FFB81C` (RGB: 255, 184, 28)

## 📂 Estrutura de Saída

```
outputs/relatorios/
├── csv/
│   └── REL01_fabricantes_reles_YYYYMMDD_HHMMSS.csv
├── xlsx/
│   └── REL01_fabricantes_reles_YYYYMMDD_HHMMSS.xlsx
└── pdf/
    └── REL01_fabricantes_reles_YYYYMMDD_HHMMSS.pdf
```

## 📊 Relatórios Disponíveis

| Código | Nome | Descrição | View PostgreSQL |
|--------|------|-----------|-----------------|
| **REL01** | Fabricantes de Relés | Lista fabricantes com total de relés e modelos | `vw_manufacturers_summary` |
| **REL02** | Setpoints Críticos | Proteções principais e parâmetros críticos | `vw_critical_setpoints` |
| **REL03** | Tipos de Relés | Distribuição de relés por tipo | `vw_relay_types_summary` |
| **REL04** | Relés por Fabricante | Relés detalhados agrupados por fabricante | `vw_relays_by_manufacturer` |
| **REL05** | Funções de Proteção | Funções ANSI e seus relés | `vw_protection_functions_summary` |
| **REL06** | Relés Completo | Visão completa com estatísticas | `vw_relays_complete` |
| **REL07** | Relés por Subestação | Relés agrupados por barra/subestação | `vw_relays_by_substation` |
| **REL08** | Análise de Tensão | Classes de tensão e VTs | `vw_relays_complete` (filtrado) |
| **REL09** | Parâmetros Críticos | Consolidação de parâmetros críticos | `vw_relays_complete` (filtrado) |

## 🚀 Uso

### 1. Listar Relatórios Disponíveis

```bash
python src/python/generate_reports.py --list
```

### 2. Gerar Relatório Específico

```bash
# Gerar REL01 em todos os formatos
python src/python/generate_reports.py --report REL01

# Gerar apenas CSV e PDF
python src/python/generate_reports.py --report REL01 --format csv pdf

# Gerar apenas Excel
python src/python/generate_reports.py --report REL03 --format xlsx
```

### 3. Gerar Todos os Relatórios

```bash
# Todos os 9 relatórios em todos os formatos
python src/python/generate_reports.py --all

# Todos apenas em PDF
python src/python/generate_reports.py --all --format pdf
```

### 4. Configurar Banco de Dados

```bash
# Se o banco estiver em outro host/porta
python src/python/generate_reports.py --report REL01 \
    --db-host 192.168.1.100 \
    --db-port 5433 \
    --db-password outra_senha
```

## 🔧 Configuração Padrão

O script usa estas configurações por padrão:

```python
db_host = 'localhost'
db_port = 5432
db_name = 'protecai_db'
db_user = 'protecai'
db_password = 'protecai'
db_schema = 'protec_ai'
```

## 📝 Uso Programático

### Exemplo Básico

```python
from reporters.report_generator import ReportGenerator

# Criar gerador
generator = ReportGenerator()

# Gerar um relatório
files = generator.generate_report('REL01', formats=['csv', 'xlsx', 'pdf'])
print(files)
# {'csv': Path(...), 'xlsx': Path(...), 'pdf': Path(...)}

# Gerar todos
all_files = generator.generate_all_reports()
```

### Relatório Customizado

```python
from reporters.report_generator import ReportGenerator

generator = ReportGenerator()

# Query customizada
query = """
SELECT r.relay_id, r.serial_number, m.manufacturer_name
FROM protec_ai.relays r
JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.relay_model_id
JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.manufacturer_id
WHERE r.voltage_class_kv > 20.0
"""

# Gerar relatório
files = generator.generate_custom_report(
    query=query,
    report_code='REL10',
    report_name='reles_alta_tensao',
    report_title='Relatório de Relés de Alta Tensão',
    formats=['pdf']
)
```

### Usando Reporters Individuais

```python
from reporters.csv_reporter import CSVReporter
from reporters.excel_reporter import ExcelReporter
from reporters.pdf_reporter import PDFReporter
import pandas as pd

# Criar dados
df = pd.DataFrame({
    'Relé': ['R001', 'R002', 'R003'],
    'Fabricante': ['GE', 'Schneider', 'GE'],
    'Tensão (kV)': [13.8, 20.0, 13.8]
})

# CSV
csv_reporter = CSVReporter()
csv_path = csv_reporter.export(
    df,
    report_code='REL01',
    report_name='fabricantes',
    report_title='Relatório de Fabricantes'
)

# Excel
excel_reporter = ExcelReporter()
xlsx_path = excel_reporter.export(
    df,
    report_code='REL01',
    report_name='fabricantes',
    report_title='Relatório de Fabricantes',
    sheet_name='Fabricantes'
)

# PDF
pdf_reporter = PDFReporter()
pdf_path = pdf_reporter.export(
    df,
    report_code='REL01',
    report_name='fabricantes',
    report_title='Relatório de Fabricantes',
    orientation='portrait'  # ou 'landscape'
)
```

## 🏗️ Arquitetura

```
src/python/reporters/
├── __init__.py                 # Módulo principal
├── base_reporter.py            # Classe base com padrões
├── csv_reporter.py             # Exportador CSV
├── excel_reporter.py           # Exportador Excel
├── pdf_reporter.py             # Exportador PDF
└── report_generator.py         # Orquestrador + PostgreSQL
```

### Componentes

#### `BaseReporter`
- Define cabeçalho/rodapé padronizados
- Cores Petrobras
- Geração de timestamps e filenames
- Validação de DataFrames

#### `CSVReporter`
- Exporta para CSV com metadados em comentários
- Suporte a múltiplas seções

#### `ExcelReporter`
- Formatação completa com cores e fontes
- Linhas zebradas (alternadas)
- Ajuste automático de largura de colunas
- Suporte a múltiplas planilhas

#### `PDFReporter`
- Geração com ReportLab
- Cabeçalho/rodapé em todas as páginas
- Tabelas formatadas com cores
- Orientação portrait/landscape automática

#### `ReportGenerator`
- Conecta ao PostgreSQL
- Orquestra os 9 relatórios do sistema
- Busca dados das views
- Chama exportadores apropriados

## 📋 Requisitos

Bibliotecas necessárias (já estão em `requirements.txt`):

```
pandas>=2.3.2
openpyxl>=3.1.5
reportlab>=4.0.7
psycopg2-binary>=2.9.10
```

## 🐛 Troubleshooting

### Erro de Conexão com PostgreSQL

```bash
# Verificar se o Docker está rodando
docker ps | grep protecai_postgres

# Verificar credenciais
docker exec protecai_postgres psql -U protecai -d protecai_db -c "SELECT 1;"
```

### Dados Vazios nos Relatórios

Os relatórios buscam dados do banco. Se as views retornarem vazias:

1. Verificar se o schema `protec_ai` tem dados:
   ```sql
   SELECT COUNT(*) FROM protec_ai.relays;
   ```

2. Carregar dados normalizados (FASE 4 - em desenvolvimento)

### Erro de Permissão em Arquivos

```bash
# Dar permissão de escrita
chmod -R u+w outputs/relatorios/
```

## 🎯 Próximos Passos

1. **FASE 4**: Implementar loader para popular banco com dados dos CSVs normalizados
2. **Dashboard Web**: Interface para visualização e download dos relatórios
3. **Agendamento**: Cron jobs para geração automática
4. **Notificações**: Email com relatórios anexados
5. **Templates Customizáveis**: Permitir usuário definir layout

## 📖 Exemplos de Saída

### CSV
```csv
# ENGENHARIA DE PROTEÇÃO PETROBRAS
# Relatório de Fabricantes de Relés
# Gerado em: 20/11/2025 15:59
#
manufacturer,country,model_count,relay_count,models
GENERAL ELECTRIC,USA,3,15,"P122, P220, P922"
SCHNEIDER ELECTRIC,France,2,8,"SEPAM S40, SEPAM S80"
```

### Excel
- **Linha 1**: Cabeçalho azul com título principal
- **Linha 2**: Título do relatório em amarelo
- **Linha 4+**: Dados com linhas zebradas
- **Última linha**: Rodapé com timestamp e paginação

### PDF
- **Cabeçalho**: Logo quadrado + título centralizado
- **Corpo**: Tabela formatada com cores Petrobras
- **Rodapé**: 3 colunas (timestamp | título | pág)

## 🤝 Contribuindo

Para adicionar novo relatório:

1. Criar view no PostgreSQL
2. Adicionar entrada em `ReportGenerator.REPORTS`
3. Testar com `--report REL##`

## 📄 Licença

Projeto interno Petrobras/UFF
