WITH merge_rules AS (

    SELECT
        source_product_name,
        source_quantity,
        canonical_product_name

    FROM {{ ref('beatstars_matching_rules') }}

    WHERE rule_type = 'merge'

),

regular_sales AS (

    SELECT
        sales.product_name,
        sales.product_type,
        sales.quantity,
        sales.gross_amount,
        sales.discounts,
        sales.collab_amount,
        sales.beatstars_fee,
        sales.net_revenue

    FROM {{ source('silver', 'sales_summary') }} AS sales

    LEFT JOIN merge_rules AS rules
        ON sales.product_name = rules.source_product_name
        AND sales.quantity = rules.source_quantity

    WHERE rules.source_product_name IS NULL

),

merged_sales AS (

    SELECT
        rules.canonical_product_name AS product_name,
        sales.product_type,

        SUM(sales.quantity) AS quantity,
        SUM(sales.gross_amount) AS gross_amount,
        SUM(sales.discounts) AS discounts,
        SUM(sales.collab_amount) AS collab_amount,
        SUM(sales.beatstars_fee) AS beatstars_fee,
        SUM(sales.net_revenue) AS net_revenue

    FROM {{ source('silver', 'sales_summary') }} AS sales

    INNER JOIN merge_rules AS rules
        ON sales.product_name = rules.source_product_name
        AND sales.quantity = rules.source_quantity

    GROUP BY
        rules.canonical_product_name,
        sales.product_type

)

SELECT *
FROM regular_sales

UNION ALL

SELECT *
FROM merged_sales