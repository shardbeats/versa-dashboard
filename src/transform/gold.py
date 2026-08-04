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
    f.estimated_revenue,
    f.snapshot_timestamp

FROM `versa-dashboard.silver.dim_youtube_video` AS d

INNER JOIN
    `versa-dashboard.silver.fact_youtube_video_metrics` AS f
    USING (video_id)
"""


BEATSTARS_MATCHING_RULES_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.beatstars_matching_rules`
AS

SELECT
    'manual_match' AS rule_type,
    'Xcsz6v0JjOY' AS youtube_video_id,
    'Walk My Choppa' AS source_product_name,
    1330 AS source_quantity,
    'Walk My Choppa' AS canonical_product_name

UNION ALL

SELECT
    'merge',
    NULL,
    'In My Cup',
    43,
    'In My Cup'

UNION ALL

SELECT
    'merge',
    NULL,
    'In My Cup',
    3,
    'In My Cup'
"""


BEATSTARS_SALES_PERFORMANCE_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.beatstars_sales_performance`
AS

WITH merge_rules AS (
    SELECT
        source_product_name,
        source_quantity,
        canonical_product_name
    FROM `versa-dashboard.gold.beatstars_matching_rules`
    WHERE rule_type = 'merge'
),

regular_sales AS (
    SELECT
        sales.product_name,
        sales.product_type,
        sales.quantity,
        sales.gross_amount,
        sales.discounts,
        sales.collab_amount,
        sales.beatstars_fee,
        sales.net_revenue
    FROM `versa-dashboard.silver.sales_summary` AS sales

    LEFT JOIN merge_rules AS rules
        ON sales.product_name = rules.source_product_name
        AND sales.quantity = rules.source_quantity

    WHERE rules.source_product_name IS NULL
),

merged_sales AS (
    SELECT
        rules.canonical_product_name AS product_name,
        sales.product_type,
        SUM(sales.quantity) AS quantity,
        SUM(sales.gross_amount) AS gross_amount,
        SUM(sales.discounts) AS discounts,
        SUM(sales.collab_amount) AS collab_amount,
        SUM(sales.beatstars_fee) AS beatstars_fee,
        SUM(sales.net_revenue) AS net_revenue

    FROM `versa-dashboard.silver.sales_summary` AS sales

    INNER JOIN merge_rules AS rules
        ON sales.product_name = rules.source_product_name
        AND sales.quantity = rules.source_quantity

    GROUP BY
        rules.canonical_product_name,
        sales.product_type
)

SELECT * FROM regular_sales

UNION ALL

SELECT * FROM merged_sales
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
    FROM `versa-dashboard.gold.beatstars_sales_performance`
    WHERE product_type = 'track'
    GROUP BY product_name
),

manual_matches AS (
    SELECT
        youtube_video_id,
        source_product_name AS beatstars_product_name,
        source_quantity AS beatstars_quantity
    FROM `versa-dashboard.gold.beatstars_matching_rules`
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
    y.estimated_revenue,

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

BEATSTARS_DAILY_BEAT_SALES_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.beatstars_daily_beat_sales`
AS

SELECT
    order_date,
    beat_name_clean AS beat_name,
    store_type,

    COUNTIF(is_paid_sale) AS paid_sales,
    COUNTIF(is_free_sale) AS free_sales,
    COUNT(*) AS total_units,

    SUM(sale_price) AS gross_beat_revenue

FROM `versa-dashboard.silver.fact_beat_sales`

GROUP BY
    order_date,
    beat_name,
    store_type
"""

BEATSTARS_MONTHLY_BEAT_SALES_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.beatstars_monthly_beat_sales`
AS

SELECT
    DATE_TRUNC(order_date, MONTH) AS order_month,

    beat_name,

    store_type,

    SUM(paid_sales) AS paid_sales,

    SUM(free_sales) AS free_sales,

    SUM(total_units) AS total_units,

    SUM(gross_beat_revenue) AS gross_beat_revenue

FROM `versa-dashboard.gold.beatstars_daily_beat_sales`

GROUP BY
    order_month,
    beat_name,
    store_type
"""

DASHBOARD_OVERVIEW_QUERY = """
CREATE OR REPLACE TABLE
    `versa-dashboard.gold.dashboard_overview`
AS

SELECT
    (
        SELECT
            SUM(net_revenue)
        FROM `versa-dashboard.gold.beatstars_sales_performance`
    ) AS beatstars_revenue,

    (
        SELECT
            SUM(estimated_revenue)
        FROM `versa-dashboard.gold.youtube_video_performance`
    ) AS youtube_revenue,

    (
        SELECT
            SUM(quantity)
        FROM `versa-dashboard.gold.beatstars_sales_performance`
    ) AS total_sales,

    (
        SELECT
            SUM(views)
        FROM `versa-dashboard.gold.youtube_video_performance`
    ) AS total_views
"""