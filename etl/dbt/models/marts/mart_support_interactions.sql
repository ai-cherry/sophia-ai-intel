-- Support interactions data mart
{{ config(
    materialized='table'
) }}

SELECT 
    event_id,
    account_id,
    channel,
    ts,
    subject,
    body,
    url,
    metadata
FROM {{ ref('stg_support_events') }}