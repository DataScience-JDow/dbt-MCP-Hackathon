with flower_orders as (
    select * from {{ ref('int_flowers__orders_joined') }}
)

select
    flower_order_id,
    customer_name,
    customer_email,
    customer_phone,
    arrangement_id,
    arrangement_name,
    arrangement_description,
    size_category,
    occasion_type,
    is_custom,
    quantity,
    arrangement_base_price,
    total_amount,
    delivery_fee,
    discount_amount,
    (total_amount + delivery_fee - discount_amount) as final_amount,
    recipient_name,
    recipient_phone,
    delivery_address,
    delivery_city,
    delivery_state,
    delivery_zipcode,
    delivery_date,
    delivery_time,
    delivery_status,
    occasion,
    promo_code,
    order_date,
    order_status
from flower_orders
