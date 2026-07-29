import pandas as pd
from google.cloud import bigquery

from src.load.bigquery import load_dataframe_to_bigquery


DIM_YOUTUBE_PATH = (
    "data/silver/youtube/dim_youtube_video.parquet"
)


def main():
    dim_youtube_video = pd.read_parquet(
        DIM_YOUTUBE_PATH
    )

    load_dataframe_to_bigquery(
        dataframe=dim_youtube_video,
        table_name="dim_youtube_video",
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )


if __name__ == "__main__":
    main()