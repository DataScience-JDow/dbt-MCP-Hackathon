with jaffle_customers as (
    select distinct
        customer_id,
        customer_name,
        'jaffle' as source
    from {{ ref('int_jaffles__orders_joined') }}
),

flower_customers as (
    select distinct
        customer_email as customer_id,
        customer_name,
        'flower' as source
    from {{ ref('int_flowers__orders_joined') }}
),

all_customers as (
    select * from jaffle_customers
    union all
    select * from flower_customers
)

select
    {{ dbt_utils.generate_surrogate_key(['customer_id', 'source']) }} as customer_key,
    customer_id,
    customer_name,
    source
from all_customers
