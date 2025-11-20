# 🔧 Issues Pendentes - ProtecAI

## 🚨 CRÍTICO

### Issue #1: Carregamento de Parâmetros no Banco de Dados
**Status**: ⏳ **BLOQUEADOR**
**Descoberto em**: 20/11/2025
**Impacto**: 3947 parâmetros extraídos, 0 no banco de dados

#### Descrição
O sistema extrai 3947 parâmetros corretamente e normaliza em `all_parameters.csv`, mas não consegue carregá-los no PostgreSQL devido a incompatibilidade de chaves estrangeiras.

#### Causa Raiz
- **Tabela `parameters`** espera FK: `protection_function_id` (INT)
- **CSV `all_parameters.csv`** fornece: `relay_id` (VARCHAR, ex: "R001")
- **Problema**: Não há mapeamento direto entre parâmetros e funções de proteção

#### Dados Atuais
```
Extraídos: 3947 parâmetros
No Banco: 0 parâmetros
Perda: 100%
```

#### Opções de Solução

##### Opção A: Criar Tabela `relay_parameters` (Recomendada)
**Descrição**: Criar tabela separada para parâmetros não vinculados a proteções
```sql
CREATE TABLE protec_ai.relay_parameters (
    id SERIAL PRIMARY KEY,
    relay_id INTEGER REFERENCES protec_ai.relays(id),
    parameter_code VARCHAR(50),
    parameter_name TEXT,
    parameter_value TEXT,
    unit VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Vantagens**:
- Arquitetura limpa
- Parâmetros de sistema separados de parâmetros de proteção
- Permite futura expansão (parâmetros globais vs específicos)

**Desvantagens**:
- Requer migração do schema
- Duas tabelas para parâmetros

**Tempo**: 1-2 horas

##### Opção B: Mapear para Primeira Proteção
**Descrição**: Associar todos os parâmetros à primeira função de proteção do relé
```python
# Buscar primeira proteção do relé
first_protection = session.query(ProtectionFunction)\
    .filter_by(relay_id=relay_db_id).first()
if first_protection:
    parameter.protection_function_id = first_protection.id
```
**Vantagens**:
- Rápido de implementar
- Não requer mudança de schema

**Desvantagens**:
- Semanticamente incorreto (parâmetros não pertencem a proteções específicas)
- Dados artificialmente vinculados

**Tempo**: 30 minutos

##### Opção C: Criar Proteção Genérica "System Parameters"
**Descrição**: Criar função de proteção virtual para cada relé
```python
# Criar proteção genérica se não existir
system_protection = ProtectionFunction(
    relay_id=relay_db_id,
    function_name="System Parameters",
    ansi_function_id=ansi_unknown_id
)
```
**Vantagens**:
- Mantém arquitetura atual
- Separação clara (proteção virtual vs reais)

**Desvantagens**:
- Poluição de dados (proteções "fake")
- Confusão em relatórios

**Tempo**: 1 hora

#### Decisão Necessária
⏳ **Aguardando decisão do usuário/arquiteto**

#### Workaround Temporário
Parâmetros permanecem em `all_parameters.csv` até decisão. Relatórios podem ler diretamente do CSV.

---

## ⚠️ ALTA PRIORIDADE

### Issue #2: Códigos ANSI "Unknown"
**Status**: ⏳ Não Implementado
**Impacto**: 77 proteções sem identificação ANSI correta

#### Descrição
Todas as proteções estão sendo marcadas como ANSI "Unknown" porque os parsers não extraem códigos ANSI dos nomes das funções.

#### Exemplos
```csv
Relay ID,Function Name,ANSI Code
R002,50N-1 NEF I>,Unknown
R003,Directional O/C Ph,Unknown
R006,67N-1 Directional EF,Unknown
```

#### Causa Raiz
- **Parsers atuais**: Extraem nome da proteção, mas não identificam ANSI code
- **Glossário ANSI**: Não implementado
- **Regex patterns**: Não buscam códigos ANSI (50, 51, 67N, etc.)

#### Dados Atuais
```
Total proteções: 77
Com código ANSI: 0
"Unknown": 77 (100%)
```

#### Solução Proposta

##### Fase 1: Criar Glossário ANSI
**Arquivo**: `inputs/glossario/ansi_codes.json`
```json
{
  "50": {"description": "Instantaneous Overcurrent", "type": "Phase"},
  "50N": {"description": "Instantaneous Ground Overcurrent", "type": "Ground"},
  "51": {"description": "Time Overcurrent", "type": "Phase"},
  "51N": {"description": "Time Ground Overcurrent", "type": "Ground"},
  "67": {"description": "Directional Overcurrent", "type": "Phase"},
  "67N": {"description": "Directional Ground Overcurrent", "type": "Ground"},
  "87": {"description": "Differential Protection", "type": "Differential"},
  ...
}
```

##### Fase 2: Melhorar Parsers
**Arquivos**: `micon_parser.py`, `sepam_parser.py`, `schneider_parser.py`
```python
import re

ANSI_PATTERN = re.compile(r'\b(\d{2}[A-Z]?)\b')

def extract_ansi_code(function_name):
    """Extrai código ANSI do nome da função"""
    match = ANSI_PATTERN.search(function_name)
    if match:
        return match.group(1)
    return "Unknown"
```

##### Fase 3: Atualizar Normalizadores
**Arquivo**: `normalize.py`
```python
# Adicionar coluna ANSI code
protections_df['ansi_code'] = protections_df['function_name'].apply(extract_ansi_code)
```

**Tempo Estimado**: 4-6 horas

#### Impacto nos Relatórios
- ⚠️ Relatório de proteções terá campos vazios
- ⚠️ Impossível filtrar/agrupar por tipo de proteção
- ⚠️ Análise comparativa de proteções limitada

---

## 📊 MÉDIA PRIORIDADE

### Issue #3: Performance com Grandes Volumes
**Status**: ⏳ Não Testado
**Impacto Potencial**: Alto com 42+ relés

#### Descrição
Pipeline atual processa 8 relés em 3.2 segundos. Performance com 50 relés não foi testada.

#### Previsão
```
8 relés: 3.2s
50 relés: ~20s (estimativa linear)
100 relés: ~40s
```

#### Gargalos Potenciais
1. **Extração PDF**: PyMuPDF lê arquivo completo em memória
2. **Normalização**: Concatenação de DataFrames sem otimização
3. **Database Load**: Commits individuais sem batch

#### Soluções Propostas

##### 3.1 Processamento Paralelo
```python
from concurrent.futures import ProcessPoolExecutor

def extract_file(file_path):
    # Extração de um arquivo
    pass

with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(extract_file, files)
```
**Ganho Esperado**: 2-4x mais rápido

##### 3.2 Batch Commits
```python
# Em vez de commit por relé
session.add(relay)
session.commit()

# Fazer batch
session.add_all(relays_list)
session.commit()
```
**Ganho Esperado**: 30-50% mais rápido

**Tempo Estimado**: 3-4 horas
**Prioridade**: Implementar após teste com 42 relés

---

### Issue #4: Falta de Interface Gráfica
**Status**: ⏳ Planejado para 21/11/2025
**Impacto**: Usuário depende de linha de comando

#### Requisitos
- Dashboard com estatísticas
- Execução de pipeline via web
- Upload de arquivos
- Geração de relatórios
- Visualização de relés

**Ver**: `PLANO_TRABALHO_AMANHA.md` para detalhes

---

## 🔍 BAIXA PRIORIDADE

### Issue #5: Logs Muito Verbosos
**Status**: ⏳ Aceitável por enquanto
**Impacto**: Arquivos de log grandes

#### Descrição
Logs atuais são muito detalhados (DEBUG level), gerando arquivos grandes.

#### Solução
```python
# Mudar nível de log em produção
logger.setLevel(logging.INFO)  # Em vez de DEBUG
```

**Tempo**: 15 minutos

---

### Issue #6: Sem Validação de Inputs
**Status**: ⏳ Não Crítico
**Impacto**: Erros não informativos

#### Descrição
Sistema não valida arquivos antes de processar:
- Formato correto (PDF/TXT)
- Arquivo corrompido
- Fabricante desconhecido

#### Solução
```python
def validate_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.endswith('.pdf'):
        # Validar PDF
        pass
    elif file_path.endswith(('.txt', '.S40')):
        # Validar TXT
        pass
    else:
        raise ValueError(f"Unsupported format: {file_path}")
```

**Tempo**: 1-2 horas

---

### Issue #7: Falta de Testes Automatizados
**Status**: ⏳ Desejável
**Impacto**: Risco de regressões

#### Descrição
Nenhum teste automatizado implementado.

#### Proposta
```
tests/
├── test_extractors.py    # Testar extração de PDFs/TXT
├── test_parsers.py       # Testar parsers (MiCOM, SEPAM, Schneider)
├── test_normalizers.py   # Testar normalização
├── test_loaders.py       # Testar carga no banco
└── test_reporters.py     # Testar geração de relatórios
```

**Framework**: pytest
**Tempo**: 8-10 horas para cobertura completa

---

## 📈 Roadmap

### Semana 1 (21-22/11/2025)
- [ ] **Issue #1**: Decidir e implementar solução de parâmetros
- [ ] **Issue #4**: Implementar interface básica Flask
- [ ] Testar com 42 novos relés
- [ ] Gerar relatórios completos

### Semana 2 (25-29/11/2025)
- [ ] **Issue #2**: Implementar identificação ANSI codes
- [ ] **Issue #3**: Testar performance, otimizar se necessário
- [ ] **Issue #5**: Ajustar níveis de log
- [ ] **Issue #6**: Implementar validação de inputs

### Semana 3 (02-06/12/2025)
- [ ] **Issue #7**: Implementar testes automatizados
- [ ] Documentação completa
- [ ] Deploy em ambiente de produção

---

## 🔗 Referências

- [Plano de Trabalho Amanhã](./PLANO_TRABALHO_AMANHA.md)
- [Sistema de Relatórios](./SISTEMA_RELATORIOS.md)
- [README Principal](../README.md)
- [Database Schema](../docker/postgres/init.sql)
