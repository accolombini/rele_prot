-- ============================================================
-- VIEWS PARA SISTEMA DE RELATÓRIOS - ProtecAI
-- Criado: 21/11/2025
-- ============================================================

-- REL01: Fabricantes de Relés
CREATE OR REPLACE VIEW protec_ai.vw_manufacturers_summary AS
SELECT 
    m.id as manufacturer_id,
    m.name as manufacturer_name,
    COUNT(DISTINCT rm.id) as total_models,
    COUNT(DISTINCT r.id) as total_relays
FROM protec_ai.manufacturers m
LEFT JOIN protec_ai.relay_models rm ON m.id = rm.manufacturer_id
LEFT JOIN protec_ai.relays r ON rm.id = r.relay_model_id
GROUP BY m.id, m.name
ORDER BY total_relays DESC, m.name;

-- REL02: Setpoints Críticos
CREATE OR REPLACE VIEW protec_ai.vw_critical_setpoints AS
SELECT 
    r.id as id_rele,
    r.bay_identifier as barra,
    m.name as fabricante,
    rm.model_name as modelo,
    af.ansi_code as codigo_ansi,
    af.name as nome_funcao,
    pf.is_enabled as habilitado,
    p.parameter_name as parametro,
    p.parameter_value as valor,
    p.parameter_unit as unidade,
    p.parameter_type as tipo_parametro
FROM protec_ai.relays r
JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.id
JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.id
JOIN protec_ai.protection_functions pf ON r.id = pf.relay_id
JOIN protec_ai.ansi_functions af ON pf.ansi_function_id = af.id
JOIN protec_ai.parameters p ON pf.id = p.protection_function_id
WHERE p.parameter_type IN ('Current', 'Voltage', 'Time')
  AND af.ansi_code != 'Unknown'
ORDER BY barra, codigo_ansi, parametro;

-- REL03: Tipos de Relés
CREATE OR REPLACE VIEW protec_ai.vw_relay_types_summary AS
SELECT 
    COALESCE(r.relay_type, 'Não Especificado') as relay_type,
    COUNT(DISTINCT r.id) as total_relays,
    COUNT(DISTINCT r.relay_model_id) as total_models,
    STRING_AGG(DISTINCT m.name, ', ' ORDER BY m.name) as manufacturers
FROM protec_ai.relays r
LEFT JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.id
LEFT JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.id
GROUP BY COALESCE(r.relay_type, 'Não Especificado')
ORDER BY total_relays DESC;

-- REL04: Relés por Fabricante
CREATE OR REPLACE VIEW protec_ai.vw_relays_by_manufacturer AS
SELECT 
    m.name as fabricante,
    rm.model_name as modelo,
    r.id as id_rele,
    r.bay_identifier as barra,
    r.relay_type as tipo_rele,
    COALESCE(CAST(r.voltage_class_kv AS VARCHAR), 'Dados_N_Forn') as classe_tensao_kv,
    COUNT(DISTINCT pf.id) as total_protecoes
FROM protec_ai.manufacturers m
JOIN protec_ai.relay_models rm ON m.id = rm.manufacturer_id
JOIN protec_ai.relays r ON rm.id = r.relay_model_id
LEFT JOIN protec_ai.protection_functions pf ON r.id = pf.relay_id
GROUP BY fabricante, modelo, id_rele, barra, tipo_rele, r.voltage_class_kv
ORDER BY fabricante, modelo, barra;

-- REL05: Funções de Proteção
CREATE OR REPLACE VIEW protec_ai.vw_protection_functions_summary AS
SELECT 
    af.ansi_code as codigo_ansi,
    CASE 
        WHEN af.name = 'Negative Sequence Overcurrent' THEN 'NSOC1'
        WHEN af.name = 'Directional Ground Overcurrent' THEN 'Prot_Dir.Terra'
        ELSE af.name
    END as nome_funcao,
    COUNT(DISTINCT pf.id) as total_instancias,
    COUNT(DISTINCT r.id) as total_reles,
    STRING_AGG(
        DISTINCT 
        CASE 
            WHEN m.name = 'GENERAL ELECTRIC' THEN 'GE'
            WHEN m.name = 'SCHNEIDER ELECTRIC' THEN 'SNE'
            WHEN m.name = 'SCHWEITZER' THEN 'SEL'
            WHEN m.name = 'SIEMENS' THEN 'SIE'
            WHEN m.name = 'ABB' THEN 'ABB'
            ELSE m.name
        END, 
        E'\n'
    ) as fabricantes,
    COUNT(DISTINCT CASE WHEN pf.is_enabled = TRUE THEN pf.id END) as habilitadas,
    COUNT(DISTINCT CASE WHEN pf.is_enabled = FALSE THEN pf.id END) as desabilitadas
FROM protec_ai.ansi_functions af
LEFT JOIN protec_ai.protection_functions pf ON af.id = pf.ansi_function_id
LEFT JOIN protec_ai.relays r ON pf.relay_id = r.id
LEFT JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.id
LEFT JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.id
GROUP BY af.ansi_code, af.name
ORDER BY codigo_ansi;

-- REL06: Relés Completo
CREATE OR REPLACE VIEW protec_ai.vw_relays_complete AS
SELECT 
    r.id as relay_id,
    r.bay_identifier,
    CASE 
        WHEN r.relay_type = 'Proteção de Alimentador' THEN 'P_ALIM'
        WHEN r.relay_type = 'Proteção de Linha' THEN 'P_LIN'
        WHEN r.relay_type = 'Proteção de Motor' THEN 'P_MOT'
        WHEN r.relay_type = 'Proteção de Transformador' THEN 'P_TF'
        ELSE r.relay_type
    END as relay_type,
    r.voltage_class_kv,
    r.substation_code,
    SUBSTRING(TO_CHAR(r.config_date, 'YYYYMMDD'), 3) as config_date,
    CASE 
        WHEN m.name = 'GENERAL ELECTRIC' THEN 'GE'
        WHEN m.name = 'SCHNEIDER ELECTRIC' THEN 'SNE'
        WHEN m.name = 'SCHWEITZER' THEN 'SEL'
        WHEN m.name = 'SIEMENS' THEN 'SIE'
        WHEN m.name = 'ABB' THEN 'ABB'
        ELSE m.name
    END as manufacturer_name,
    CASE
        WHEN rm.model_name LIKE 'SEPAM S%' THEN REPLACE(REPLACE(rm.model_name, 'SEPAM ', ''), 'S', 'S')
        ELSE rm.model_name
    END as model_name,
    CASE
        -- Quebra strings longas em duas linhas após 8 caracteres
        WHEN LENGTH(REPLACE(REPLACE(r.software_version, '_', ''), ' ', '')) > 8 THEN
            SUBSTRING(REPLACE(REPLACE(r.software_version, '_', ''), ' ', ''), 1, 8) || E'\n' || 
            SUBSTRING(REPLACE(REPLACE(r.software_version, '_', ''), ' ', ''), 9)
        ELSE REPLACE(REPLACE(r.software_version, '_', ''), ' ', '')
    END as software_version,
    rm.software_version as firmware_version,
    COUNT(DISTINCT pf.id) as total_protections,
    COUNT(DISTINCT CASE WHEN pf.is_enabled = TRUE THEN pf.id END) as enabled_protections,
    COUNT(DISTINCT p.id) as total_parameters,
    COUNT(DISTINCT ct.id) as total_cts,
    COUNT(DISTINCT vt.id) as total_vts,
    r.vt_defined,
    r.vt_enabled,
    r.voltage_source,
    r.voltage_confidence
FROM protec_ai.relays r
JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.id
JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.id
LEFT JOIN protec_ai.protection_functions pf ON r.id = pf.relay_id
LEFT JOIN protec_ai.parameters p ON pf.id = p.protection_function_id
LEFT JOIN protec_ai.current_transformers ct ON r.id = ct.relay_id
LEFT JOIN protec_ai.voltage_transformers vt ON r.id = vt.relay_id
GROUP BY r.id, r.bay_identifier, r.relay_type, r.voltage_class_kv,
         r.substation_code, r.config_date, r.software_version,
         m.name, rm.model_name, rm.software_version,
         r.vt_defined, r.vt_enabled, r.voltage_source, r.voltage_confidence
ORDER BY r.bay_identifier;

-- REL07: Relés por Subestação
CREATE OR REPLACE VIEW protec_ai.vw_relays_by_substation AS
SELECT 
    COALESCE(r.substation_code, 'Não Especificado') as codigo_subestacao,
    r.bay_identifier as barra,
    CASE 
        WHEN m.name = 'GENERAL ELECTRIC' THEN 'GE'
        WHEN m.name = 'SCHNEIDER ELECTRIC' THEN 'SNE'
        WHEN m.name = 'SCHWEITZER' THEN 'SEL'
        WHEN m.name = 'SIEMENS' THEN 'SIE'
        WHEN m.name = 'ABB' THEN 'ABB'
        ELSE m.name
    END as fabricante,
    CASE
        WHEN rm.model_name LIKE 'SEPAM S%' THEN REPLACE(REPLACE(rm.model_name, 'SEPAM ', ''), 'S', 'S')
        ELSE rm.model_name
    END as modelo,
    CASE 
        WHEN r.relay_type = 'Proteção de Alimentador' THEN 'P_ALIM'
        WHEN r.relay_type = 'Proteção de Linha' THEN 'P_LIN'
        WHEN r.relay_type = 'Proteção de Motor' THEN 'P_MOT'
        WHEN r.relay_type = 'Proteção de Transformador' THEN 'P_TF'
        ELSE r.relay_type
    END as tipo_rele,
    COALESCE(CAST(r.voltage_class_kv AS VARCHAR), 'Dados_N_Forn') as classe_tensao_kv,
    COUNT(DISTINCT pf.id) as total_protecoes
FROM protec_ai.relays r
JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.id
JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.id
LEFT JOIN protec_ai.protection_functions pf ON r.id = pf.relay_id
GROUP BY codigo_subestacao, barra, m.name, rm.model_name, r.relay_type, r.voltage_class_kv
ORDER BY codigo_subestacao, barra;

-- REL08: Análise de Tensão
CREATE OR REPLACE VIEW protec_ai.vw_voltage_analysis AS
SELECT 
    r.voltage_class_kv,
    COUNT(DISTINCT r.id) as total_relays,
    COUNT(DISTINCT CASE WHEN r.vt_defined = TRUE THEN r.id END) as relays_with_vt_defined,
    COUNT(DISTINCT CASE WHEN r.vt_enabled = TRUE THEN r.id END) as relays_with_vt_enabled,
    COUNT(DISTINCT vt.id) as total_vts,
    STRING_AGG(DISTINCT r.voltage_source, ', ') as voltage_sources,
    STRING_AGG(DISTINCT r.voltage_confidence, ', ') as confidence_levels
FROM protec_ai.relays r
LEFT JOIN protec_ai.voltage_transformers vt ON r.id = vt.relay_id
GROUP BY r.voltage_class_kv
ORDER BY r.voltage_class_kv DESC NULLS LAST;

-- REL09: Parâmetros Críticos Consolidados
CREATE OR REPLACE VIEW protec_ai.vw_critical_parameters_consolidated AS
SELECT 
    r.bay_identifier as barra,
    CASE 
        WHEN m.name = 'GENERAL ELECTRIC' THEN 'GE'
        WHEN m.name = 'SCHNEIDER ELECTRIC' THEN 'SNE'
        WHEN m.name = 'SCHWEITZER' THEN 'SEL'
        WHEN m.name = 'SIEMENS' THEN 'SIE'
        WHEN m.name = 'ABB' THEN 'ABB'
        ELSE m.name
    END as fabricante,
    CASE
        WHEN rm.model_name LIKE 'SEPAM S%' THEN REPLACE(REPLACE(rm.model_name, 'SEPAM ', ''), 'S', 'S')
        WHEN rm.model_name LIKE 'P12%' THEN rm.model_name
        ELSE rm.model_name
    END as modelo,
    af.ansi_code as codigo_ansi,
    af.name as nome_funcao,
    COUNT(DISTINCT p.id) as total_parametros,
    COUNT(DISTINCT CASE WHEN p.parameter_type IN ('Current', 'Voltage', 'Time') THEN p.id END) as parametros_criticos,
    REPLACE(
        STRING_AGG(
            CASE WHEN p.parameter_type IN ('Current', 'Voltage', 'Time') 
            THEN p.parameter_name || '=' || p.parameter_value || COALESCE(' ' || p.parameter_unit, '')
            END, 
            '; ' 
            ORDER BY p.parameter_name
        ),
        '; ',
        E';\n'
    ) as lista_parametros_criticos
FROM protec_ai.relays r
JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.id
JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.id
JOIN protec_ai.protection_functions pf ON r.id = pf.relay_id
JOIN protec_ai.ansi_functions af ON pf.ansi_function_id = af.id
JOIN protec_ai.parameters p ON pf.id = p.protection_function_id
WHERE af.ansi_code != 'Unknown'
GROUP BY barra, m.name, rm.model_name, codigo_ansi, nome_funcao
HAVING COUNT(DISTINCT CASE WHEN p.parameter_type IN ('Current', 'Voltage', 'Time') THEN p.id END) > 0
ORDER BY barra, codigo_ansi;
