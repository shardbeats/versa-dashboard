SELECT

(
    SELECT
        SUM(net_revenue)

    FROM {{ ref('beatstars_sales_performance') }}

) AS beatstars_revenue,

(
    SELECT
        SUM(estimated_revenue)

    FROM {{ ref('youtube_video_performance') }}

) AS youtube_revenue,

(
    SELECT
        SUM(quantity)

    FROM {{ ref('beatstars_sales_performance') }}

) AS total_sales,

(
    SELECT
        SUM(views)

    FROM {{ ref('youtube_video_performance') }}

) AS total_views