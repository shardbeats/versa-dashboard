WITH beat_sales AS (

    SELECT
        beat_name_clean,

        COUNTIF(is_paid_sale) AS paid_sales,

        SUM(
            CASE
                WHEN is_paid_sale THEN sale_price
                ELSE 0
            END
        ) AS beatstars_revenue,

        MAX(
            CASE
                WHEN is_paid_sale THEN order_date
            END
        ) AS last_sale_date,

        DATE_DIFF(
            CURRENT_DATE(),
            MAX(
                CASE
                    WHEN is_paid_sale THEN order_date
                END
            ),
            DAY
        ) AS days_since_last_sale

    FROM {{ source('silver', 'fact_beat_sales') }}

    GROUP BY beat_name_clean

),

youtube_metrics AS (

    SELECT
        video_id,
        views,
        estimated_revenue

    FROM {{ ref('youtube_video_performance') }}

),

beat_dimension AS (

    SELECT
        beat_key,
        beat_name,
        youtube_video_id,
        published_at,
        beatstars_product_name

    FROM {{ ref('dim_beat') }}

),

base AS (

    SELECT
        d.beat_key,
        d.beat_name,
        d.published_at,

        y.views AS youtube_views,
        y.estimated_revenue AS youtube_revenue,

        COALESCE(s.paid_sales, 0) AS paid_sales,

        COALESCE(
            s.beatstars_revenue,
            0
        ) AS beatstars_revenue,

        s.last_sale_date,

        COALESCE(
            s.days_since_last_sale,
            99999
        ) AS days_since_last_sale,

        COALESCE(
            s.beatstars_revenue,
            0
        )
        +
        COALESCE(
            y.estimated_revenue,
            0
        ) AS total_revenue

    FROM beat_dimension AS d

    LEFT JOIN youtube_metrics AS y
        ON d.youtube_video_id = y.video_id

    LEFT JOIN beat_sales AS s
        ON d.beatstars_product_name = s.beat_name_clean

),

scored AS (

    SELECT
        *,

        ROUND(
            SAFE_DIVIDE(
                LN(1 + paid_sales),
                LN(1 + MAX(paid_sales) OVER ())
            ) * 100,
            1
        ) AS sales_score,

        ROUND(
            SAFE_DIVIDE(
                LN(1 + youtube_views),
                LN(1 + MAX(youtube_views) OVER ())
            ) * 100,
            1
        ) AS views_score,

        ROUND(
            SAFE_DIVIDE(
                LN(1 + total_revenue),
                LN(1 + MAX(total_revenue) OVER ())
            ) * 100,
            1
        ) AS revenue_score,

        ROUND(
            100 * EXP(
                -SAFE_DIVIDE(
                    days_since_last_sale,
                    365
                )
            ),
            1
        ) AS recency_score

    FROM base

),

final AS (

    SELECT
        *,

        ROUND(
            sales_score * 0.40
            + revenue_score * 0.30
            + views_score * 0.20
            + recency_score * 0.10,
            1
        ) AS overall_score

    FROM scored

),

priced AS (

    SELECT
        *,

        ROUND(
            300
            + 4200 * POW(overall_score / 100, 4)
            + 11000 * POW(overall_score / 100, 20),
            0
        ) AS target_price

    FROM final

),

ranged AS (

    SELECT
        *,

        GREATEST(
            300,
            FLOOR((target_price * 0.85) / 50) * 50
        ) AS price_min,

        GREATEST(
            350,
            CEIL((target_price * 1.15) / 50) * 50
        ) AS price_max

    FROM priced

)

SELECT *
FROM ranged