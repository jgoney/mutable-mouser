-- Mouser NO,
-- Mfr.NO,
-- Manufacturer,
-- Customer NO,
-- Description,
-- RoHS,
-- Lifecycle,
-- ORDER Qty.,
-- Price (EUR),
-- Ext:(EUR)

CREATE TABLE items
(
  mouser_number       TEXT PRIMARY KEY NOT NULL,
  manufacturer_number TEXT,
  manufacturer        TEXT,
  customer_number     TEXT,
  description         TEXT,
  rohs                TEXT,
  lifecycle           TEXT,
  qty                 INTEGER,
  price               TEXT,
  total               TEXT
);
