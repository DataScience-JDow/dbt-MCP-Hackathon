select
    id as customer_id,
    trim(name) as customer_name
from {{ get_raw_data('raw_customers') }}