{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'gong_calls') }}
),

cleaned AS (
    SELECT
        call_id,
        TO_DATE(call_date, 'YYYY-MM-DD') as call_date,
        EXTRACT(EPOCH FROM duration::interval) / 60 as duration_minutes,
        participant_count,
        call_title,
        created_at,
        updated_at
    FROM source
    WHERE call_id IS NOT NULL
)

SELECT * FROM cleaned