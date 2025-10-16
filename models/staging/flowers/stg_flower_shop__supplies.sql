select
    id as supply_id,
    name as supply_name,
    cost,
    perishable,
    sku
from {{ get_raw_data('raw_supplies') }}