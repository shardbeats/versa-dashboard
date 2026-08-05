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

FROM {{ source('silver', 'dim_youtube_video') }} AS d

INNER JOIN {{ source('silver', 'fact_youtube_video_metrics') }} AS f
    USING (video_id)