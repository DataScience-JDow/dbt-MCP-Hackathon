select
    stg_jaffle__orders.order_id,
    stg_jaffle__orders.customer_id,
    stg_jaffle__customers.customer_name,
    stg_jaffle__orders.ordered_at,
    stg_jaffle__orders.store_id,
    stg_jaffle__stores.store_name,
    stg_jaffle__stores.opened_at as store_opened_at,
    stg_jaffle__stores.tax_rate as store_tax_rate,
    stg_jaffle__orders.subtotal,
    stg_jaffle__orders.tax_paid,
    stg_jaffle__orders.order_total,
    stg_jaffle__items.product_sku,
    stg_jaffle__items.product_name as item_name,
    stg_jaffle__items.product_type as item_type,
    stg_jaffle__items.price as item_price,
    stg_jaffle__items.description as item_description,
    stg_jaffle__products.product_name,
    stg_jaffle__products.product_type,
    stg_jaffle__products.price as product_price,
    stg_jaffle__products.description as product_description
from {{ ref('stg_jaffle__orders') }} stg_jaffle__orders
left join {{ ref('stg_jaffle__customers') }} stg_jaffle__customers
    on stg_jaffle__orders.customer_id = stg_jaffle__customers.customer_id
left join {{ ref('stg_jaffle__stores') }} stg_jaffle__stores
    on stg_jaffle__orders.store_id = stg_jaffle__stores.store_id
left join {{ ref('stg_jaffle__items') }} stg_jaffle__items
    on stg_jaffle__orders.order_id = stg_jaffle__items.order_id
left join {{ ref('stg_jaffle__products') }} stg_jaffle__products
    on stg_jaffle__items.product_sku = stg_jaffle__products.product_sku