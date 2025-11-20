# DER - DIAGRAMA ENTIDADE-RELACIONAMENTO
## ProtecAI Database - 3FN Normalizada

**Data:** 20/11/2025  
**Schema:** `protec_ai`  
**Versão:** FASE 3 - Com metadados completos

---

## 📊 TABELAS PRINCIPAIS (3FN)

### 1. **manufacturers** (Fabricantes)
```sql
id                SERIAL PRIMARY KEY
name              VARCHAR(100) NOT NULL UNIQUE
country           VARCHAR(50)
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Propósito:** Cadastro de fabricantes de relés (1FN - Elimina repetição de dados)  
**Dados iniciais:** SCHNEIDER ELECTRIC, GENERAL ELECTRIC

---

### 2. **relay_models** (Modelos de Relés)
```sql
id                SERIAL PRIMARY KEY
manufacturer_id   INTEGER NOT NULL → manufacturers(id)
model_name        VARCHAR(50) NOT NULL
model_series      VARCHAR(50)
software_version  VARCHAR(50)
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
UNIQUE(manufacturer_id, model_name)
```
**Propósito:** Catálogo de modelos (2FN - Dependência funcional completa)  
**Exemplos:** P122, P220, P922, S40

---

### 3. **substations** (Subestações)
```sql
id                SERIAL PRIMARY KEY
code              VARCHAR(20) NOT NULL UNIQUE
name              VARCHAR(200)
voltage_level_kv  DECIMAL(10, 2)
location          VARCHAR(200)
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Propósito:** Cadastro de subestações (1FN)  
**Códigos:** MF, MK, etc

---

### 4. **relays** (Relés - Tabela Central) ⭐
```sql
id                    SERIAL PRIMARY KEY
relay_model_id        INTEGER NOT NULL → relay_models(id)
substation_id         INTEGER → substations(id)
serial_number         VARCHAR(100)
plant_reference       VARCHAR(100)
model_number          VARCHAR(100)
bay_identifier        VARCHAR(50)
element_identifier    VARCHAR(50)
parametrization_date  DATE
frequency_hz          DECIMAL(5, 2)

-- FASE 3 - Novos campos
relay_type            VARCHAR(100)        -- Tipo: Alimentador, Motor, Linha, etc
voltage_class_kv      DECIMAL(10, 2)      -- Classe de tensão (do VT primário)
vt_defined            BOOLEAN DEFAULT FALSE -- VT existe no documento?
vt_enabled            BOOLEAN              -- VT está habilitado?
voltage_source        VARCHAR(30)          -- doc | barras_mapping | manual
voltage_confidence    DECIMAL(3, 2)        -- 0.0 a 1.0
substation_code       VARCHAR(20)          -- Código da subestação (MF, MK)
config_date           DATE                 -- Data de configuração
software_version      VARCHAR(100)         -- Versão firmware

created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Propósito:** Registro individual de cada relé instalado (3FN - Sem dependências transitivas)

---

### 5. **current_transformers** (Transformadores de Corrente)
```sql
id                   SERIAL PRIMARY KEY
relay_id             INTEGER NOT NULL → relays(id) ON DELETE CASCADE
tc_type              VARCHAR(50) NOT NULL    -- Phase, Ground, Residual, SEF
primary_rating_a     DECIMAL(10, 2) NOT NULL
secondary_rating_a   DECIMAL(10, 2) NOT NULL
ratio                VARCHAR(50)
burden               VARCHAR(50)
accuracy_class       VARCHAR(20)
created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Propósito:** TCs associados a cada relé (3FN - Relação 1:N)

---

### 6. **voltage_transformers** (Transformadores de Potencial)
```sql
id                   SERIAL PRIMARY KEY
relay_id             INTEGER NOT NULL → relays(id) ON DELETE CASCADE
vt_type              VARCHAR(50) NOT NULL    -- Main, Check Sync, Residual, NVD
primary_rating_v     DECIMAL(10, 2) NOT NULL
secondary_rating_v   DECIMAL(10, 2) NOT NULL
ratio                VARCHAR(50)
connection_type      VARCHAR(50)
location             VARCHAR(50)
vt_enabled           BOOLEAN DEFAULT TRUE    -- FASE 3
created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Propósito:** TPs associados a cada relé (3FN - Relação 1:N)

---

### 7. **ansi_functions** (Funções ANSI)
```sql
id                SERIAL PRIMARY KEY
ansi_code         VARCHAR(10) NOT NULL UNIQUE
name              VARCHAR(200) NOT NULL
description       TEXT
category          VARCHAR(100)
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Propósito:** Catálogo de funções de proteção ANSI (1FN)  
**Exemplos:** 50, 51, 87, 27, 59, 21, 67, 81

---

### 8. **protection_functions** (Funções Configuradas)
```sql
id                SERIAL PRIMARY KEY
relay_id          INTEGER NOT NULL → relays(id) ON DELETE CASCADE
ansi_function_id  INTEGER NOT NULL → ansi_functions(id)
function_label    VARCHAR(100)
is_enabled        BOOLEAN NOT NULL DEFAULT FALSE
setting_group     INTEGER
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
UNIQUE(relay_id, ansi_function_id, function_label, setting_group)
```
**Propósito:** Funções habilitadas em cada relé (3FN - Relação N:M)

---

### 9. **parameters** (Parâmetros de Proteção)
```sql
id                      SERIAL PRIMARY KEY
protection_function_id  INTEGER NOT NULL → protection_functions(id) ON DELETE CASCADE
parameter_code          VARCHAR(50) NOT NULL
parameter_name          VARCHAR(200) NOT NULL
parameter_value         TEXT NOT NULL
parameter_unit          VARCHAR(50)
parameter_type          VARCHAR(50)  -- setpoint, delay, curve, logic, mode
created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Propósito:** Configurações detalhadas de cada função (3FN)

---

### 10. **processing_log** (Log de Processamento)
```sql
id                SERIAL PRIMARY KEY
file_name         VARCHAR(255) NOT NULL
file_path         TEXT NOT NULL
file_type         VARCHAR(20) NOT NULL      -- PDF, S40
file_hash         VARCHAR(64) NOT NULL UNIQUE
manufacturer      VARCHAR(100)
relay_model       VARCHAR(50)
status            VARCHAR(50) NOT NULL       -- SUCCESS, ERROR, DUPLICATE
error_message     TEXT
records_inserted  INTEGER DEFAULT 0
processed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Propósito:** Auditoria e controle de duplicatas

---

## 🔗 RELACIONAMENTOS

```
manufacturers (1) ────< (N) relay_models
relay_models (1) ─────< (N) relays
substations (1) ──────< (N) relays

relays (1) ───────────< (N) current_transformers
relays (1) ───────────< (N) voltage_transformers
relays (1) ───────────< (N) protection_functions

ansi_functions (1) ───< (N) protection_functions
protection_functions (1) ─< (N) parameters
```

**Cardinalidades:**
- 1 fabricante → N modelos
- 1 modelo → N relés
- 1 subestação → N relés
- 1 relé → 0..N TCs, 0..N TPs, 0..N funções
- 1 função ANSI → N instâncias configuradas
- 1 função configurada → N parâmetros

---

## 📋 VIEWS PARA RELATÓRIOS

### **vw_relays_complete** (Relatórios 6, 8, 9)
Visão completa com: relay info, stats (CTs, VTs, proteções), códigos ANSI

### **vw_manufacturers_summary** (Relatório 1)
Fabricantes com contagem de modelos e relés

### **vw_relay_types_summary** (Relatório 3)
Tipos de relés (Alimentador, Motor, Linha, Transformador) com contagens

### **vw_relays_by_manufacturer** (Relatório 4)
Relés agrupados por fabricante e modelo

### **vw_protection_functions_summary** (Relatório 5)
Funções ANSI com contagem de relés habilitados/desabilitados

### **vw_relays_by_substation** (Relatório 7)
Relés agrupados por subestação/barra

### **vw_critical_setpoints** (Relatório 2)
Setpoints críticos de proteções principais (50, 51, 87, 27, 59)

---

## 🔍 ÍNDICES DE PERFORMANCE

```sql
-- Relays
idx_relays_model             ON relays(relay_model_id)
idx_relays_substation        ON relays(substation_id)
idx_relays_bay               ON relays(bay_identifier)
idx_relays_type              ON relays(relay_type)              -- FASE 3
idx_relays_voltage_class     ON relays(voltage_class_kv)        -- FASE 3
idx_relays_substation_code   ON relays(substation_code)         -- FASE 3
idx_relays_vt_defined        ON relays(vt_defined)              -- FASE 3

-- Relationships
idx_ct_relay                 ON current_transformers(relay_id)
idx_vt_relay                 ON voltage_transformers(relay_id)
idx_prot_func_relay          ON protection_functions(relay_id)
idx_prot_func_ansi           ON protection_functions(ansi_function_id)
idx_params_prot_func         ON parameters(protection_function_id)

-- Processing
idx_processing_log_hash      ON processing_log(file_hash)
idx_processing_log_status    ON processing_log(status)
idx_processing_log_date      ON processing_log(processed_at)
```

---

## ✅ CONFORMIDADE 3FN

### **1FN (Primeira Forma Normal):** ✅
- ✅ Valores atômicos (não há listas ou arrays em campos)
- ✅ Cada coluna contém apenas um valor
- ✅ Sem grupos repetitivos

### **2FN (Segunda Forma Normal):** ✅
- ✅ Está em 1FN
- ✅ Todos os atributos não-chave dependem COMPLETAMENTE da chave primária
- ✅ Exemplos:
  - `relay_models.model_name` depende de (manufacturer_id, model_name)
  - `parameters` dependem de protection_function_id (não apenas relay_id)

### **3FN (Terceira Forma Normal):** ✅
- ✅ Está em 2FN
- ✅ Não há dependências transitivas
- ✅ Atributos não-chave não dependem de outros atributos não-chave
- ✅ Exemplos:
  - Fabricante separado de modelo (sem redundância)
  - Subestação separada de relé
  - ANSI functions separadas de protection_functions

---

## 🎯 COMPATIBILIDADE COM FASE 2

Os dados normalizados da FASE 2 (CSVs) mapeiam perfeitamente para o schema 3FN:

| CSV FASE 2 | Tabela(s) Destino |
|------------|-------------------|
| `all_relays_info.csv` | `relays` + `relay_models` + `manufacturers` + `substations` |
| `all_ct_data.csv` | `current_transformers` |
| `all_vt_data.csv` | `voltage_transformers` |
| `all_protections.csv` | `protection_functions` + `ansi_functions` |
| `all_parameters.csv` | `parameters` |

---

## 📊 DADOS ATUAIS (FASE 3)

**Relés processados:** 8  
**TCs:** 6  
**TPs:** 5  
**Proteções:** 77  
**Parâmetros:** 3.692  

**Modelos:** P122, P220, P241, P922, P143, SEPAM S40  
**Fabricantes:** Schneider Electric, General Electric  
**Subestações:** MF, MK  
**Classes de tensão:** 13.8 kV, 20.0 kV  

---

**Próximos passos:** Implementar loader Python para popular o banco com os dados da FASE 2! 🚀
