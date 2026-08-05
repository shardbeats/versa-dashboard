SELECT
    order_date,
    beat_name_clean AS beat_name,
    store_type,

    COUNTIF(is_paid_sale) AS paid_sales,
    COUNTIF(is_free_sale) AS free_sales,
    COUNT(*) AS total_units,

    SUM(sale_price) AS gross_beat_revenue

FROM {{ source('silver', 'fact_beat_sales') }}

GROUP BY
    order_date,
    beat_name,
    store_type