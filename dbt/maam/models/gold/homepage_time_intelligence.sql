WITH periods AS (

    SELECT 'Last 7 Days' AS period_name, 7 AS days_back, 1 AS sort_order
    UNION ALL
    SELECT 'Last 30 Days', 30, 2
    UNION ALL
    SELECT 'Last 90 Days', 90, 3
    UNION ALL
    SELECT 'Lifetime', NULL, 4

),

beatstars AS (

    SELECT
        p.period_name,
        p.sort_order,

        SUM(
            CASE
                WHEN s.is_paid_sale
                AND (
                    p.days_back IS NULL
                    OR s.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL p.days_back DAY)
                )
                THEN s.sale_price
                ELSE 0
            END
        ) AS beat_revenue,

        COUNTIF(
            s.is_paid_sale
            AND (
                p.days_back IS NULL
                OR s.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL p.days_back DAY)
            )
        ) AS beat_sales

    FROM periods AS p

    CROSS JOIN {{ source('silver', 'fact_beat_sales_unified') }} AS s

    GROUP BY
        p.period_name,
        p.sort_order

),

youtube_latest AS (

    SELECT
        video_id,
        views,
        watch_time_minutes,
        subscribers_gained,
        estimated_revenue,
        snapshot_timestamp

    FROM {{ source('silver', 'fact_youtube_video_metrics') }}

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY video_id
        ORDER BY snapshot_timestamp DESC
    ) = 1

),

youtube_periods AS (

    SELECT
        p.period_name,
        p.sort_order,
        p.days_back,

        SUM(latest.views) AS latest_views,
        SUM(latest.watch_time_minutes) AS latest_watch_time_minutes,
        SUM(latest.subscribers_gained) AS latest_subscribers_gained,
        SUM(latest.estimated_revenue) AS latest_estimated_revenue

    FROM periods AS p

    CROSS JOIN youtube_latest AS latest

    GROUP BY
        p.period_name,
        p.sort_order,
        p.days_back

),

youtube_previous AS (

    SELECT
        period_name,
        SUM(views) AS previous_views,
        SUM(watch_time_minutes) AS previous_watch_time_minutes,
        SUM(subscribers_gained) AS previous_subscribers_gained,
        SUM(estimated_revenue) AS previous_estimated_revenue

    FROM (

        SELECT
            p.period_name,
            previous.video_id,
            previous.views,
            previous.watch_time_minutes,
            previous.subscribers_gained,
            previous.estimated_revenue

        FROM periods AS p

        LEFT JOIN {{ source('silver', 'fact_youtube_video_metrics') }} AS previous
            ON p.days_back IS NOT NULL
            AND DATE(previous.snapshot_timestamp) <= DATE_SUB(
                CURRENT_DATE(),
                INTERVAL p.days_back DAY
            )

        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY
                p.period_name,
                previous.video_id
            ORDER BY previous.snapshot_timestamp DESC
        ) = 1

    )

    GROUP BY period_name

),

youtube AS (

    SELECT
        curr.period_name,
        curr.sort_order,

        CASE
            WHEN curr.days_back IS NULL
                THEN curr.latest_views
            ELSE GREATEST(
                curr.latest_views
                - COALESCE(
                    previous.previous_views,
                    curr.latest_views
                ),
                0
            )
        END AS youtube_views,

        CASE
            WHEN curr.days_back IS NULL
                THEN curr.latest_estimated_revenue
            ELSE GREATEST(
                curr.latest_estimated_revenue
                - COALESCE(
                    previous.previous_estimated_revenue,
                    curr.latest_estimated_revenue
                ),
                0
            )
        END AS youtube_revenue,

        CASE
            WHEN curr.days_back IS NULL
                THEN curr.latest_watch_time_minutes
            ELSE GREATEST(
                curr.latest_watch_time_minutes
                - COALESCE(
                    previous.previous_watch_time_minutes,
                    curr.latest_watch_time_minutes
                ),
                0
            )
        END AS watch_time_minutes,

        CASE
            WHEN curr.days_back IS NULL
                THEN curr.latest_subscribers_gained
            ELSE GREATEST(
                curr.latest_subscribers_gained
                - COALESCE(
                    previous.previous_subscribers_gained,
                    curr.latest_subscribers_gained
                ),
                0
            )
        END AS subscribers_gained

    FROM youtube_periods AS curr

    LEFT JOIN youtube_previous AS previous
        USING (period_name)

),

published AS (

    SELECT
        p.period_name,

        COUNTIF(
            p.days_back IS NULL
            OR DATE(v.published_at) >= DATE_SUB(
                CURRENT_DATE(),
                INTERVAL p.days_back DAY
            )
        ) AS beats_published

    FROM periods AS p

    CROSS JOIN {{ source('silver', 'dim_youtube_video') }} AS v

    WHERE v.duration_seconds > 60

    GROUP BY
        p.period_name

)

SELECT
    b.period_name,
    b.sort_order,

    b.beat_revenue,
    b.beat_sales,

    y.youtube_revenue,
    y.youtube_views,
    y.watch_time_minutes,
    y.subscribers_gained,

    p.beats_published,

    b.beat_revenue
        + y.youtube_revenue
        AS total_revenue

FROM beatstars AS b

LEFT JOIN youtube AS y
    USING (period_name, sort_order)

LEFT JOIN published AS p
    USING (period_name)

ORDER BY sort_order