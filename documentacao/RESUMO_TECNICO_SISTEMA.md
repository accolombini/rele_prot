# 📘 RESUMO TÉCNICO - SISTEMA PROTECAI

**Data**: 22 de Novembro de 2025  
**Versão**: 1.0  
**Status**: PRODUÇÃO

---

## 🎯 VISÃO GERAL

Sistema completo de extração, normalização, análise e geração de relatórios para relés de proteção da Petrobras. Processa múltiplos formatos (PDF Schneider/GE, .S40 SEPAM) e gera 9 relatórios padronizados em Excel/PDF.

---

## 🏗️ ARQUITETURA ATUAL

```
ENTRADA → EXTRAÇÃO → PARSING → EXPORTAÇÃO → NORMALIZAÇÃO → DATABASE → RELATÓRIOS
```

### Componentes Principais

1. **Extractors** (Fase 1)
   - `pdf_extractor.py`: Extrai texto de PDFs (pdfplumber)
   - `ini_extractor.py`: Extrai INI de arquivos .S40

2. **Parsers** (Fase 2)
   - `schneider_parser.py`: P122, P220, P922
   - `micon_parser.py`: P143, P241 (GE)
   - `sepam_parser.py`: SEPAM S40

3. **Exporters** (Fase 3)
   - `full_parameters_exporter.py`: CSV completo
   - `excel_exporter.py`: Excel auditoria

4. **Normalizers** (Fase 4)
   - `relay_normalizer.py`: 3FN format
   - `normalized_csv_exporter.py`: CSV consolidados

5. **Database** (Fase 5)
   - `database_loader.py`: PostgreSQL loading
   - Schema: `protec_ai`

6. **Reporters** (Fase 6)
   - `report_generator.py`: Orquestrador
   - `excel_reporter.py`: Excel formatado
   - `pdf_reporter.py`: PDF com ReportLab

---

## 📊 RELATÓRIOS IMPLEMENTADOS

| ID | Nome | Colunas | Formato | Status |
|----|------|---------|---------|--------|
| REL01 | Fabricantes de Relés | 3 | Portrait | ✅ |
| REL02 | Setpoints Críticos | 8 | Portrait | ✅ |
| REL03 | Tipos de Relés | 4 | Portrait | ✅ |
| REL04 | Relés por Fabricante | 6 | Portrait | ✅ |
| REL05 | Funções de Proteção | 4 | Portrait | ✅ |
| REL06 | Completo de Relés | 19 | Landscape | ✅ |
| REL07 | Relés por Subestação | 7 | Portrait | ✅ |
| REL08 | Análise de Tensão | 18 | Landscape | ✅ |
| REL09 | Parâmetros Críticos | 8 | Portrait | ✅ |

---

## 🗄️ SCHEMA DO BANCO DE DADOS

```sql
protec_ai
├── manufacturers (id, name, description)
├── relay_models (id, manufacturer_id, model_name, software_version)
├── relays (id, source_file, bay_identifier, relay_type, voltage_class_kv, ...)
├── current_transformers (id, relay_id, ct_type, primary_a, secondary_a, ratio)
├── voltage_transformers (id, relay_id, vt_type, primary_v, secondary_v, ratio)
├── ansi_functions (id, ansi_code, name, description)
├── protection_functions (id, relay_id, ansi_function_id, is_enabled, ...)
└── parameters (id, protection_function_id, parameter_name, parameter_value, ...)
```

### Views Criadas (9)
- `vw_manufacturers`
- `vw_relay_types`
- `vw_relays_by_manufacturer`
- `vw_critical_setpoints`
- `vw_protection_functions_summary`
- `vw_relays_complete`
- `vw_relays_by_substation`
- `vw_voltage_analysis`
- `vw_critical_parameters_consolidated`

---

## 🔧 OTIMIZAÇÕES APLICADAS

### 1. Abreviações Padronizadas
```python
HEADER_ABBREVIATIONS = {
    'Fabricantes': 'Fab',
    'Habilitadas': 'EN',
    'Desabilitadas': 'DES',
    'C.Tensão kV': 'V_kV',
    'Código da Subestação': 'SE',
    'Data_N_Forn': 'Data_N_Forn',
    # ... +20 abreviações
}
```

### 2. Abreviações em SQL Views
```sql
-- Fabricantes
CASE 
    WHEN m.name = 'GENERAL ELECTRIC' THEN 'GE'
    WHEN m.name = 'SCHNEIDER ELECTRIC' THEN 'SNE'
    WHEN m.name = 'SCHWEITZER' THEN 'SEL'
    WHEN m.name = 'SIEMENS' THEN 'SIE'
    WHEN m.name = 'ABB' THEN 'ABB'
END

-- Tipos de Relé
CASE 
    WHEN r.relay_type = 'Proteção de Alimentador' THEN 'P_ALIM'
    WHEN r.relay_type = 'Proteção de Linha' THEN 'P_LIN'
    WHEN r.relay_type = 'Proteção de Motor' THEN 'P_MOT'
    WHEN r.relay_type = 'Proteção de Transformador' THEN 'P_TF'
END

-- Datas (6 dígitos)
SUBSTRING(TO_CHAR(r.config_date, 'YYYYMMDD'), 3)  -- 20200708 → 200708

-- Ver. SW (quebra de linha)
CASE
    WHEN LENGTH(software_version) > 8 THEN
        SUBSTRING(software_version, 1, 8) || E'\n' || 
        SUBSTRING(software_version, 9)
    ELSE software_version
END
```

### 3. Larguras de Colunas Dinâmicas
```python
# excel_reporter.py
if num_columns > 10:
    font_size = 9
    header_height = 60
else:
    font_size = 10
    header_height = 50

# Larguras por tipo de coluna
if 'Ver.' in column_name and 'SW' in column_name:
    col_width = max(calculated_width, 20)  # Ver. SW
elif 'Ver.' in column_name and 'FW' in column_name:
    col_width = max(calculated_width, 8)   # Ver. FW
elif 'Modelo' in column_name:
    col_width = max(calculated_width, 18)
# ... +10 regras específicas
```

### 4. Landscape Automático
```python
FORCE_LANDSCAPE = ['REL06', 'REL08']  # >15 colunas

if report_id in FORCE_LANDSCAPE or num_columns > 8:
    orientation = 'landscape'
```

---

## 📁 ESTRUTURA DE ARQUIVOS

```
rele_prot/
├── docker/
│   └── postgres/
│       ├── init.sql              # Schema creation
│       └── create_views.sql      # 9 views ✨ NOVO
│
├── inputs/
│   ├── pdf/                      # PDFs Schneider/GE
│   ├── txt/                      # .S40 SEPAM
│   ├── glossario/
│   │   ├── glossary_mapping.json
│   │   └── relay_models_config.json
│   └── registry/
│       └── processed_files.json  # Evita duplicatas
│
├── outputs/
│   ├── csv/                      # CSVs completos (Fase 3)
│   ├── excel/                    # Excel auditoria (Fase 3)
│   ├── norm_csv/                 # CSVs 3FN consolidados (Fase 4)
│   └── relatorios/              # 9 relatórios (Fase 6)
│       ├── csv/
│       ├── xlsx/
│       └── pdf/
│
├── src/python/
│   ├── main.py                   # Pipeline orchestrator ✨
│   ├── extractors/
│   │   ├── pdf_extractor.py
│   │   └── ini_extractor.py
│   ├── parsers/
│   │   ├── schneider_parser.py
│   │   ├── micon_parser.py
│   │   └── sepam_parser.py
│   ├── exporters/
│   │   ├── full_parameters_exporter.py
│   │   ├── excel_exporter.py
│   │   └── normalized_csv_exporter.py ✨
│   ├── normalizers/
│   │   └── relay_normalizer.py   ✨
│   ├── database/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── database_loader.py
│   ├── reporters/
│   │   ├── report_generator.py   ✨
│   │   ├── excel_reporter.py     ✨
│   │   └── pdf_reporter.py
│   └── utils/
│       ├── logger.py
│       ├── file_manager.py
│       └── glossary_loader.py
│
├── documentacao/
│   ├── GARANTIA_PIPELINE_21NOV2025.md
│   ├── PLANO_RETOMADA_42_RELES.md
│   └── RESUMO_TECNICO_SISTEMA.md  (este arquivo)
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

**✨ = Arquivos modificados/criados em 22/11/2025**

---

## 🧪 TESTE COMPLETO - COMANDOS

### 1. Setup Inicial
```bash
# Ativar ambiente
source /Volumes/Mac_XIII/virtualenvs/rele_prot/bin/activate

# Verificar PostgreSQL
docker ps | grep protecai_postgres

# Limpar outputs (opcional)
rm -rf outputs/csv/*.csv outputs/excel/*.xlsx
rm -rf outputs/norm_csv/*.csv
rm -rf outputs/relatorios/*/*.{csv,xlsx,pdf}
```

### 2. Executar Pipeline
```bash
# Pipeline completa (Fases 1-5)
python src/python/main.py

# Monitorar logs
tail -f logs/pipeline_*.log
```

### 3. Gerar Relatórios
```bash
# Todos os 9 relatórios
python -c "
from src.python.reporters.report_generator import ReportGenerator
g = ReportGenerator(output_base_path='outputs/relatorios')
for rel in ['REL01', 'REL02', 'REL03', 'REL04', 'REL05', 
            'REL06', 'REL07', 'REL08', 'REL09']:
    g.generate_report(rel)
"

# Relatório individual
python -c "
from src.python.reporters.report_generator import ReportGenerator
g = ReportGenerator(output_base_path='outputs/relatorios')
g.generate_report('REL06')
"
```

### 4. Consultas SQL Úteis
```sql
-- Total de relés
SELECT COUNT(*) FROM protec_ai.relays;

-- Relés por fabricante
SELECT m.name, COUNT(*) 
FROM protec_ai.relays r
JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.id
JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.id
GROUP BY m.name;

-- Relés sem voltage_class_kv
SELECT bay_identifier, relay_type 
FROM protec_ai.relays 
WHERE voltage_class_kv IS NULL;

-- Testar view de relatório
SELECT * FROM protec_ai.vw_relays_complete LIMIT 5;
```

---

## 🐛 PROBLEMAS CONHECIDOS E SOLUÇÕES

### 1. ⚠️ voltage_class_kv NULL
**Problema**: Alguns relés não têm classe de tensão definida  
**Solução**: Implementado cálculo automático a partir de VTs (relay_normalizer.py)
```python
if relay_info['voltage_class_kv'] is None and vts:
    main_vts = [vt for vt in vts if vt['vt_type'] == 'Main']
    if main_vts:
        primary_v = main_vts[0]['primary_v']
        relay_info['voltage_class_kv'] = round(primary_v / 1000.0, 2)
```

### 2. ⚠️ Text Overlap em Relatórios
**Problema**: Colunas muito largas invadiam adjacentes  
**Solução**: 
- Abreviações em SQL views
- Larguras mínimas por tipo de coluna
- Quebra de linha em Ver. SW
- Landscape automático para >8 colunas

### 3. ⚠️ VTs não detectados (GE)
**Problema**: VTs em continuation_lines não eram parseados  
**Solução**: Adicionado STRATEGY 2 em `_normalize_vts()` que busca em continuation_lines com regex

### 4. ⚠️ Duplicatas no processed_files.json
**Problema**: Re-processamento desnecessário  
**Solução**: Hash SHA256 do conteúdo do arquivo como chave

---

## 📊 MÉTRICAS ATUAIS

### Arquivos Processados: 8
- 5 PDFs (3 Schneider, 2 GE)
- 3 .S40 (SEPAM)

### Database
- Relés: 8
- CTs: 16
- VTs: 10
- Protection Functions: 64
- Parameters: 1,247

### Relatórios
- 9 tipos × 3 formatos = 27 arquivos/geração
- Formato: CSV, XLSX, PDF
- Estilo: Petrobras (azul/amarelo)

---

## 🔐 CREDENCIAIS E ACESSOS

### PostgreSQL
```
Host: localhost (Docker)
Port: 5432
Database: protecai_db
User: protecai
Password: protecai
Schema: protec_ai
```

### Conexão Python
```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='protecai_db',
    user='protecai',
    password='protecai'
)
```

---

## 📦 DEPENDÊNCIAS PRINCIPAIS

```
pandas==2.1.3
psycopg2-binary==2.9.9
pdfplumber==0.10.3
openpyxl==3.1.2
reportlab==4.0.7
python-dotenv==1.0.0
```

---

## 🚀 PRÓXIMOS DESENVOLVIMENTOS

### Fase 7: Front-End Web (Streamlit)
- [ ] Dashboard com estatísticas
- [ ] Upload de arquivos drag-and-drop
- [ ] Processamento com progress bar
- [ ] Geração de relatórios on-demand
- [ ] Busca e filtros de relés
- [ ] Gráficos interativos (Plotly)

### Fase 8: API REST (FastAPI)
- [ ] Endpoints para upload
- [ ] Endpoints para relatórios
- [ ] Endpoints para consultas
- [ ] WebSockets para progresso real-time
- [ ] Autenticação JWT
- [ ] Documentação Swagger

### Fase 9: Melhorias
- [ ] Validação de dados mais rigorosa
- [ ] Detecção de anomalias
- [ ] Comparação entre configurações
- [ ] Histórico de mudanças
- [ ] Exportação para outros formatos (Word, JSON)
- [ ] Testes unitários (pytest)

---

## 📞 SUPORTE E MANUTENÇÃO

### Logs
```bash
# Ver logs da última execução
tail -100 logs/pipeline_$(date +%Y%m%d)*.log

# Monitorar em tempo real
tail -f logs/pipeline_*.log

# Buscar erros
grep -i error logs/pipeline_*.log
```

### Backup
```bash
# Backup do banco
docker exec protecai_postgres pg_dump -U protecai protecai_db > backup_$(date +%Y%m%d).sql

# Backup do registry
cp inputs/registry/processed_files.json inputs/registry/backup_$(date +%Y%m%d).json

# Backup dos relatórios
tar -czf relatorios_backup_$(date +%Y%m%d).tar.gz outputs/relatorios/
```

### Troubleshooting
```bash
# Container parado?
docker start protecai_postgres

# Erro de conexão?
docker logs protecai_postgres

# Views não encontradas?
docker exec -i protecai_postgres psql -U protecai -d protecai_db < docker/postgres/create_views.sql

# Recriar schema
docker exec -i protecai_postgres psql -U protecai -d protecai_db < docker/postgres/init.sql
```

---

## ✅ CHECKLIST DE QUALIDADE

### Código
- [x] Código modular e reutilizável
- [x] Logging detalhado
- [x] Tratamento de erros
- [x] Documentação inline
- [ ] Testes unitários (TODO)
- [ ] Type hints completos (parcial)

### Dados
- [x] Normalização 3FN
- [x] Constraints no banco
- [x] Validação de entrada
- [x] Prevenção de duplicatas
- [ ] Auditoria de mudanças (TODO)

### Relatórios
- [x] Formatação padronizada
- [x] Estilo Petrobras
- [x] Landscape/Portrait automático
- [x] Abreviações consistentes
- [x] Exportação múltipla (CSV/XLSX/PDF)

---

**🎯 SISTEMA 100% FUNCIONAL E PRONTO PARA EXPANSÃO**

*Última atualização: 22/11/2025 20:30*
