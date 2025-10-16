select
    stg_flower_shop__flower_orders.flower_order_id,
    stg_flower_shop__flower_orders.customer_name,
    stg_flower_shop__flower_orders.customer_email,
    stg_flower_shop__flower_orders.customer_phone,
    stg_flower_shop__flower_orders.arrangement_id,
    stg_flower_shop__flower_arrangements.arrangement_name,
    stg_flower_shop__flower_arrangements.description as arrangement_description,
    stg_flower_shop__flower_arrangements.base_price as arrangement_base_price,
    stg_flower_shop__flower_arrangements.size_category,
    stg_flower_shop__flower_arrangements.occasion_type,
    stg_flower_shop__flower_arrangements.is_custom,
    stg_flower_shop__flower_orders.quantity,
    stg_flower_shop__flower_orders.total_amount,
    stg_flower_shop__flower_orders.delivery_id,
    stg_flower_shop__delivery_info.delivery_address,
    stg_flower_shop__delivery_info.delivery_city,
    stg_flower_shop__delivery_info.delivery_state,
    stg_flower_shop__delivery_info.delivery_zipcode,
    stg_flower_shop__delivery_info.delivery_date,
    stg_flower_shop__delivery_info.delivery_time,
    stg_flower_shop__delivery_info.delivery_instructions,
    stg_flower_shop__delivery_info.delivery_status,
    stg_flower_shop__delivery_info.delivery_fee,
    stg_flower_shop__delivery_info.recipient_name,
    stg_flower_shop__delivery_info.recipient_phone,
    stg_flower_shop__flower_orders.occasion,
    stg_flower_shop__flower_orders.promo_code,
    stg_flower_shop__flower_orders.discount_amount,
    stg_flower_shop__flower_orders.order_date,
    stg_flower_shop__flower_orders.order_status
from {{ ref('stg_flower_shop__flower_orders') }} stg_flower_shop__flower_orders
left join {{ ref('stg_flower_shop__flower_arrangements') }} stg_flower_shop__flower_arrangements
    on stg_flower_shop__flower_orders.arrangement_id = stg_flower_shop__flower_arrangements.arrangement_id
left join {{ ref('stg_flower_shop__delivery_info') }} stg_flower_shop__delivery_info
    on stg_flower_shop__flower_orders.delivery_id = stg_flower_shop__delivery_info.delivery_id