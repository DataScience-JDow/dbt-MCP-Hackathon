with jaffle_revenue as (
    select
        customer_id,
        customer_name,
        sum(order_total) as total_revenue,
        count(distinct order_id) as order_count,
        min(ordered_at) as first_order_date,
        max(ordered_at) as last_order_date,
        'jaffle' as source
    from {{ ref('int_jaffles__orders_joined') }}
    group by customer_id, customer_name
),

flower_revenue as (
    select
        customer_email as customer_id,
        customer_name,
        sum(total_amount + delivery_fee - discount_amount) as total_revenue,
        count(distinct flower_order_id) as order_count,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        'flower' as source
    from {{ ref('int_flowers__orders_joined') }}
    group by customer_email, customer_name
),

combined_revenue as (
    select * from jaffle_revenue
    union all
    select * from flower_revenue
)

select
    {{ dbt_utils.generate_surrogate_key(['customer_id', 'source']) }} as customer_key,
    customer_id,
    customer_name,
    source,
    total_revenue,
    order_count,
    round(total_revenue / order_count, 2) as avg_order_value,
    first_order_date,
    last_order_date,
    datediff('day', first_order_date, last_order_date) as customer_tenure_days
from combined_revenue
