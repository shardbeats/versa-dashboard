WITH item_level AS (

    SELECT
        invoice_number,
        item_sequence,
        sold_at,
        source,
        total,
        sale_type,
        beat_title,

        CASE
            WHEN license LIKE 'MP3 Lease%' THEN 'MP3 Lease'
            WHEN license LIKE 'WAV Lease%' THEN 'WAV Lease'
            WHEN license LIKE 'Unlimited Lease%' THEN 'Unlimited Lease'
            WHEN license IS NULL THEN NULL
            ELSE license
        END AS license_label

    FROM {{ source('silver', 'stg_beatstars_email_sales') }}

),

order_level AS (

    SELECT
        invoice_number,
        MIN(sold_at) AS sold_at,
        ANY_VALUE(source) AS source,
        ANY_VALUE(total) AS order_total,
        ANY_VALUE(sale_type) AS sale_type,

        COUNT(*) AS beat_count,

        ARRAY_AGG(
            beat_title
            ORDER BY item_sequence
        ) AS beat_titles,

        ARRAY_AGG(
            license_label
            IGNORE NULLS
            ORDER BY item_sequence
        ) AS licenses

    FROM item_level

    GROUP BY invoice_number

)

SELECT
    invoice_number,
    sold_at,
    source,
    order_total,
    sale_type,
    beat_count,
    beat_titles,
    licenses,

    CASE
        WHEN beat_count = 1 THEN beat_titles[SAFE_OFFSET(0)]
        ELSE CONCAT(
            beat_titles[SAFE_OFFSET(0)],
            ' + ',
            CAST(beat_count - 1 AS STRING),
            ' more'
        )
    END AS display_beat,

    licenses[SAFE_OFFSET(0)] AS display_license,

    CASE
        WHEN source = 'pro_page' THEN 'Pro Page'
        WHEN source = 'marketplace' THEN 'Marketplace'
        ELSE source
    END AS display_source,

    CASE
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), sold_at, HOUR) < 24 THEN
            CONCAT(
                CAST(
                    TIMESTAMP_DIFF(
                        CURRENT_TIMESTAMP(),
                        sold_at,
                        HOUR
                    ) AS STRING
                ),
                ' hours ago'
            )
        ELSE
            CONCAT(
                CAST(
                    TIMESTAMP_DIFF(
                        CURRENT_TIMESTAMP(),
                        sold_at,
                        DAY
                    ) AS STRING
                ),
                ' days ago'
            )
    END AS display_time

FROM order_level

ORDER BY sold_at DESC

LIMIT 5