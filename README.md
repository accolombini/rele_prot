# ProtecAI - Pipeline de Extração e Análise de Relés de Proteção

Sistema integrado para extração, normalização e análise de dados de relés de proteção elétrica.

## 🚀 Execução Rápida

### Pipeline Completa de Dados
```bash
workon rele_prot
python src/python/run_pipeline.py
```

Este comando único executa todas as fases:
1. **Extração**: PDF/TXT → CSV/Excel
2. **Normalização**: CSV → Dados normalizados (3FN)
3. **Carga no Banco**: CSV normalizado → PostgreSQL

### Geração de Relatórios (On-Demand)
```bash
python src/python/generate_reports.py --all
```

## 📋 Pré-requisitos

- Python 3.12.5
- PostgreSQL 16 (via Docker)
- Ambiente virtual: `workon rele_prot`

### Iniciar Banco de Dados
```bash
docker-compose up -d
```

## 📂 Estrutura do Projeto

```
inputs/
  ├── pdf/           # Arquivos PDF de relés
  ├── txt/           # Arquivos .S40 (SEPAM)
  └── glossario/     # Glossários de mapeamento

outputs/
  ├── csv/           # CSVs extraídos
  ├── excel/         # Excel extraídos
  ├── norm_csv/      # Dados normalizados (5 arquivos consolidados)
  └── norm_excel/    # Excel normalizados individuais

src/python/
  ├── run_pipeline.py       # 🎯 COMANDO PRINCIPAL - Pipeline integrada
  ├── main.py              # FASE 1: Extração
  ├── normalize.py         # FASE 2: Normalização
  ├── test_loader.py       # FASE 3: Carga no banco
  └── generate_reports.py  # Relatórios (separado)
```

## 🔄 Fluxo da Pipeline

### 1️⃣ Extração (main.py)
- **Input**: PDFs (GE MiCOM, Schneider Easergy) + TXT (.S40)
- **Processo**: Extração de parâmetros, CTs, VTs, proteções
- **Output**: 8 CSVs + 8 Excel em `outputs/csv` e `outputs/excel`

### 2️⃣ Normalização (normalize.py)
- **Input**: CSVs de `outputs/csv`
- **Processo**: Normalização para 3FN
- **Output**: 
  - 5 CSVs consolidados em `outputs/norm_csv/`:
    - `all_relays_info.csv`
    - `all_ct_data.csv`
    - `all_vt_data.csv`
    - `all_protections.csv`
    - `all_parameters.csv`
  - 8 Excel individuais em `outputs/norm_excel/`

### 3️⃣ Carga no Banco (test_loader.py)
- **Input**: CSVs de `outputs/norm_csv`
- **Processo**: Carga no PostgreSQL (schema `protec_ai`)
- **Output**: Dados em tabelas relacionais

### 📊 Relatórios (generate_reports.py)
- **Input**: Dados do PostgreSQL
- **Opções**: 
  - `--all`: Todos os relatórios
  - `--relays`: Inventário de relés
  - `--protections`: Resumo de proteções
- **Output**: CSV, Excel e PDF em `outputs/relatorios/`

## 🔧 Arquivos Suportados

### Formatos
- **PDF**: GE MiCOM (00.01: format), Schneider Easergy (0120: format)
- **TXT**: SEPAM (.S40 files)

### Fabricantes
- General Electric (GE)
- Schneider Electric
- Alstom

## 📈 Exemplo de Uso

```bash
# 1. Ativar ambiente
workon rele_prot

# 2. Iniciar banco de dados
docker-compose up -d

# 3. Executar pipeline completa
python src/python/run_pipeline.py

# 4. Gerar relatórios (opcional)
python src/python/generate_reports.py --all
```

## 🎯 Status Atual

✅ **Funcionalidades Implementadas:**
- Extração de PDFs (GE + Schneider) e TXT (SEPAM)
- Normalização para 3FN
- Carga em PostgreSQL
- Pipeline integrada (comando único)
- Sistema de relatórios on-demand

⏳ **Próximos Passos (21/11/2025):**
- Sistema de relatórios completo (5 relatórios principais)
- Interface web básica (Flask + Bootstrap)
- Teste com 42 novos relés
- Mapeamento de códigos ANSI

📚 **Documentação Detalhada:**
- [Plano de Trabalho 21/11](documentacao/PLANO_21NOV2025.md)
- [Arquitetura Front-end](documentacao/ARQUITETURA_FRONT_END.md)
- [Sistema de Relatórios](documentacao/SISTEMA_RELATORIOS.md)

## 📝 Logs

Todos os logs são salvos em `logs/` com timestamp:
- `pipeline_YYYYMMDD_HHMMSS.log` - Pipeline completa
- `extraction_YYYYMMDD_HHMMSS.log` - Extração
- `normalization_YYYYMMDD_HHMMSS.log` - Normalização
- `database_loader_YYYYMMDD_HHMMSS.log` - Carga no banco

## 🐛 Troubleshooting

### VSCode travando
Use `workon rele_prot` em vez de `source /path/to/activate`

### Erro de conexão PostgreSQL
```bash
docker ps  # Verificar se container está rodando
docker-compose restart  # Reiniciar se necessário
```

### Reprocessar arquivos
```bash
echo '{"processed_files": {}}' > inputs/registry/processed_files.json
python src/python/run_pipeline.py
```
