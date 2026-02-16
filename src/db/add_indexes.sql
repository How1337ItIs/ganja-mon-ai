-- Database Performance Optimization
-- Add indexes for common queries
-- ====================================

-- Sensor readings: queries by timestamp
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_grow_day ON sensor_readings(grow_session_id, grow_day);

-- Device states: queries by timestamp
CREATE INDEX IF NOT EXISTS idx_device_states_timestamp ON device_states(timestamp DESC);

-- AI decisions: queries by day and timestamp
CREATE INDEX IF NOT EXISTS idx_ai_decisions_grow_day ON ai_decisions(grow_session_id, grow_day);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_timestamp ON ai_decisions(timestamp DESC);

-- Action logs: queries by timestamp and type
CREATE INDEX IF NOT EXISTS idx_action_logs_timestamp ON action_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_action_logs_type ON action_logs(action_type, timestamp DESC);

-- Grow sessions: active session lookups
CREATE INDEX IF NOT EXISTS idx_grow_sessions_active ON grow_sessions(is_active) WHERE is_active = 1;

-- Episodic memory: queries by timestamp
CREATE INDEX IF NOT EXISTS idx_episodic_memory_timestamp ON episodic_memory(timestamp DESC);

-- Leads: email lookups
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);

-- Water predictions: queries by timestamp
CREATE INDEX IF NOT EXISTS idx_water_predictions_timestamp ON water_predictions(predicted_at DESC);

-- Composite indexes for common joins
CREATE INDEX IF NOT EXISTS idx_sensors_session_time ON sensor_readings(grow_session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_devices_session_time ON device_states(grow_session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_actions_decision ON action_logs(ai_decision_id, timestamp);
