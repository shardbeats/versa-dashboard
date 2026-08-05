SELECT

    DATE_TRUNC(order_date, MONTH) AS order_month,

    beat_name,

    store_type,

    SUM(paid_sales) AS paid_sales,

    SUM(free_sales) AS free_sales,

    SUM(total_units) AS total_units,

    SUM(gross_beat_revenue) AS gross_beat_revenue

FROM {{ ref('beatstars_daily_beat_sales') }}

GROUP BY

    order_month,

    beat_name,

    store_type