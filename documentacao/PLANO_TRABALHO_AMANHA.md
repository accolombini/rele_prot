# 📅 Plano de Trabalho - 21 de Novembro de 2025

## 🎯 Objetivos do Dia

1. **Sistema de Relatórios Completo**
2. **Interface Básica (Front-end)**
3. **Teste com 42 Novos Relés**

---

## 📊 TAREFA 1: Sistema de Relatórios

### Status Atual
- ✅ Estrutura básica implementada (`generate_reports.py`)
- ✅ Conexão com PostgreSQL funcionando
- ⏳ Relatórios a implementar

### Relatórios Necessários

#### 1.1 Inventário de Relés
**Arquivo**: `relatorio_inventario_reles.{csv,xlsx,pdf}`
**Conteúdo**:
- ID do Relé
- Fabricante
- Modelo
- Número de Série
- Firmware Version
- Localização (Usina/Subestação)
- Total de CTs configurados
- Total de VTs configurados
- Total de Proteções ativas
- Total de Parâmetros

**Query SQL**:
```sql
SELECT 
    r.relay_id,
    m.manufacturer_name,
    r.model,
    r.serial_number,
    r.firmware_version,
    COUNT(DISTINCT ct.id) as total_cts,
    COUNT(DISTINCT vt.id) as total_vts,
    COUNT(DISTINCT pf.id) as total_protections
FROM protec_ai.relays r
LEFT JOIN protec_ai.manufacturers m ON r.manufacturer_id = m.id
LEFT JOIN protec_ai.ct_configurations ct ON r.id = ct.relay_id
LEFT JOIN protec_ai.vt_configurations vt ON r.id = vt.relay_id
LEFT JOIN protec_ai.protection_functions pf ON r.id = pf.relay_id
GROUP BY r.relay_id, m.manufacturer_name, r.model, r.serial_number, r.firmware_version
ORDER BY r.relay_id;
```

#### 1.2 Resumo de Proteções por Relé
**Arquivo**: `relatorio_protecoes_por_rele.{csv,xlsx,pdf}`
**Conteúdo**:
- Relé ID
- Código ANSI
- Nome da Função
- Descrição da Proteção
- Status (ativa/inativa)

**Query SQL**:
```sql
SELECT 
    r.relay_id,
    af.ansi_code,
    af.description as ansi_description,
    pf.function_name,
    pf.description
FROM protec_ai.protection_functions pf
JOIN protec_ai.relays r ON pf.relay_id = r.id
LEFT JOIN protec_ai.ansi_functions af ON pf.ansi_function_id = af.id
ORDER BY r.relay_id, af.ansi_code;
```

#### 1.3 Configuração de CTs
**Arquivo**: `relatorio_configuracao_cts.{csv,xlsx,pdf}`
**Conteúdo**:
- Relé ID
- Tipo de CT (phase/neutral/ground)
- Corrente Primária (A)
- Corrente Secundária (A)
- Relação (ratio)

#### 1.4 Configuração de VTs
**Arquivo**: `relatorio_configuracao_vts.{csv,xlsx,pdf}`
**Conteúdo**:
- Relé ID
- Tipo de VT
- Tensão Primária (kV)
- Tensão Secundária (V)
- Relação (ratio)

#### 1.5 Auditoria de Extração
**Arquivo**: `relatorio_auditoria_extracao.{csv,xlsx,pdf}`
**Conteúdo**:
- Nome do Arquivo Original
- Relé ID Gerado
- Data de Processamento
- Total Parâmetros Extraídos
- Total CTs Extraídos
- Total VTs Extraídos
- Total Proteções Extraídas
- Status (sucesso/erro)

**Fonte**: Logs de extração + dados do banco

#### 1.6 Comparativo de Fabricantes
**Arquivo**: `relatorio_comparativo_fabricantes.{csv,xlsx,pdf}`
**Conteúdo**:
- Fabricante
- Total de Relés
- Modelos Únicos
- Total de Proteções
- Proteções Médias por Relé
- Total de Parâmetros
- Parâmetros Médios por Relé

### Implementação
**Localização**: `src/python/reporters/`
**Arquivos**:
- `inventory_reporter.py` - Relatório 1.1
- `protections_reporter.py` - Relatório 1.2
- `ct_vt_reporter.py` - Relatórios 1.3 e 1.4
- `audit_reporter.py` - Relatório 1.5
- `comparison_reporter.py` - Relatório 1.6

**Tempo Estimado**: 3-4 horas

---

## 🖥️ TAREFA 2: Interface Básica (Front-end)

### Requisitos

#### 2.1 Tecnologia
**Opção A - Flask + Bootstrap** (Recomendada para MVP rápido)
- Backend: Flask (já temos Python)
- Frontend: Bootstrap 5 + jQuery
- Tempo: 2-3 horas

**Opção B - FastAPI + React**
- Backend: FastAPI (mais moderno)
- Frontend: React (mais robusto)
- Tempo: 4-6 horas

**Decisão**: Flask + Bootstrap para MVP de hoje

#### 2.2 Funcionalidades da Interface

##### Dashboard Principal
- **Rota**: `/`
- **Conteúdo**:
  - Total de relés no sistema
  - Total de proteções configuradas
  - Total de CTs e VTs
  - Gráfico: Relés por fabricante
  - Últimas extrações processadas

##### Página: Executar Pipeline
- **Rota**: `/pipeline`
- **Conteúdo**:
  - Botão: "Executar Pipeline Completa"
  - Log em tempo real da execução
  - Status: Em execução / Concluída / Erro
  - Resumo final com estatísticas

##### Página: Upload de Arquivos
- **Rota**: `/upload`
- **Conteúdo**:
  - Área de drag-and-drop para PDFs/TXT
  - Lista de arquivos já processados
  - Botão: "Processar Novos Arquivos"

##### Página: Relatórios
- **Rota**: `/relatorios`
- **Conteúdo**:
  - Lista de relatórios disponíveis
  - Botões para gerar cada relatório
  - Download em CSV/Excel/PDF
  - Histórico de relatórios gerados

##### Página: Visualizar Relés
- **Rota**: `/reles`
- **Conteúdo**:
  - Tabela com todos os relés
  - Filtros: Fabricante, Modelo
  - Busca por Relé ID
  - Link para detalhes de cada relé

##### Página: Detalhes do Relé
- **Rota**: `/reles/<relay_id>`
- **Conteúdo**:
  - Informações básicas do relé
  - Lista de proteções configuradas
  - Configuração de CTs
  - Configuração de VTs
  - Lista de parâmetros (quando implementado)

### Estrutura do Código
```
src/python/
├── app.py                 # Aplicação Flask principal
├── templates/             # Templates HTML
│   ├── base.html         # Template base
│   ├── index.html        # Dashboard
│   ├── pipeline.html     # Executar pipeline
│   ├── upload.html       # Upload de arquivos
│   ├── relatorios.html   # Geração de relatórios
│   ├── reles.html        # Lista de relés
│   └── rele_detail.html  # Detalhes do relé
└── static/               # CSS, JS, imagens
    ├── css/
    │   └── custom.css
    └── js/
        └── app.js
```

### APIs REST Necessárias
```python
# app.py

@app.route('/api/pipeline/run', methods=['POST'])
def run_pipeline():
    """Executa pipeline completa via subprocess"""
    pass

@app.route('/api/files/upload', methods=['POST'])
def upload_files():
    """Faz upload de arquivos para inputs/"""
    pass

@app.route('/api/relays', methods=['GET'])
def get_relays():
    """Retorna lista de relés (JSON)"""
    pass

@app.route('/api/relays/<relay_id>', methods=['GET'])
def get_relay_detail(relay_id):
    """Retorna detalhes de um relé (JSON)"""
    pass

@app.route('/api/reports/<report_name>', methods=['POST'])
def generate_report(report_name):
    """Gera relatório específico"""
    pass

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retorna estatísticas para dashboard"""
    pass
```

**Tempo Estimado**: 2-3 horas

---

## 🧪 TAREFA 3: Teste com 42 Novos Relés

### Preparação

#### 3.1 Organizar Arquivos
```bash
# Criar backup dos arquivos atuais
mkdir inputs/backup_8_reles
cp inputs/pdf/* inputs/backup_8_reles/
cp inputs/txt/* inputs/backup_8_reles/

# Copiar 42 novos relés para inputs/
# (usuário deve fornecer os arquivos)
```

#### 3.2 Limpar Registro
```bash
# Backup do registro atual
cp inputs/registry/processed_files.json inputs/registry/processed_files_8_reles_backup.json

# Limpar para reprocessamento
echo '{"processed_files": {}}' > inputs/registry/processed_files.json
```

#### 3.3 Limpar Banco de Dados
```bash
docker exec -i protecai_postgres psql -U protecai -d protecai_db -c \
"TRUNCATE TABLE protec_ai.relays CASCADE; 
 TRUNCATE TABLE protec_ai.manufacturers CASCADE; 
 TRUNCATE TABLE protec_ai.ansi_functions CASCADE;"
```

### Execução

#### 3.4 Executar Pipeline
```bash
workon rele_prot
python src/python/run_pipeline.py
```

### Validação

#### 3.5 Checklist de Validação
- [ ] Total de arquivos processados: 50 (8 antigos + 42 novos)
- [ ] Total de relés no banco: 50
- [ ] Erros de extração: 0
- [ ] Erros de normalização: 0
- [ ] Erros de carga: 0
- [ ] CTs carregados: verificar total
- [ ] VTs carregados: verificar total
- [ ] Proteções carregadas: verificar total

#### 3.6 Relatórios de Validação
```bash
# Gerar todos os relatórios para análise
python src/python/generate_reports.py --all

# Verificar:
# - relatorio_inventario_reles.xlsx - Deve ter 50 relés
# - relatorio_auditoria_extracao.xlsx - Verificar sucessos/erros
# - relatorio_comparativo_fabricantes.xlsx - Distribuição por fabricante
```

#### 3.7 Queries de Validação
```sql
-- Total de relés
SELECT COUNT(*) as total_relays FROM protec_ai.relays;

-- Relés por fabricante
SELECT m.manufacturer_name, COUNT(r.id) as total
FROM protec_ai.relays r
JOIN protec_ai.manufacturers m ON r.manufacturer_id = m.id
GROUP BY m.manufacturer_name;

-- Total de proteções
SELECT COUNT(*) as total_protections FROM protec_ai.protection_functions;

-- Relés com problemas (sem proteções)
SELECT relay_id FROM protec_ai.relays r
WHERE NOT EXISTS (
    SELECT 1 FROM protec_ai.protection_functions pf 
    WHERE pf.relay_id = r.id
);
```

**Tempo Estimado**: 1 hora (30min execução + 30min validação)

---

## 📋 Checklist Completo

### Manhã (3-4 horas)
- [ ] Implementar 6 relatórios em `src/python/reporters/`
- [ ] Testar cada relatório individualmente
- [ ] Validar outputs (CSV, Excel, PDF)

### Tarde (3-4 horas)
- [ ] Criar estrutura Flask (app.py + templates/)
- [ ] Implementar dashboard principal
- [ ] Implementar página de pipeline
- [ ] Implementar página de relatórios
- [ ] Implementar página de relés
- [ ] Testar interface localmente

### Final do Dia (1 hora)
- [ ] Receber 42 arquivos novos do usuário
- [ ] Copiar para inputs/
- [ ] Executar pipeline completa
- [ ] Validar resultados
- [ ] Gerar relatórios finais
- [ ] Documentar problemas encontrados

---

## 🚨 Pontos de Atenção

### Issue 1: Carregamento de Parâmetros
**Status**: ⏳ Pendente
**Problema**: Arquitetura FK (parameters.protection_function_id vs CSV relay_id)
**Decisão Necessária**: 
- Opção A: Criar tabela `relay_parameters` separada
- Opção B: Mapear para primeira proteção
- Opção C: Criar proteção genérica "System Parameters"
**Impacto**: Relatórios de parâmetros não funcionarão até resolver
**Tempo**: 1-2 horas após decisão

### Issue 2: Códigos ANSI
**Status**: ⏳ Pendente
**Problema**: 77 proteções com código "Unknown"
**Solução**: Criar glossário ANSI + melhorar parsers
**Impacto**: Relatório de proteções terá campos vazios
**Tempo**: 4-6 horas
**Decisão**: Deixar para depois do teste dos 42 relés

### Issue 3: Performance com 50 Relés
**Previsão**: Pipeline pode demorar 15-20 segundos (vs 3s com 8 relés)
**Monitorar**: Logs de cada fase
**Se necessário**: Implementar processamento paralelo

---

## 📦 Dependências Adicionais

### Para Interface Flask
```bash
pip install flask flask-cors flask-socketio
pip install plotly  # Para gráficos no dashboard
```

### Para Geração de PDFs
```bash
pip install reportlab  # Já deve estar instalado
```

---

## 🎯 Critérios de Sucesso

### Sistema de Relatórios
- ✅ 6 relatórios funcionando
- ✅ Outputs em 3 formatos (CSV, Excel, PDF)
- ✅ Queries SQL otimizadas (< 1s por relatório)

### Interface Básica
- ✅ Dashboard com estatísticas ao vivo
- ✅ Executar pipeline via interface
- ✅ Gerar relatórios via interface
- ✅ Visualizar relés e detalhes
- ✅ Interface responsiva (mobile-friendly)

### Teste 42 Relés
- ✅ 50 relés no banco (8 + 42)
- ✅ Taxa de sucesso > 95%
- ✅ Todos os relatórios gerados
- ✅ Performance aceitável (< 30s pipeline completa)

---

## 📞 Dúvidas a Resolver com Usuário

1. **Parâmetros**: Qual abordagem preferida para FK?
2. **Interface**: Flask+Bootstrap ou FastAPI+React?
3. **Relatórios**: Algum relatório adicional necessário?
4. **42 Relés**: Quando estarão disponíveis para teste?
5. **Deployment**: Onde será hospedado o sistema?

---

## 🔗 Referências

- [Documentação Pipeline](./SISTEMA_RELATORIOS.md)
- [README Principal](../README.md)
- [Logs](../logs/)
- [Outputs](../outputs/)
