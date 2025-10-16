select
    flower_id,
    flower_name,
    color,
    price_per_stem,
    supplier_id,
    seasonal_availability,
    care_difficulty,
    lifespan_days
from {{ get_raw_data('raw_flowers') }}