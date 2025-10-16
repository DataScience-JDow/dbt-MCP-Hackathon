select
    delivery_id,
    delivery_address,
    delivery_city,
    delivery_state,
    delivery_zip as delivery_zipcode,
    delivery_date,
    delivery_time_slot as delivery_time,
    special_instructions as delivery_instructions,
    delivery_status,
    delivery_fee,
    recipient_name,
    recipient_phone
from {{ get_raw_data('raw_delivery_info') }}