-- ============================================================
-- SkySignal MVP — CISA Sector Mapping
-- Migration: 002_cisa_mapping.sql
-- ============================================================

CREATE TYPE cisa_sector_enum AS ENUM (
  'CHEMICAL',
  'COMMERCIAL_FACILITIES',
  'COMMUNICATIONS',
  'CRITICAL_MANUFACTURING',
  'DAMS',
  'DEFENSE_INDUSTRIAL_BASE',
  'EMERGENCY_SERVICES',
  'ENERGY',
  'FINANCIAL_SERVICES',
  'FOOD_AND_AGRICULTURE',
  'GOVERNMENT_FACILITIES',
  'HEALTHCARE_PUBLIC_HEALTH',
  'INFORMATION_TECHNOLOGY',
  'NUCLEAR',
  'TRANSPORTATION_SYSTEMS',
  'WATER_WASTEWATER'
);

-- Add CISA columns to incidents
ALTER TABLE incidents
  ADD COLUMN cisa_sector    cisa_sector_enum,
  ADD COLUMN cisa_subsector TEXT;

CREATE INDEX incidents_cisa_sector_idx ON incidents(cisa_sector);

-- ============================================================
-- SECTOR ↔ CISA MAPPING TABLE
-- ============================================================

CREATE TABLE sector_cisa_mapping (
  operational_sector  sector_enum PRIMARY KEY,
  default_cisa_sector cisa_sector_enum NOT NULL,
  cisa_subsectors     TEXT[],
  notes               TEXT
);

INSERT INTO sector_cisa_mapping
  (operational_sector, default_cisa_sector, cisa_subsectors, notes)
VALUES
  ('AVIATION',          'TRANSPORTATION_SYSTEMS',  ARRAY['Aviation'],                              'Airports, flight paths, airspace'),
  ('MILITARY',          'DEFENSE_INDUSTRIAL_BASE',  ARRAY['DoD-owned facilities'],                 'Military installations'),
  ('CRITICAL_INFRA',    'ENERGY',                   ARRAY['Electricity','Oil and Natural Gas'],    'Default; context-dependent'),
  ('BORDER_SECURITY',   'GOVERNMENT_FACILITIES',    ARRAY['Federal Facilities'],                   'CBP/DHS border operations'),
  ('CORRECTIONS',       'GOVERNMENT_FACILITIES',    ARRAY['State/Local/Tribal/Territorial'],        'Prisons, detention facilities'),
  ('LAW_ENFORCEMENT',   'EMERGENCY_SERVICES',       ARRAY['Law Enforcement'],                       'Police, federal LE agencies'),
  ('MARITIME',          'TRANSPORTATION_SYSTEMS',   ARRAY['Maritime'],                              'Ports, vessels, offshore'),
  ('GOVERNMENT',        'GOVERNMENT_FACILITIES',    ARRAY['Federal Facilities'],                    'All levels of government'),
  ('STADIUM_VENUE',     'COMMERCIAL_FACILITIES',    ARRAY['Sports Leagues','Public Assembly'],      'Events, venues, arenas'),
  ('VIP_PROTECTION',    'GOVERNMENT_FACILITIES',    ARRAY['Federal Facilities'],                    'Executive protection, diplomatic'),
  ('MEDIA',             'COMMERCIAL_FACILITIES',    ARRAY['Entertainment and Media'],               'Broadcast, news, film'),
  ('NATURE_RESERVE',    'FOOD_AND_AGRICULTURE',     ARRAY['Farms'],                                 'Parks, wilderness, agricultural land'),
  ('ENTERPRISE',        'COMMERCIAL_FACILITIES',    ARRAY['Real Estate'],                           'Default; refine by sub-type'),
  ('RESIDENTIAL',       'COMMERCIAL_FACILITIES',    ARRAY['Real Estate'],                           'Neighborhoods, private property'),
  ('TRANSPORTATION',    'TRANSPORTATION_SYSTEMS',   ARRAY['Highway and Motor Carrier','Freight Rail'], 'Non-aviation transport'),
  ('HEALTHCARE',        'HEALTHCARE_PUBLIC_HEALTH', ARRAY['Direct care facilities'],                'Hospitals, clinics'),
  ('EDUCATION',         'GOVERNMENT_FACILITIES',    ARRAY['Education Facilities'],                  'Schools, universities'),
  ('LOCAL_GOVERNMENTAL','GOVERNMENT_FACILITIES',    ARRAY['State/Local/Tribal/Territorial'],        'Municipal, county, tribal');

-- ============================================================
-- AUTO-ASSIGN CISA SECTOR TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION auto_assign_cisa_sector()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.operational_sector IS NOT NULL AND NEW.cisa_sector IS NULL THEN
    SELECT default_cisa_sector INTO NEW.cisa_sector
    FROM sector_cisa_mapping
    WHERE operational_sector = NEW.operational_sector;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER incidents_auto_cisa
  BEFORE INSERT OR UPDATE ON incidents
  FOR EACH ROW EXECUTE FUNCTION auto_assign_cisa_sector();
