-- ProtecAI Database Initialization Script
-- Schema: protec_ai
-- 3NF Normalized Structure

-- Create schema
CREATE SCHEMA IF NOT EXISTS protec_ai;

-- Set search path
SET search_path TO protec_ai;

-- Table: manufacturers
CREATE TABLE IF NOT EXISTS manufacturers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: relay_models
CREATE TABLE IF NOT EXISTS relay_models (
    id SERIAL PRIMARY KEY,
    manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(id) ON DELETE RESTRICT,
    model_name VARCHAR(50) NOT NULL,
    model_series VARCHAR(50),
    software_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manufacturer_id, model_name)
);

-- Table: substations
CREATE TABLE IF NOT EXISTS substations (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200),
    voltage_level_kv DECIMAL(10, 2),
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: relays
CREATE TABLE IF NOT EXISTS relays (
    id SERIAL PRIMARY KEY,
    relay_model_id INTEGER NOT NULL REFERENCES relay_models(id) ON DELETE RESTRICT,
    substation_id INTEGER REFERENCES substations(id) ON DELETE SET NULL,
    bay_identifier VARCHAR(50),
    parametrization_date DATE,
    frequency_hz DECIMAL(5, 2),
    relay_type VARCHAR(50),
    voltage_class_kv DECIMAL(10, 2),
    vt_defined BOOLEAN DEFAULT FALSE,
    vt_enabled BOOLEAN DEFAULT FALSE,
    voltage_source VARCHAR(50),
    voltage_confidence VARCHAR(50),
    substation_code VARCHAR(50),
    config_date DATE,
    software_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: current_transformers (TCs)
CREATE TABLE IF NOT EXISTS current_transformers (
    id SERIAL PRIMARY KEY,
    relay_id INTEGER NOT NULL REFERENCES relays(id) ON DELETE CASCADE,
    tc_type VARCHAR(50) NOT NULL, -- 'Phase', 'Ground', 'Residual', 'SEF'
    primary_rating_a DECIMAL(10, 2) NOT NULL,
    secondary_rating_a DECIMAL(10, 2) NOT NULL,
    ratio VARCHAR(50),
    burden VARCHAR(50),
    accuracy_class VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: voltage_transformers (TPs)
CREATE TABLE IF NOT EXISTS voltage_transformers (
    id SERIAL PRIMARY KEY,
    relay_id INTEGER NOT NULL REFERENCES relays(id) ON DELETE CASCADE,
    vt_type VARCHAR(50) NOT NULL, -- 'Main', 'Check Sync', 'Residual', 'NVD'
    primary_rating_v DECIMAL(10, 2) NOT NULL,
    secondary_rating_v DECIMAL(10, 2) NOT NULL,
    ratio VARCHAR(50),
    vt_enabled BOOLEAN DEFAULT FALSE,
    connection_type VARCHAR(50),
    location VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: ansi_functions
CREATE TABLE IF NOT EXISTS ansi_functions (
    id SERIAL PRIMARY KEY,
    ansi_code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: protection_functions
CREATE TABLE IF NOT EXISTS protection_functions (
    id SERIAL PRIMARY KEY,
    relay_id INTEGER NOT NULL REFERENCES relays(id) ON DELETE CASCADE,
    ansi_function_id INTEGER NOT NULL REFERENCES ansi_functions(id) ON DELETE RESTRICT,
    function_label VARCHAR(100),
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    setting_group INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(relay_id, ansi_function_id, function_label, setting_group)
);

-- Table: parameters
CREATE TABLE IF NOT EXISTS parameters (
    id SERIAL PRIMARY KEY,
    protection_function_id INTEGER NOT NULL REFERENCES protection_functions(id) ON DELETE CASCADE,
    parameter_code VARCHAR(50) NOT NULL,
    parameter_name VARCHAR(200) NOT NULL,
    parameter_value TEXT NOT NULL,
    parameter_unit VARCHAR(50),
    parameter_type VARCHAR(50), -- 'setpoint', 'delay', 'curve', 'logic', 'mode'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: processing_log
CREATE TABLE IF NOT EXISTS processing_log (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(20) NOT NULL, -- 'PDF', 'S40'
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    manufacturer VARCHAR(100),
    relay_model VARCHAR(50),
    status VARCHAR(50) NOT NULL, -- 'SUCCESS', 'ERROR', 'DUPLICATE', 'SKIPPED'
    error_message TEXT,
    records_inserted INTEGER DEFAULT 0,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_relays_model ON relays(relay_model_id);
CREATE INDEX idx_relays_substation ON relays(substation_id);
CREATE INDEX idx_relays_bay ON relays(bay_identifier);
CREATE INDEX idx_ct_relay ON current_transformers(relay_id);
CREATE INDEX idx_vt_relay ON voltage_transformers(relay_id);
CREATE INDEX idx_prot_func_relay ON protection_functions(relay_id);
CREATE INDEX idx_prot_func_ansi ON protection_functions(ansi_function_id);
CREATE INDEX idx_params_prot_func ON parameters(protection_function_id);
CREATE INDEX idx_processing_log_hash ON processing_log(file_hash);
CREATE INDEX idx_processing_log_status ON processing_log(status);
CREATE INDEX idx_processing_log_date ON processing_log(processed_at);

-- Insert initial manufacturers
INSERT INTO manufacturers (name, country) VALUES
    ('SCHNEIDER ELECTRIC', 'France'),
    ('GENERAL ELECTRIC', 'USA')
ON CONFLICT (name) DO NOTHING;

-- Insert initial ANSI functions
INSERT INTO ansi_functions (ansi_code, name, description, category) VALUES
    ('21', 'Distance Protection', 'Impedance-based protection', 'Distance'),
    ('27', 'Undervoltage', 'Detects undervoltage conditions', 'Voltage'),
    ('32', 'Reverse Power', 'Detects reverse power flow', 'Power'),
    ('37', 'Undercurrent', 'Detects undercurrent conditions', 'Current'),
    ('40', 'Loss of Field', 'Detects loss of excitation', 'Generator'),
    ('46', 'Negative Sequence Overcurrent', 'Unbalanced load protection', 'Current'),
    ('47', 'Negative Sequence Overvoltage', 'Voltage unbalance protection', 'Voltage'),
    ('49', 'Thermal Overload', 'Thermal protection', 'Thermal'),
    ('50', 'Instantaneous Overcurrent', 'Fast overcurrent protection', 'Current'),
    ('51', 'Time Overcurrent', 'Delayed overcurrent protection', 'Current'),
    ('50N', 'Instantaneous Ground Overcurrent', 'Fast ground fault protection', 'Current'),
    ('51N', 'Time Ground Overcurrent', 'Delayed ground fault protection', 'Current'),
    ('50BF', 'Breaker Failure', 'Circuit breaker failure protection', 'Breaker'),
    ('59', 'Overvoltage', 'Detects overvoltage conditions', 'Voltage'),
    ('59N', 'Residual Overvoltage', 'Ground overvoltage detection', 'Voltage'),
    ('67', 'Directional Overcurrent', 'Directional current protection', 'Current'),
    ('67N', 'Directional Ground Overcurrent', 'Directional ground protection', 'Current'),
    ('78', 'Out of Step', 'Loss of synchronism protection', 'Synchronism'),
    ('81', 'Frequency', 'Under/over frequency protection', 'Frequency'),
    ('87', 'Differential', 'Differential protection', 'Differential')
ON CONFLICT (ansi_code) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA protec_ai TO protecai;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA protec_ai TO protecai;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA protec_ai TO protecai;
