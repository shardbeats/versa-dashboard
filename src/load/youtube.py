from pathlib import Path

import pandas as pd


DIM_YOUTUBE_PATH = Path(
    "data/silver/youtube/dim_youtube_video.parquet"
)

FACT_YOUTUBE_PATH = Path(
    "data/silver/youtube/fact_youtube_video_metrics.parquet"
)


def load_youtube_to_silver(
    dim_youtube_video: pd.DataFrame,
    fact_youtube_video_metrics: pd.DataFrame,
) -> None:
    """
    Save the YouTube dimension and fact tables
    to the Silver layer.
    """

    DIM_YOUTUBE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dim_youtube_video.to_parquet(
        DIM_YOUTUBE_PATH,
        index=False,
    )

    fact_youtube_video_metrics.to_parquet(
        FACT_YOUTUBE_PATH,
        index=False,
    )

    print(
        "\n✅ Saved YouTube Silver tables:"
    )

    print(
        f"Dimension: {DIM_YOUTUBE_PATH}"
    )

    print(
        f"Fact:      {FACT_YOUTUBE_PATH}"
    )