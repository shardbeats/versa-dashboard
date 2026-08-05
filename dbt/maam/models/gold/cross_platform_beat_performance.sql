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

FROM {{ ref('dim_beat') }} AS b

LEFT JOIN {{ ref('youtube_video_performance') }} AS y
    ON b.youtube_video_id = y.video_id

LEFT JOIN {{ ref('beatstars_sales_performance') }} AS bs
    ON b.beatstars_product_name = bs.product_name
    AND b.beatstars_quantity = bs.quantity

WHERE b.match_status IN ('exact', 'manual')