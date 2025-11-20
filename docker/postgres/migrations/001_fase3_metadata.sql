-- ProtecAI Database Schema - FASE 3 Updated
-- Schema: protec_ai
-- 3NF Normalized Structure with Enhanced Metadata

SET search_path TO protec_ai;

-- =============================================================================
-- SCHEMA ALTERATIONS FOR FASE 3
-- =============================================================================

-- Add new columns to relays table
ALTER TABLE relays 
    ADD COLUMN IF NOT EXISTS relay_type VARCHAR(100),
    ADD COLUMN IF NOT EXISTS voltage_class_kv DECIMAL(10, 2),
    ADD COLUMN IF NOT EXISTS vt_defined BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS vt_enabled BOOLEAN,
    ADD COLUMN IF NOT EXISTS voltage_source VARCHAR(30),
    ADD COLUMN IF NOT EXISTS voltage_confidence DECIMAL(3, 2),
    ADD COLUMN IF NOT EXISTS substation_code VARCHAR(20),
    ADD COLUMN IF NOT EXISTS config_date DATE,
    ADD COLUMN IF NOT EXISTS software_version VARCHAR(100);

-- Add comments for documentation
COMMENT ON COLUMN relays.relay_type IS 'Tipo de proteção: Alimentador, Motor, Linha, Transformador, etc';
COMMENT ON COLUMN relays.voltage_class_kv IS 'Classe de tensão em kV derivada do VT primário';
COMMENT ON COLUMN relays.vt_defined IS 'Indica se VT está definido no documento de configuração';
COMMENT ON COLUMN relays.vt_enabled IS 'Indica se VT está habilitado (SEPAM: EnServiceTP)';
COMMENT ON COLUMN relays.voltage_source IS 'Fonte do valor de tensão: doc, barras_mapping, setpoint59, manual';
COMMENT ON COLUMN relays.voltage_confidence IS 'Confiança no valor de tensão: 1.0 (doc) a 0.0 (incerto)';
COMMENT ON COLUMN relays.substation_code IS 'Código da subestação: MF, MK, etc';
COMMENT ON COLUMN relays.config_date IS 'Data de configuração/parametrização do relé';
COMMENT ON COLUMN relays.software_version IS 'Versão do software/firmware do relé';

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_relays_type ON relays(relay_type);
CREATE INDEX IF NOT EXISTS idx_relays_voltage_class ON relays(voltage_class_kv);
CREATE INDEX IF NOT EXISTS idx_relays_substation_code ON relays(substation_code);
CREATE INDEX IF NOT EXISTS idx_relays_vt_defined ON relays(vt_defined);

-- Add vt_enabled field to voltage_transformers
ALTER TABLE voltage_transformers
    ADD COLUMN IF NOT EXISTS vt_enabled BOOLEAN DEFAULT TRUE;

COMMENT ON COLUMN voltage_transformers.vt_enabled IS 'Indica se o VT está habilitado no relé';

-- =============================================================================
-- VIEWS FOR REPORTS
-- =============================================================================

-- View: Complete Relay Information (Report 6, 8, 9)
CREATE OR REPLACE VIEW vw_relays_complete AS
SELECT 
    r.id AS relay_id,
    r.serial_number,
    r.plant_reference,
    r.bay_identifier,
    r.element_identifier,
    r.substation_code,
    s.name AS substation_name,
    s.voltage_level_kv AS substation_voltage_kv,
    m.name AS manufacturer,
    rm.model_name,
    rm.model_series,
    r.relay_type,
    r.voltage_class_kv,
    r.vt_defined,
    r.vt_enabled,
    r.voltage_source,
    r.voltage_confidence,
    r.config_date,
    r.frequency_hz,
    r.software_version,
    COUNT(DISTINCT ct.id) AS ct_count,
    COUNT(DISTINCT vt.id) AS vt_count,
    COUNT(DISTINCT pf.id) AS protection_count,
    STRING_AGG(DISTINCT af.ansi_code, ', ' ORDER BY af.ansi_code) AS ansi_codes,
    r.created_at,
    r.updated_at
FROM relays r
LEFT JOIN relay_models rm ON r.relay_model_id = rm.id
LEFT JOIN manufacturers m ON rm.manufacturer_id = m.id
LEFT JOIN substations s ON r.substation_id = s.id
LEFT JOIN current_transformers ct ON r.id = ct.relay_id
LEFT JOIN voltage_transformers vt ON r.id = vt.relay_id
LEFT JOIN protection_functions pf ON r.id = pf.relay_id AND pf.is_enabled = TRUE
LEFT JOIN ansi_functions af ON pf.ansi_function_id = af.id
GROUP BY 
    r.id, r.serial_number, r.plant_reference, r.bay_identifier, 
    r.element_identifier, r.substation_code, s.name, s.voltage_level_kv,
    m.name, rm.model_name, rm.model_series, r.relay_type, 
    r.voltage_class_kv, r.vt_defined, r.vt_enabled, r.voltage_source,
    r.voltage_confidence, r.config_date, r.frequency_hz, r.software_version,
    r.created_at, r.updated_at;

COMMENT ON VIEW vw_relays_complete IS 'Visão completa dos relés com estatísticas para relatórios 6, 8 e 9';

-- View: Manufacturers Report (Report 1)
CREATE OR REPLACE VIEW vw_manufacturers_summary AS
SELECT 
    m.name AS manufacturer,
    m.country,
    COUNT(DISTINCT rm.id) AS model_count,
    COUNT(DISTINCT r.id) AS relay_count,
    STRING_AGG(DISTINCT rm.model_name, ', ' ORDER BY rm.model_name) AS models
FROM manufacturers m
LEFT JOIN relay_models rm ON m.id = rm.manufacturer_id
LEFT JOIN relays r ON rm.id = r.relay_model_id
GROUP BY m.id, m.name, m.country
ORDER BY relay_count DESC, m.name;

COMMENT ON VIEW vw_manufacturers_summary IS 'Relatório 1: Fabricantes de Relés';

-- View: Relay Types Report (Report 3)
CREATE OR REPLACE VIEW vw_relay_types_summary AS
SELECT 
    r.relay_type,
    COUNT(r.id) AS relay_count,
    COUNT(DISTINCT rm.model_name) AS model_count,
    STRING_AGG(DISTINCT rm.model_name, ', ' ORDER BY rm.model_name) AS models,
    STRING_AGG(DISTINCT m.name, ', ') AS manufacturers
FROM relays r
LEFT JOIN relay_models rm ON r.relay_model_id = rm.id
LEFT JOIN manufacturers m ON rm.manufacturer_id = m.id
WHERE r.relay_type IS NOT NULL
GROUP BY r.relay_type
ORDER BY relay_count DESC;

COMMENT ON VIEW vw_relay_types_summary IS 'Relatório 3: Tipos de Relés';

-- View: Relays by Manufacturer (Report 4)
CREATE OR REPLACE VIEW vw_relays_by_manufacturer AS
SELECT 
    m.name AS manufacturer,
    rm.model_name,
    r.relay_type,
    COUNT(r.id) AS relay_count,
    STRING_AGG(DISTINCT r.substation_code, ', ' ORDER BY r.substation_code) AS substations
FROM manufacturers m
JOIN relay_models rm ON m.id = rm.manufacturer_id
JOIN relays r ON rm.id = r.relay_model_id
GROUP BY m.name, rm.model_name, r.relay_type
ORDER BY m.name, relay_count DESC;

COMMENT ON VIEW vw_relays_by_manufacturer IS 'Relatório 4: Relés por Fabricante';

-- View: Protection Functions Report (Report 5)
CREATE OR REPLACE VIEW vw_protection_functions_summary AS
SELECT 
    af.ansi_code,
    af.name AS function_name,
    af.category,
    COUNT(DISTINCT pf.relay_id) AS relay_count,
    COUNT(pf.id) FILTER (WHERE pf.is_enabled = TRUE) AS enabled_count,
    COUNT(pf.id) FILTER (WHERE pf.is_enabled = FALSE) AS disabled_count,
    STRING_AGG(DISTINCT rm.model_name, ', ' ORDER BY rm.model_name) AS models
FROM ansi_functions af
LEFT JOIN protection_functions pf ON af.id = pf.ansi_function_id
LEFT JOIN relays r ON pf.relay_id = r.id
LEFT JOIN relay_models rm ON r.relay_model_id = rm.id
GROUP BY af.ansi_code, af.name, af.category
ORDER BY relay_count DESC, af.ansi_code;

COMMENT ON VIEW vw_protection_functions_summary IS 'Relatório 5: Funções de Proteção e Relés';

-- View: Relays by Substation (Report 7)
CREATE OR REPLACE VIEW vw_relays_by_substation AS
SELECT 
    COALESCE(s.code, r.substation_code, 'SEM CÓDIGO') AS substation_code,
    COALESCE(s.name, 'Não cadastrada') AS substation_name,
    s.voltage_level_kv AS substation_voltage_kv,
    COUNT(r.id) AS relay_count,
    COUNT(DISTINCT rm.model_name) AS model_count,
    COUNT(DISTINCT r.bay_identifier) AS bay_count,
    STRING_AGG(DISTINCT m.name, ', ') AS manufacturers,
    STRING_AGG(DISTINCT r.relay_type, ', ') AS relay_types
FROM relays r
LEFT JOIN substations s ON r.substation_id = s.id OR r.substation_code = s.code
LEFT JOIN relay_models rm ON r.relay_model_id = rm.id
LEFT JOIN manufacturers m ON rm.manufacturer_id = m.id
GROUP BY s.code, s.name, s.voltage_level_kv, r.substation_code
ORDER BY relay_count DESC, substation_code;

COMMENT ON VIEW vw_relays_by_substation IS 'Relatório 7: Relés por Barra/Subestação';

-- View: Critical Setpoints Report (Report 2)
CREATE OR REPLACE VIEW vw_critical_setpoints AS
SELECT 
    r.id AS relay_id,
    r.serial_number,
    r.bay_identifier,
    r.substation_code,
    m.name AS manufacturer,
    rm.model_name,
    af.ansi_code,
    af.name AS function_name,
    pf.function_label,
    p.parameter_name,
    p.parameter_value,
    p.parameter_unit,
    p.parameter_type
FROM parameters p
JOIN protection_functions pf ON p.protection_function_id = pf.id
JOIN relays r ON pf.relay_id = r.id
JOIN relay_models rm ON r.relay_model_id = rm.id
JOIN manufacturers m ON rm.manufacturer_id = m.id
JOIN ansi_functions af ON pf.ansi_function_id = af.id
WHERE 
    pf.is_enabled = TRUE
    AND p.parameter_type IN ('setpoint', 'delay', 'curve')
    AND af.ansi_code IN ('50', '51', '50N', '51N', '87', '27', '59', '21')
ORDER BY r.substation_code, r.bay_identifier, af.ansi_code, p.parameter_name;

COMMENT ON VIEW vw_critical_setpoints IS 'Relatório 2: SetPoints Críticos (proteções principais)';

-- =============================================================================
-- GRANTS
-- =============================================================================

GRANT SELECT ON ALL TABLES IN SCHEMA protec_ai TO protecai;
GRANT SELECT ON ALL VIEWS IN SCHEMA protec_ai TO protecai;
