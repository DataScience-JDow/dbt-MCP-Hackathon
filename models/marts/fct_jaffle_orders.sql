with jaffle_orders as (
    select * from {{ ref('int_jaffles__orders_joined') }}
)

select
    order_id,
    customer_id,
    customer_name,
    ordered_at,
    store_id,
    store_name,
    store_opened_at,
    store_tax_rate,
    product_sku,
    item_name,
    item_type,
    item_price,
    subtotal,
    tax_paid,
    order_total
from jaffle_orders
