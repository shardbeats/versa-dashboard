YOUTUBE_VIDEO_PERFORMANCE_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.youtube_video_performance`
AS

SELECT
    d.video_id,
    d.title,
    d.beat_name,
    d.published_at,
    d.duration_seconds,

    f.views,
    f.likes,
    f.comments,
    f.watch_time_minutes,
    f.average_view_duration_seconds,
    f.average_view_percentage,
    f.subscribers_gained,
    f.subscribers_lost,
    f.snapshot_timestamp

FROM `versa-dashboard.silver.dim_youtube_video` AS d

INNER JOIN
    `versa-dashboard.silver.fact_youtube_video_metrics` AS f
    USING (video_id)
"""


MANUAL_BEATSTARS_OVERRIDES_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.manual_beatstars_overrides`
AS

SELECT
    'Xcsz6v0JjOY' AS youtube_video_id,
    'Walk My Choppa' AS beatstars_product_name,
    1330 AS beatstars_quantity
"""


BEATSTARS_SALES_PERFORMANCE_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.beatstars_sales_performance`
AS

SELECT
    product_name,
    product_type,
    quantity,
    gross_amount,
    discounts,
    collab_amount,
    beatstars_fee,
    net_revenue

FROM `versa-dashboard.silver.sales_summary`
"""


DIM_BEAT_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.dim_beat`
AS

WITH youtube_beats AS (
    SELECT
        video_id,
        title,
        beat_name,
        published_at
    FROM `versa-dashboard.silver.dim_youtube_video`
    WHERE
        is_short = FALSE
        AND published_at >= TIMESTAMP('2020-03-01')
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
    FROM `versa-dashboard.gold.beatstars_sales_performance`
    WHERE product_type = 'track'
    GROUP BY product_name
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
        overrides.beatstars_product_name,
        CASE
            WHEN
                yc.youtube_match_count = 1
                AND bs.beatstars_match_count = 1
            THEN bs.product_name
            ELSE NULL
        END
    ) AS beatstars_product_name,

    COALESCE(
        overrides.beatstars_quantity,
        CASE
            WHEN
                yc.youtube_match_count = 1
                AND bs.beatstars_match_count = 1
            THEN bs.single_match_quantity
            ELSE NULL
        END
    ) AS beatstars_quantity,

    CASE
        WHEN overrides.youtube_video_id IS NOT NULL
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

LEFT JOIN
    `versa-dashboard.gold.manual_beatstars_overrides`
    AS overrides
    ON y.video_id = overrides.youtube_video_id
"""


CROSS_PLATFORM_BEAT_PERFORMANCE_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.cross_platform_beat_performance`
AS

SELECT
    b.beat_key,
    b.beat_name,
    b.match_status,
    b.published_at,

    y.views,
    y.likes,
    y.comments,
    y.watch_time_minutes,
    y.average_view_duration_seconds,
    y.average_view_percentage,
    y.subscribers_gained,
    y.subscribers_lost,

    bs.quantity,
    bs.gross_amount,
    bs.discounts,
    bs.collab_amount,
    bs.beatstars_fee,
    bs.net_revenue

FROM `versa-dashboard.gold.dim_beat` AS b

LEFT JOIN
    `versa-dashboard.gold.youtube_video_performance` AS y
    ON b.youtube_video_id = y.video_id

LEFT JOIN
    `versa-dashboard.gold.beatstars_sales_performance` AS bs
    ON b.beatstars_product_name = bs.product_name
    AND b.beatstars_quantity = bs.quantity

WHERE b.match_status IN ('exact', 'manual')
"""