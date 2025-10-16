with jaffle_daily as (
    select
        cast(ordered_at as date) as order_date,
        'jaffle' as business,
        sum(order_total) as revenue,
        count(distinct order_id) as order_count,
        count(distinct customer_id) as customer_count
    from {{ ref('int_jaffles__orders_joined') }}
    group by 1, 2
),

flower_daily as (
    select
        order_date,
        'flower' as business,
        sum(total_amount + delivery_fee - discount_amount) as revenue,
        count(distinct flower_order_id) as order_count,
        count(distinct customer_email) as customer_count
    from {{ ref('int_flowers__orders_joined') }}
    group by 1, 2
),

combined_daily as (
    select * from jaffle_daily
    union all
    select * from flower_daily
)

select
    order_date,
    business,
    revenue,
    order_count,
    customer_count,
    round(revenue / order_count, 2) as avg_order_value,
    round(revenue / customer_count, 2) as revenue_per_customer
from combined_daily
