{% macro get_raw_data(table_name) %}
    {# {% if (env_var('DBT_USE_SEEDS', 'false') | lower) != 'false' %} #}
    {% if true %}
        {{ ref(table_name) }}
    {% else %}
        {{ source('raw_data', table_name) }}
    {% endif %}
{% endmacro %}
