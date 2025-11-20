# Plano de Trabalho - 21 de Novembro de 2025

## 🎯 Objetivos do Dia

1. **Sistema de Relatórios Completo**
2. **Interface Front-end Básica**
3. **Teste com 42 Novos Relés**

---

## 📊 1. Sistema de Relatórios

### Estado Atual
- ✅ Estrutura base implementada (`generate_reports.py`)
- ✅ 3 reporters configurados: CSV, Excel, PDF
- ⏳ Funcionalidades incompletas

### Tarefas

#### 1.1. Implementar Relatórios Principais
**Prioridade: ALTA**

##### Relatório 1: Inventário de Relés
```python
# Arquivo: src/python/reports/relay_inventory.py
# Conteúdo:
# - Lista completa de relés
# - Fabricante, modelo, firmware
# - Data de processamento
# - Status (ativo/inativo)
# - Localização (se disponível)
```

##### Relatório 2: Análise de Proteções
```python
# Arquivo: src/python/reports/protection_analysis.py
# Conteúdo:
# - Proteções por relé
# - Códigos ANSI identificados
# - Setpoints (quando disponível)
# - Status de habilitação
# - Agrupamento por tipo de proteção
```

##### Relatório 3: Configuração de CTs e VTs
```python
# Arquivo: src/python/reports/transformer_config.py
# Conteúdo:
# - CTs: relação, corrente primária/secundária, classe
# - VTs: relação, tensão primária/secundária
# - Validação de valores (nulls, inconsistências)
```

##### Relatório 4: Parâmetros Extraídos
```python
# Arquivo: src/python/reports/parameters_report.py
# Conteúdo:
# - Total de parâmetros por relé
# - Parâmetros agrupados por categoria
# - Valores configurados
# - Comparação entre relés similares
```

##### Relatório 5: Auditoria de Dados
```python
# Arquivo: src/python/reports/data_audit.py
# Conteúdo:
# - Completude dos dados (% campos preenchidos)
# - Valores null/inválidos
# - Inconsistências detectadas
# - Recomendações de correção
```

#### 1.2. Funcionalidades de Relatórios

```python
# Opções de execução:
# 1. Relatório individual
python src/python/generate_reports.py --report inventory

# 2. Todos os relatórios
python src/python/generate_reports.py --all

# 3. Formato específico
python src/python/generate_reports.py --report inventory --format pdf

# 4. Filtros
python src/python/generate_reports.py --report protections --relay R001

# 5. Período
python src/python/generate_reports.py --report audit --from 2025-11-01 --to 2025-11-21
```

#### 1.3. Estrutura de Saída

```
outputs/relatorios/
├── csv/
│   ├── inventario_reles_20251121.csv
│   ├── analise_protecoes_20251121.csv
│   ├── config_transformadores_20251121.csv
│   └── auditoria_dados_20251121.csv
├── xlsx/
│   ├── inventario_reles_20251121.xlsx
│   ├── analise_protecoes_20251121.xlsx (com gráficos)
│   └── auditoria_dados_20251121.xlsx (com dashboards)
└── pdf/
    ├── relatorio_completo_20251121.pdf
    ├── inventario_executivo_20251121.pdf
    └── analise_tecnica_20251121.pdf
```

#### 1.4. Cronograma de Implementação

| Hora | Tarefa | Duração |
|------|--------|---------|
| 09:00-10:30 | Implementar Relatório 1 (Inventário) | 1.5h |
| 10:30-12:00 | Implementar Relatório 2 (Proteções) | 1.5h |
| 12:00-13:00 | **ALMOÇO** | 1h |
| 13:00-14:00 | Implementar Relatório 3 (CTs/VTs) | 1h |
| 14:00-15:00 | Implementar Relatório 4 (Parâmetros) | 1h |
| 15:00-16:00 | Implementar Relatório 5 (Auditoria) | 1h |
| 16:00-16:30 | Testes e refinamentos | 0.5h |

---

## 🖥️ 2. Interface Front-end Básica

### Objetivo
Criar interface web simples para:
- Executar pipeline de dados
- Gerar relatórios
- Visualizar status do sistema
- Carregar novos arquivos

### Tecnologia Proposta
**Flask + HTML/CSS/JS (Bootstrap)**
- Simples, rápido, sem dependências complexas
- Integração direta com Python backend

### Estrutura

```
src/
└── web/
    ├── app.py              # Flask application
    ├── static/
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── main.js
    └── templates/
        ├── base.html       # Template base
        ├── index.html      # Dashboard principal
        ├── pipeline.html   # Execução pipeline
        ├── reports.html    # Geração relatórios
        └── upload.html     # Upload arquivos
```

### Funcionalidades

#### 2.1. Dashboard Principal (`/`)
- **Status do Sistema**
  - Total de relés processados
  - Últimas execuções da pipeline
  - Status do banco de dados
  - Espaço em disco

- **Estatísticas Rápidas**
  - Total de parâmetros extraídos
  - Total de proteções identificadas
  - Fabricantes representados
  - Modelos de relés

- **Ações Rápidas**
  - Botão: "Executar Pipeline"
  - Botão: "Gerar Relatórios"
  - Botão: "Carregar Arquivos"

#### 2.2. Página Pipeline (`/pipeline`)
- **Execução Manual**
  - Botão: "Iniciar Pipeline Completa"
  - Log em tempo real (WebSocket/SSE)
  - Progresso por fase (Extração, Normalização, Carga)

- **Histórico**
  - Últimas 10 execuções
  - Duração, status, erros
  - Link para logs completos

#### 2.3. Página Relatórios (`/reports`)
- **Geração de Relatórios**
  - Dropdown: Selecionar relatório
  - Dropdown: Selecionar formato (CSV/Excel/PDF)
  - Filtros: Data, relé, fabricante
  - Botão: "Gerar Relatório"

- **Relatórios Gerados**
  - Lista dos últimos relatórios
  - Download direto
  - Visualização inline (CSV/Excel)

#### 2.4. Página Upload (`/upload`)
- **Upload de Arquivos**
  - Drag & drop area
  - Suporte: PDF, TXT, S40
  - Validação de formato
  - Preview antes de processar

- **Arquivos Pendentes**
  - Lista de arquivos carregados
  - Não processados pela pipeline
  - Botão: "Processar Agora"

### APIs REST

```python
# app.py - Endpoints principais

# Status do sistema
GET /api/status
# Retorna: { relays: 8, parameters: 3947, last_run: "2025-11-20 17:12:59" }

# Executar pipeline
POST /api/pipeline/run
# Retorna: { job_id: "uuid", status: "running" }

# Status da pipeline
GET /api/pipeline/status/<job_id>
# Retorna: { status: "running", phase: "normalization", progress: 45 }

# Logs da pipeline
GET /api/pipeline/logs/<job_id>
# Retorna: { logs: [...], complete: false }

# Gerar relatório
POST /api/reports/generate
# Body: { report_type: "inventory", format: "pdf", filters: {...} }
# Retorna: { file_url: "/downloads/report_xyz.pdf" }

# Listar relatórios
GET /api/reports/list
# Retorna: [{ name: "inventario_20251121.pdf", size: 1234, date: "..." }]

# Upload arquivo
POST /api/upload
# Body: FormData com arquivo
# Retorna: { filename: "P999.pdf", status: "uploaded" }

# Listar arquivos
GET /api/files/list
# Retorna: [{ name: "P999.pdf", processed: false, date: "..." }]
```

### Cronograma de Implementação

| Hora | Tarefa | Duração |
|------|--------|---------|
| 16:30-17:00 | Setup Flask + estrutura base | 0.5h |
| 17:00-17:30 | Dashboard principal | 0.5h |
| 17:30-18:00 | Página Pipeline + APIs | 0.5h |
| 18:00-18:30 | Página Relatórios + APIs | 0.5h |
| 18:30-19:00 | Página Upload + APIs | 0.5h |
| 19:00-19:30 | Testes e refinamentos | 0.5h |

---

## 🧪 3. Teste com 42 Novos Relés

### Objetivo
Validar sistema completo com volume real de produção

### Pré-requisitos
- ✅ Pipeline integrada funcionando
- ✅ Sistema de relatórios completo
- ⏳ Decisão sobre carga de parâmetros (FK)

### Etapas

#### 3.1. Preparação (19:30-20:00)
```bash
# 1. Backup do estado atual
cp inputs/registry/processed_files.json inputs/registry/backup_21nov_antes_42.json
pg_dump -U protecai -d protecai_db -Fc > backups/db_antes_42_reles.dump

# 2. Organizar arquivos
# - Colocar 42 arquivos em inputs/pdf/ ou inputs/txt/
# - Verificar nomes e formatos

# 3. Limpar outputs (opcional)
rm -rf outputs/csv/*
rm -rf outputs/norm_csv/*
rm -rf outputs/excel/*
rm -rf outputs/norm_excel/*
```

#### 3.2. Execução (20:00-20:15)
```bash
# Executar pipeline completa
python src/python/run_pipeline.py

# OU via interface web
# http://localhost:5000/pipeline -> "Iniciar Pipeline"
```

#### 3.3. Validação (20:15-21:00)

##### Validação 1: Extração
```bash
# Verificar CSVs gerados
ls -lh outputs/csv/
# Espera: 50 arquivos (8 antigos + 42 novos)

# Verificar parâmetros extraídos
grep "Total Parameters Extracted" outputs/csv/*.csv | wc -l
# Espera: 50 linhas

# Somar parâmetros
grep "Total Parameters Extracted" outputs/csv/*.csv | \
  awk -F';' '{sum+=$NF} END {print "Total:", sum}'
# Espera: ~20.000 parâmetros (estimativa)
```

##### Validação 2: Normalização
```bash
# Verificar CSVs consolidados
wc -l outputs/norm_csv/all_*.csv
# Espera:
# - all_relays_info.csv: 51 linhas (1 header + 50 relés)
# - all_protections.csv: 400-500 linhas
# - all_parameters.csv: 20.000+ linhas

# Verificar distribuição
echo "Relés por fabricante:"
tail -n +2 outputs/norm_csv/all_relays_info.csv | \
  awk -F';' '{print $3}' | sort | uniq -c
```

##### Validação 3: Banco de Dados
```sql
-- Conectar ao PostgreSQL
docker exec -it protecai_postgres psql -U protecai -d protecai_db

-- Verificar contagens
SELECT 
    (SELECT COUNT(*) FROM protec_ai.relays) as relays,
    (SELECT COUNT(*) FROM protec_ai.protection_functions) as protections,
    (SELECT COUNT(*) FROM protec_ai.current_transformers) as cts,
    (SELECT COUNT(*) FROM protec_ai.voltage_transformers) as vts;

-- Verificar relés por fabricante
SELECT manufacturer, COUNT(*) 
FROM protec_ai.relays r
JOIN protec_ai.manufacturers m ON r.manufacturer_id = m.id
GROUP BY manufacturer;

-- Verificar proteções por ANSI code
SELECT ansi_code, COUNT(*) 
FROM protec_ai.protection_functions pf
JOIN protec_ai.ansi_functions af ON pf.ansi_function_id = af.id
GROUP BY ansi_code
ORDER BY COUNT(*) DESC
LIMIT 10;
```

##### Validação 4: Relatórios
```bash
# Gerar todos os relatórios
python src/python/generate_reports.py --all

# OU via interface web
# http://localhost:5000/reports -> "Gerar Todos"

# Verificar outputs
ls -lh outputs/relatorios/{csv,xlsx,pdf}/

# Abrir relatório executivo
open outputs/relatorios/pdf/relatorio_completo_*.pdf
```

#### 3.4. Análise de Resultados (21:00-21:30)

##### Métricas Esperadas
| Métrica | Valor Esperado | Validação |
|---------|----------------|-----------|
| Total de relés | 50 | `SELECT COUNT(*) FROM protec_ai.relays` |
| Taxa de sucesso extração | >95% | Verificar logs |
| Parâmetros extraídos | 15.000-25.000 | `wc -l outputs/norm_csv/all_parameters.csv` |
| Proteções identificadas | 300-600 | `SELECT COUNT(*) FROM protec_ai.protection_functions` |
| Erros de normalização | <5% | Verificar logs |
| Erros de carga DB | 0 | Verificar logs + queries |
| Tempo total pipeline | 10-30s | Ver sumário run_pipeline.py |

##### Problemas Potenciais

**Problema 1: Arquivos não processados**
- Causa: Formato desconhecido, arquivo corrompido
- Ação: Verificar logs, tentar extração manual
- Workaround: Mover para inputs/teste/, processar separadamente

**Problema 2: Parâmetros muito baixos**
- Causa: Novo formato de PDF/TXT não suportado
- Ação: Analisar arquivo manualmente, atualizar parsers
- Tempo estimado: 2-4 horas por formato novo

**Problema 3: Códigos ANSI não identificados**
- Causa: Nomenclatura diferente nos novos relés
- Ação: Expandir glossário ANSI
- Tempo estimado: 1-2 horas

**Problema 4: Carga de parâmetros falhando**
- Causa: FK de protection_functions ainda não resolvido
- Ação: Implementar solução temporária (FK nullable)
- Tempo estimado: 30 minutos

**Problema 5: Performance ruim**
- Causa: Volume maior de dados, queries não otimizadas
- Ação: Adicionar índices, otimizar queries
- Tempo estimado: 1 hora

---

## 📋 Checklist Final

### Manhã (09:00-12:00)
- [ ] Relatório 1: Inventário de Relés
- [ ] Relatório 2: Análise de Proteções
- [ ] Teste inicial dos 2 primeiros relatórios

### Tarde (13:00-16:30)
- [ ] Relatório 3: CTs/VTs
- [ ] Relatório 4: Parâmetros
- [ ] Relatório 5: Auditoria
- [ ] Teste completo de todos os relatórios

### Noite (16:30-19:30)
- [ ] Setup Flask + estrutura
- [ ] Dashboard principal
- [ ] Página Pipeline
- [ ] Página Relatórios
- [ ] Página Upload
- [ ] Teste completo do front-end

### Final (19:30-21:30)
- [ ] Preparação ambiente para 42 relés
- [ ] Backup do estado atual
- [ ] Execução pipeline com 42 relés
- [ ] Validação completa (extração, normalização, banco)
- [ ] Geração de relatórios finais
- [ ] Análise de resultados
- [ ] Documentação de problemas encontrados

---

## 🚀 Comandos Rápidos

### Pipeline de Dados
```bash
# Ativar ambiente
workon rele_prot

# Executar pipeline completa
python src/python/run_pipeline.py

# Verificar logs
tail -f logs/pipeline_*.log
```

### Relatórios
```bash
# Gerar todos
python src/python/generate_reports.py --all

# Gerar específico
python src/python/generate_reports.py --report inventory --format pdf

# Verificar outputs
ls -lh outputs/relatorios/{csv,xlsx,pdf}/
```

### Front-end
```bash
# Iniciar servidor Flask
python src/web/app.py

# Acessar interface
open http://localhost:5000
```

### Banco de Dados
```bash
# Conectar
docker exec -it protecai_postgres psql -U protecai -d protecai_db

# Backup
pg_dump -U protecai -d protecai_db -Fc > backups/db_$(date +%Y%m%d_%H%M%S).dump

# Restore
pg_restore -U protecai -d protecai_db -c backups/db_XXXXXX.dump
```

### Git
```bash
# Verificar status
git status

# Commit
git add -A
git commit -m "feat: relatórios e front-end básico"

# Push
git push
```

---

## 📊 Resultado Esperado

Ao final do dia 21/11:
- ✅ **5 relatórios funcionais** (inventário, proteções, transformadores, parâmetros, auditoria)
- ✅ **Interface web básica** (dashboard, pipeline, relatórios, upload)
- ✅ **50 relés processados** (8 de teste + 42 novos)
- ✅ **Sistema validado** com volume real de produção
- ✅ **Documentação completa** de problemas e soluções
- ✅ **Pronto para uso em produção** (com ressalvas conhecidas)

---

## ⚠️ Pendências Conhecidas

1. **Parâmetros não carregando no banco** (FK de protection_functions)
2. **Códigos ANSI genéricos** (maioria marcada como "Unknown")
3. **Performance não testada** com >100 relés
4. **Front-end é MVP** (sem autenticação, validações básicas)
5. **Relatórios sem gráficos avançados** (versão inicial)

Estas pendências devem ser endereçadas em iterações futuras.

---

**Última atualização:** 20 de novembro de 2025, 17:30
**Próxima revisão:** 21 de novembro de 2025, 21:30
