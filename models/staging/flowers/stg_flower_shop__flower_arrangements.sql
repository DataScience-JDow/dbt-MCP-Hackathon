select
    arrangement_id,
    arrangement_name,
    description,
    base_price,
    flower_ids,
    flower_quantities,
    size as size_category,
    occasion_type,
    is_custom
from {{ ref('raw_flower_arrangements') }}