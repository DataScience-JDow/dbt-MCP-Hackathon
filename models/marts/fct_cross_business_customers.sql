with jaffle_customers as (
    select distinct
        lower(trim(customer_name)) as normalized_customer_name,
        customer_id,
        customer_name as original_name,
        min(ordered_at) as first_jaffle_order
    from {{ ref('int_jaffles__orders_joined') }}
    group by 1, 2, 3
),

flower_customers as (
    select distinct
        lower(trim(customer_name)) as normalized_customer_name,
        customer_email,
        customer_name as original_name,
        min(order_date) as first_flower_order
    from {{ ref('int_flowers__orders_joined') }}
    group by 1, 2, 3
),

cross_business as (
    select
        j.normalized_customer_name,
        j.customer_id as jaffle_customer_id,
        f.customer_email as flower_customer_email,
        coalesce(j.original_name, f.original_name) as customer_name,
        j.first_jaffle_order,
        f.first_flower_order
    from jaffle_customers j
    inner join flower_customers f
        on j.normalized_customer_name = f.normalized_customer_name
)

select
    {{ dbt_utils.generate_surrogate_key(['jaffle_customer_id', 'flower_customer_email']) }} as cross_business_key,
    customer_name,
    jaffle_customer_id,
    flower_customer_email,
    first_jaffle_order,
    first_flower_order,
    case
        when first_jaffle_order < first_flower_order then 'jaffle_first'
        when first_flower_order < first_jaffle_order then 'flower_first'
        else 'same_day'
    end as acquisition_source
from cross_business
