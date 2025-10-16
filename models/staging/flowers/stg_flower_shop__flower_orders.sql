select
    flower_order_id,
    trim(customer_name) as customer_name,
    customer_email,
    customer_phone,
    arrangement_id,
    quantity,
    total_amount,
    delivery_id,
    occasion,
    promo_code,
    discount_amount,
    order_date,
    order_status
from {{ get_raw_data('raw_flower_orders') }}
