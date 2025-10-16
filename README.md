This project was created for the dbt MCP server hackathon during Coalesce 2025.
It contains a set of seeds, models, exposures, and a configured semantic layer.

Feel free to clone it and start building on top of it!

You should be able to run the project with dbt Core and Fusion on any data warehouse by providing the appropriate credentials in your profiles.yml file.

If you don't have access to a data warehouse, you can also run the project with dbt Core and DuckDB.
To do so:
1. create a python virtual environment and activate it
2. install dbt-duckdb
3. rename `profiles.yml.bak` to `profiles.yml`
4. just do a `dbt build` to run the project!