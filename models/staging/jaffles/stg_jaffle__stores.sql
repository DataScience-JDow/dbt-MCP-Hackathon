select
    id as store_id,
    name as store_name,
    opened_at,
    tax_rate
from {{ get_raw_data('raw_stores') }}