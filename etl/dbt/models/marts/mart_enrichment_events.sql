-- Enrichment events data mart
{{ config(
    materialized='table'
) }}

SELECT 
    event_id,
    provider,
    kind,
    account_id,
    person_id,
    company_id,
    payload,
    ts
FROM {{ ref('stg_enrichment_data') }}