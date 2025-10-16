select
    order_id,
    sku as product_sku,
    name as product_name,
    type as product_type,
    price,
    description
from {{ get_raw_data('raw_items') }}