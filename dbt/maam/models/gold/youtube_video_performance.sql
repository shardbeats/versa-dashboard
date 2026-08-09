WITH latest_metrics AS (

    SELECT
        video_id,
        views,
        likes,
        comments,
        watch_time_minutes,
        average_view_duration_seconds,
        average_view_percentage,
        subscribers_gained,
        subscribers_lost,
        estimated_revenue,
        snapshot_timestamp

    FROM {{ source('silver', 'fact_youtube_video_metrics') }}

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY video_id
        ORDER BY snapshot_timestamp DESC
    ) = 1

)

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

INNER JOIN latest_metrics AS f
USING (video_id)