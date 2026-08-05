WITH youtube_beats AS (

    SELECT
        video_id,
        title,
        beat_name,
        published_at

    FROM {{ source('silver', 'dim_youtube_video') }}

    WHERE is_short = FALSE

),

youtube_name_counts AS (

    SELECT
        beat_name,
        COUNT(*) AS youtube_match_count

    FROM youtube_beats

    GROUP BY beat_name

),

beatstars_beats AS (

    SELECT
        product_name,
        COUNT(*) AS beatstars_match_count,
        ANY_VALUE(quantity) AS single_match_quantity

    FROM {{ ref('beatstars_sales_performance') }}

    WHERE product_type = 'track'

    GROUP BY product_name

),

manual_matches AS (

    SELECT
        youtube_video_id,
        source_product_name AS beatstars_product_name,
        source_quantity AS beatstars_quantity

    FROM {{ ref('beatstars_matching_rules') }}

    WHERE rule_type = 'manual_match'

)

SELECT
    y.video_id AS beat_key,
    y.beat_name,
    y.video_id AS youtube_video_id,
    y.title AS youtube_title,
    y.published_at,

    yc.youtube_match_count,

    COALESCE(
        bs.beatstars_match_count,
        0
    ) AS beatstars_match_count,

    COALESCE(
        manual.beatstars_product_name,
        CASE
            WHEN
                yc.youtube_match_count = 1
                AND bs.beatstars_match_count = 1
            THEN bs.product_name
            ELSE NULL
        END
    ) AS beatstars_product_name,

    COALESCE(
        manual.beatstars_quantity,
        CASE
            WHEN
                yc.youtube_match_count = 1
                AND bs.beatstars_match_count = 1
            THEN bs.single_match_quantity
            ELSE NULL
        END
    ) AS beatstars_quantity,

    CASE
        WHEN manual.youtube_video_id IS NOT NULL
            THEN 'manual'

        WHEN bs.product_name IS NULL
            THEN 'unmatched'

        WHEN
            yc.youtube_match_count = 1
            AND bs.beatstars_match_count = 1
        THEN 'exact'

        ELSE 'ambiguous'
    END AS match_status

FROM youtube_beats AS y

LEFT JOIN youtube_name_counts AS yc
    USING (beat_name)

LEFT JOIN beatstars_beats AS bs
    ON y.beat_name = bs.product_name

LEFT JOIN manual_matches AS manual
    ON y.video_id = manual.youtube_video_id