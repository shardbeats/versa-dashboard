import pandas as pd

youtube = pd.read_parquet(
    "data/silver/youtube/dim_youtube_video.parquet"
)

beatstars = pd.read_parquet(
    "data/silver/beatstars/sales_summary.parquet"
)

# Endast vanliga YouTube-videor från huvudperioden.
youtube = youtube[
    (~youtube["is_short"])
    & (youtube["is_main_niche_period"])
].copy()

# Endast riktiga beats.
beatstars = beatstars[
    beatstars["product_type"] == "track"
].copy()

# Hur många YouTube-videor finns för varje beatnamn?
youtube_match_counts = (
    youtube.groupby("beat_name")
    .size()
    .rename("youtube_match_count")
    .reset_index()
)

# Lägg på matchinformation på BeatStars.
match_check = beatstars.merge(
    youtube_match_counts,
    left_on="product_name",
    right_on="beat_name",
    how="left",
)

match_check["youtube_match_count"] = (
    match_check["youtube_match_count"]
    .fillna(0)
    .astype("int64")
)

match_check["match_status"] = "unmatched"

match_check.loc[
    match_check["youtube_match_count"] == 1,
    "match_status",
] = "exact"

match_check.loc[
    match_check["youtube_match_count"] > 1,
    "match_status",
] = "ambiguous"

print("\n========== MATCH SUMMARY ==========\n")

print(match_check["match_status"].value_counts())

print("\nPercentages:")

print(
    (
        match_check["match_status"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
    )
)

print("\n========== AMBIGUOUS MATCHES ==========\n")

print(
    match_check.loc[
        match_check["match_status"] == "ambiguous",
        [
            "product_name",
            "quantity",
            "net_revenue",
            "youtube_match_count",
        ],
    ]
    .sort_values(
        ["quantity", "net_revenue"],
        ascending=False,
    )
    .to_string(index=False)
)

print("\n========== UNMATCHED PRODUCTS ==========\n")

print(
    match_check.loc[
        match_check["match_status"] == "unmatched",
        [
            "product_name",
            "quantity",
            "net_revenue",
        ],
    ]
    .sort_values(
        ["quantity", "net_revenue"],
        ascending=False,
    )
    .to_string(index=False)
)

print("\n========== REVENGE DEBUG ==========\n")

print(
    youtube.loc[
        youtube["beat_name"] == "Revenge",
        [
            "video_id",
            "title",
            "published_at",
        ],
    ]
    .sort_values("published_at")
    .to_string(index=False)
)