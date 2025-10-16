-- Snowflake Stored Procedure for Flower Shop ETL
-- Replicates all flower-related models and transformations from the dbt project

CREATE OR REPLACE PROCEDURE flower_shop_etl()
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    -- Variables for logging and error handling
    v_start_time TIMESTAMP := CURRENT_TIMESTAMP();
    v_end_time TIMESTAMP;
    v_row_count INTEGER;
    v_error_message STRING;
    v_procedure_status STRING := 'SUCCESS';
    v_table_exists INTEGER;
BEGIN
    -- Create supporting tables for audit logging first
    CREATE TABLE IF NOT EXISTS ETL_AUDIT_LOG (
        log_id NUMBER AUTOINCREMENT PRIMARY KEY,
        procedure_name VARCHAR(100),
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        status VARCHAR(20),
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    CREATE TABLE IF NOT EXISTS DATA_QUALITY_ISSUES (
        issue_id NUMBER AUTOINCREMENT PRIMARY KEY,
        table_name VARCHAR(100),
        issue_type VARCHAR(50),
        issue_count INTEGER,
        detected_at TIMESTAMP,
        resolved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    -- Log procedure start
    INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, status, message)
    VALUES ('flower_shop_etl', v_start_time, 'STARTED', 'Beginning flower shop ETL process');

    -- ====================
    -- STEP 1: Create/Truncate temporary staging tables
    -- ====================

    -- Check and create/truncate temp_stg_flowers
    SELECT COUNT(*) INTO v_table_exists
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
      AND TABLE_NAME = 'TEMP_STG_FLOWERS'
      AND TABLE_TYPE = 'BASE TABLE';

    IF (v_table_exists > 0) THEN
        TRUNCATE TABLE temp_stg_flowers;
    ELSE
        CREATE TABLE temp_stg_flowers (
            flower_id VARCHAR(50),
            flower_name VARCHAR(100),
            color VARCHAR(50),
            price_per_stem NUMBER(10,2),
            supplier_id VARCHAR(50),
            seasonal_availability VARCHAR(20),
            care_difficulty VARCHAR(20),
            lifespan_days INTEGER,
            processed_at TIMESTAMP
        );
    END IF;

    INSERT INTO temp_stg_flowers
    SELECT
        flower_id,
        flower_name,
        color,
        price_per_stem,
        supplier_id,
        seasonal_availability,
        care_difficulty,
        lifespan_days,
        CURRENT_TIMESTAMP() as processed_at
    FROM raw_flowers
    WHERE flower_id IS NOT NULL
      AND flower_name IS NOT NULL
      AND price_per_stem > 0;

    -- Data quality checks for flowers
    SELECT COUNT(*) INTO v_row_count FROM temp_stg_flowers;
    IF (v_row_count = 0) THEN
        v_error_message := 'No valid flower records found in raw_flowers table';
        RAISE EXCEPTION v_error_message;
    END IF;

    -- Check for negative prices
    SELECT COUNT(*) INTO v_row_count
    FROM raw_flowers
    WHERE price_per_stem <= 0 AND flower_id IS NOT NULL;

    IF (v_row_count > 0) THEN
        INSERT INTO DATA_QUALITY_ISSUES (table_name, issue_type, issue_count, detected_at)
        VALUES ('raw_flowers', 'NEGATIVE_PRICE', v_row_count, CURRENT_TIMESTAMP());
    END IF;

    -- Check and create/truncate temp_stg_flower_arrangements
    SELECT COUNT(*) INTO v_table_exists
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
      AND TABLE_NAME = 'TEMP_STG_FLOWER_ARRANGEMENTS'
      AND TABLE_TYPE = 'BASE TABLE';

    IF (v_table_exists > 0) THEN
        TRUNCATE TABLE temp_stg_flower_arrangements;
    ELSE
        CREATE TABLE temp_stg_flower_arrangements (
            arrangement_id VARCHAR(50),
            arrangement_name VARCHAR(200),
            description TEXT,
            base_price NUMBER(10,2),
            flower_ids TEXT,
            flower_quantities TEXT,
            size_category VARCHAR(20),
            occasion_type VARCHAR(50),
            is_custom BOOLEAN,
            processed_at TIMESTAMP
        );
    END IF;

    INSERT INTO temp_stg_flower_arrangements
    SELECT
        arrangement_id,
        arrangement_name,
        description,
        base_price,
        flower_ids,
        flower_quantities,
        size as size_category,
        occasion_type,
        is_custom,
        CURRENT_TIMESTAMP() as processed_at
    FROM raw_flower_arrangements
    WHERE arrangement_id IS NOT NULL
      AND arrangement_name IS NOT NULL
      AND base_price > 0;

    -- Data quality checks for arrangements
    SELECT COUNT(*) INTO v_row_count FROM temp_stg_flower_arrangements;
    IF (v_row_count = 0) THEN
        v_error_message := 'No valid arrangement records found in raw_flower_arrangements table';
        RAISE EXCEPTION v_error_message;
    END IF;

    -- Check and create/truncate temp_stg_flower_orders
    SELECT COUNT(*) INTO v_table_exists
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
      AND TABLE_NAME = 'TEMP_STG_FLOWER_ORDERS'
      AND TABLE_TYPE = 'BASE TABLE';

    IF (v_table_exists > 0) THEN
        TRUNCATE TABLE temp_stg_flower_orders;
    ELSE
        CREATE TABLE temp_stg_flower_orders (
            flower_order_id VARCHAR(50),
            customer_name VARCHAR(200),
            customer_email VARCHAR(200),
            customer_phone VARCHAR(50),
            arrangement_id VARCHAR(50),
            quantity INTEGER,
            total_amount NUMBER(10,2),
            delivery_id VARCHAR(50),
            occasion VARCHAR(100),
            promo_code VARCHAR(50),
            discount_amount NUMBER(10,2),
            order_date TIMESTAMP,
            order_status VARCHAR(50),
            processed_at TIMESTAMP
        );
    END IF;

    INSERT INTO temp_stg_flower_orders
    SELECT
        flower_order_id,
        customer_name,
        customer_email,
        customer_phone,
        arrangement_id,
        quantity,
        total_amount,
        delivery_id,
        occasion,
        promo_code,
        discount_amount,
        order_date,
        order_status,
        CURRENT_TIMESTAMP() as processed_at
    FROM raw_flower_orders
    WHERE flower_order_id IS NOT NULL
      AND customer_email IS NOT NULL
      AND total_amount >= 0
      AND quantity > 0;

    -- Data quality checks for orders
    SELECT COUNT(*) INTO v_row_count FROM temp_stg_flower_orders;
    IF (v_row_count = 0) THEN
        v_error_message := 'No valid order records found in raw_flower_orders table';
        RAISE EXCEPTION v_error_message;
    END IF;

    -- Check for invalid email formats
    SELECT COUNT(*) INTO v_row_count
    FROM temp_stg_flower_orders
    WHERE customer_email NOT RLIKE '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$';

    IF (v_row_count > 0) THEN
        INSERT INTO DATA_QUALITY_ISSUES (table_name, issue_type, issue_count, detected_at)
        VALUES ('raw_flower_orders', 'INVALID_EMAIL', v_row_count, CURRENT_TIMESTAMP());
    END IF;

    -- Check and create/truncate temp_stg_delivery_info
    SELECT COUNT(*) INTO v_table_exists
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
      AND TABLE_NAME = 'TEMP_STG_DELIVERY_INFO'
      AND TABLE_TYPE = 'BASE TABLE';

    IF (v_table_exists > 0) THEN
        TRUNCATE TABLE temp_stg_delivery_info;
    ELSE
        CREATE TABLE temp_stg_delivery_info (
            delivery_id VARCHAR(50),
            delivery_address TEXT,
            delivery_city VARCHAR(100),
            delivery_state VARCHAR(50),
            delivery_zipcode VARCHAR(20),
            delivery_date DATE,
            delivery_time VARCHAR(50),
            delivery_instructions TEXT,
            delivery_status VARCHAR(50),
            delivery_fee NUMBER(10,2),
            recipient_name VARCHAR(200),
            recipient_phone VARCHAR(50),
            processed_at TIMESTAMP
        );
    END IF;

    INSERT INTO temp_stg_delivery_info
    SELECT
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
        recipient_phone,
        CURRENT_TIMESTAMP() as processed_at
    FROM raw_delivery_info
    WHERE delivery_id IS NOT NULL
      AND delivery_address IS NOT NULL
      AND delivery_city IS NOT NULL
      AND delivery_state IS NOT NULL;

    -- Data quality checks for delivery info
    SELECT COUNT(*) INTO v_row_count FROM temp_stg_delivery_info;
    IF (v_row_count = 0) THEN
        v_error_message := 'No valid delivery records found in raw_delivery_info table';
        RAISE EXCEPTION v_error_message;
    END IF;

    -- Check and create/truncate temp_stg_supplies
    SELECT COUNT(*) INTO v_table_exists
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
      AND TABLE_NAME = 'TEMP_STG_SUPPLIES'
      AND TABLE_TYPE = 'BASE TABLE';

    IF (v_table_exists > 0) THEN
        TRUNCATE TABLE temp_stg_supplies;
    ELSE
        CREATE TABLE temp_stg_supplies (
            supply_id VARCHAR(50),
            supply_name VARCHAR(200),
            cost NUMBER(10,2),
            perishable BOOLEAN,
            sku VARCHAR(50),
            processed_at TIMESTAMP
        );
    END IF;

    INSERT INTO temp_stg_supplies
    SELECT
        id as supply_id,
        name as supply_name,
        cost,
        perishable,
        sku,
        CURRENT_TIMESTAMP() as processed_at
    FROM raw_supplies
    WHERE id IS NOT NULL
      AND name IS NOT NULL
      AND cost >= 0;

    -- ====================
    -- STEP 2: Insert/Update staging tables
    -- ====================

    -- Create stg_flower_shop__flowers table if it doesn't exist
    CREATE TABLE IF NOT EXISTS stg_flower_shop__flowers (
        flower_id VARCHAR(50) PRIMARY KEY,
        flower_name VARCHAR(100) NOT NULL,
        color VARCHAR(50),
        price_per_stem NUMBER(10,2),
        supplier_id VARCHAR(50),
        seasonal_availability VARCHAR(20),
        care_difficulty VARCHAR(20),
        lifespan_days INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    -- Insert/Update stg_flower_shop__flowers
    MERGE INTO stg_flower_shop__flowers AS target
    USING temp_stg_flowers AS source
    ON target.flower_id = source.flower_id
    WHEN MATCHED THEN
        UPDATE SET
            flower_name = source.flower_name,
            color = source.color,
            price_per_stem = source.price_per_stem,
            supplier_id = source.supplier_id,
            seasonal_availability = source.seasonal_availability,
            care_difficulty = source.care_difficulty,
            lifespan_days = source.lifespan_days,
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (flower_id, flower_name, color, price_per_stem, supplier_id,
                seasonal_availability, care_difficulty, lifespan_days,
                created_at, updated_at)
        VALUES (source.flower_id, source.flower_name, source.color, source.price_per_stem,
                source.supplier_id, source.seasonal_availability, source.care_difficulty,
                source.lifespan_days, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

    GET DIAGNOSTICS v_row_count = ROW_COUNT;
    INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, status, message)
    VALUES ('flower_shop_etl', CURRENT_TIMESTAMP(), 'INFO',
            'Processed ' || v_row_count || ' flower records');

    -- Create stg_flower_shop__flower_arrangements table if it doesn't exist
    CREATE TABLE IF NOT EXISTS stg_flower_shop__flower_arrangements (
        arrangement_id VARCHAR(50) PRIMARY KEY,
        arrangement_name VARCHAR(200) NOT NULL,
        description TEXT,
        base_price NUMBER(10,2),
        flower_ids TEXT,
        flower_quantities TEXT,
        size_category VARCHAR(20),
        occasion_type VARCHAR(50),
        is_custom BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    -- Insert/Update stg_flower_shop__flower_arrangements
    MERGE INTO stg_flower_shop__flower_arrangements AS target
    USING temp_stg_flower_arrangements AS source
    ON target.arrangement_id = source.arrangement_id
    WHEN MATCHED THEN
        UPDATE SET
            arrangement_name = source.arrangement_name,
            description = source.description,
            base_price = source.base_price,
            flower_ids = source.flower_ids,
            flower_quantities = source.flower_quantities,
            size_category = source.size_category,
            occasion_type = source.occasion_type,
            is_custom = source.is_custom,
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (arrangement_id, arrangement_name, description, base_price, flower_ids,
                flower_quantities, size_category, occasion_type, is_custom,
                created_at, updated_at)
        VALUES (source.arrangement_id, source.arrangement_name, source.description,
                source.base_price, source.flower_ids, source.flower_quantities,
                source.size_category, source.occasion_type, source.is_custom,
                CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

    GET DIAGNOSTICS v_row_count = ROW_COUNT;
    INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, status, message)
    VALUES ('flower_shop_etl', CURRENT_TIMESTAMP(), 'INFO',
            'Processed ' || v_row_count || ' arrangement records');

    -- Create stg_flower_shop__flower_orders table if it doesn't exist
    CREATE TABLE IF NOT EXISTS stg_flower_shop__flower_orders (
        flower_order_id VARCHAR(50) PRIMARY KEY,
        customer_name VARCHAR(200),
        customer_email VARCHAR(200) NOT NULL,
        customer_phone VARCHAR(50),
        arrangement_id VARCHAR(50),
        quantity INTEGER,
        total_amount NUMBER(10,2),
        delivery_id VARCHAR(50),
        occasion VARCHAR(100),
        promo_code VARCHAR(50),
        discount_amount NUMBER(10,2),
        order_date TIMESTAMP,
        order_status VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    -- Insert/Update stg_flower_shop__flower_orders
    MERGE INTO stg_flower_shop__flower_orders AS target
    USING temp_stg_flower_orders AS source
    ON target.flower_order_id = source.flower_order_id
    WHEN MATCHED THEN
        UPDATE SET
            customer_name = source.customer_name,
            customer_email = source.customer_email,
            customer_phone = source.customer_phone,
            arrangement_id = source.arrangement_id,
            quantity = source.quantity,
            total_amount = source.total_amount,
            delivery_id = source.delivery_id,
            occasion = source.occasion,
            promo_code = source.promo_code,
            discount_amount = source.discount_amount,
            order_date = source.order_date,
            order_status = source.order_status,
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (flower_order_id, customer_name, customer_email, customer_phone,
                arrangement_id, quantity, total_amount, delivery_id, occasion,
                promo_code, discount_amount, order_date, order_status,
                created_at, updated_at)
        VALUES (source.flower_order_id, source.customer_name, source.customer_email,
                source.customer_phone, source.arrangement_id, source.quantity,
                source.total_amount, source.delivery_id, source.occasion,
                source.promo_code, source.discount_amount, source.order_date,
                source.order_status, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

    GET DIAGNOSTICS v_row_count = ROW_COUNT;
    INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, status, message)
    VALUES ('flower_shop_etl', CURRENT_TIMESTAMP(), 'INFO',
            'Processed ' || v_row_count || ' order records');

    -- Create stg_flower_shop__delivery_info table if it doesn't exist
    CREATE TABLE IF NOT EXISTS stg_flower_shop__delivery_info (
        delivery_id VARCHAR(50) PRIMARY KEY,
        delivery_address TEXT,
        delivery_city VARCHAR(100),
        delivery_state VARCHAR(50),
        delivery_zipcode VARCHAR(20),
        delivery_date DATE,
        delivery_time VARCHAR(50),
        delivery_instructions TEXT,
        delivery_status VARCHAR(50),
        delivery_fee NUMBER(10,2),
        recipient_name VARCHAR(200),
        recipient_phone VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    -- Insert/Update stg_flower_shop__delivery_info
    MERGE INTO stg_flower_shop__delivery_info AS target
    USING temp_stg_delivery_info AS source
    ON target.delivery_id = source.delivery_id
    WHEN MATCHED THEN
        UPDATE SET
            delivery_address = source.delivery_address,
            delivery_city = source.delivery_city,
            delivery_state = source.delivery_state,
            delivery_zipcode = source.delivery_zipcode,
            delivery_date = source.delivery_date,
            delivery_time = source.delivery_time,
            delivery_instructions = source.delivery_instructions,
            delivery_status = source.delivery_status,
            delivery_fee = source.delivery_fee,
            recipient_name = source.recipient_name,
            recipient_phone = source.recipient_phone,
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (delivery_id, delivery_address, delivery_city, delivery_state,
                delivery_zipcode, delivery_date, delivery_time, delivery_instructions,
                delivery_status, delivery_fee, recipient_name, recipient_phone,
                created_at, updated_at)
        VALUES (source.delivery_id, source.delivery_address, source.delivery_city,
                source.delivery_state, source.delivery_zipcode, source.delivery_date,
                source.delivery_time, source.delivery_instructions, source.delivery_status,
                source.delivery_fee, source.recipient_name, source.recipient_phone,
                CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

    GET DIAGNOSTICS v_row_count = ROW_COUNT;
    INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, status, message)
    VALUES ('flower_shop_etl', CURRENT_TIMESTAMP(), 'INFO',
            'Processed ' || v_row_count || ' delivery records');

    -- Create stg_flower_shop__supplies table if it doesn't exist
    CREATE TABLE IF NOT EXISTS stg_flower_shop__supplies (
        supply_id VARCHAR(50) PRIMARY KEY,
        supply_name VARCHAR(200) NOT NULL,
        cost NUMBER(10,2),
        perishable BOOLEAN,
        sku VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    -- Insert/Update stg_flower_shop__supplies
    MERGE INTO stg_flower_shop__supplies AS target
    USING temp_stg_supplies AS source
    ON target.supply_id = source.supply_id
    WHEN MATCHED THEN
        UPDATE SET
            supply_name = source.supply_name,
            cost = source.cost,
            perishable = source.perishable,
            sku = source.sku,
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (supply_id, supply_name, cost, perishable, sku, created_at, updated_at)
        VALUES (source.supply_id, source.supply_name, source.cost, source.perishable,
                source.sku, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

    GET DIAGNOSTICS v_row_count = ROW_COUNT;
    INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, status, message)
    VALUES ('flower_shop_etl', CURRENT_TIMESTAMP(), 'INFO',
            'Processed ' || v_row_count || ' supply records');

    -- ====================
    -- STEP 3: Create intermediate tables (joins)
    -- ====================

    -- Check and create/truncate temp_int_flowers_orders_joined
    SELECT COUNT(*) INTO v_table_exists
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
      AND TABLE_NAME = 'TEMP_INT_FLOWERS_ORDERS_JOINED'
      AND TABLE_TYPE = 'BASE TABLE';

    IF (v_table_exists > 0) THEN
        TRUNCATE TABLE temp_int_flowers_orders_joined;
    ELSE
        CREATE TABLE temp_int_flowers_orders_joined (
            flower_order_id VARCHAR(50),
            customer_name VARCHAR(200),
            customer_email VARCHAR(200),
            customer_phone VARCHAR(50),
            arrangement_id VARCHAR(50),
            arrangement_name VARCHAR(200),
            arrangement_description TEXT,
            arrangement_base_price NUMBER(10,2),
            flower_ids TEXT,
            flower_quantities TEXT,
            size_category VARCHAR(20),
            occasion_type VARCHAR(50),
            is_custom BOOLEAN,
            quantity INTEGER,
            total_amount NUMBER(10,2),
            delivery_id VARCHAR(50),
            delivery_address TEXT,
            delivery_city VARCHAR(100),
            delivery_state VARCHAR(50),
            delivery_zipcode VARCHAR(20),
            delivery_date DATE,
            delivery_time VARCHAR(50),
            delivery_instructions TEXT,
            delivery_status VARCHAR(50),
            delivery_fee NUMBER(10,2),
            recipient_name VARCHAR(200),
            recipient_phone VARCHAR(50),
            occasion VARCHAR(100),
            promo_code VARCHAR(50),
            discount_amount NUMBER(10,2),
            order_date TIMESTAMP,
            order_status VARCHAR(50),
            net_product_amount NUMBER(10,2),
            pricing_tier VARCHAR(20),
            overall_status VARCHAR(20),
            processed_at TIMESTAMP
        );
    END IF;

    INSERT INTO temp_int_flowers_orders_joined
    SELECT
        fo.flower_order_id,
        fo.customer_name,
        fo.customer_email,
        fo.customer_phone,
        fo.arrangement_id,
        fa.arrangement_name,
        fa.description as arrangement_description,
        fa.base_price as arrangement_base_price,
        fa.flower_ids,
        fa.flower_quantities,
        fa.size_category,
        fa.occasion_type,
        fa.is_custom,
        fo.quantity,
        fo.total_amount,
        fo.delivery_id,
        di.delivery_address,
        di.delivery_city,
        di.delivery_state,
        di.delivery_zipcode,
        di.delivery_date,
        di.delivery_time,
        di.delivery_instructions,
        di.delivery_status,
        di.delivery_fee,
        di.recipient_name,
        di.recipient_phone,
        fo.occasion,
        fo.promo_code,
        fo.discount_amount,
        fo.order_date,
        fo.order_status,
        -- Calculated fields
        (fo.total_amount - COALESCE(fo.discount_amount, 0) - COALESCE(di.delivery_fee, 0)) as net_product_amount,
        CASE
            WHEN fo.discount_amount > 0 THEN 'DISCOUNTED'
            ELSE 'FULL_PRICE'
        END as pricing_tier,
        CASE
            WHEN di.delivery_status = 'delivered' AND fo.order_status = 'delivered' THEN 'COMPLETED'
            WHEN di.delivery_status = 'in_transit' OR fo.order_status = 'preparing' THEN 'IN_PROGRESS'
            WHEN di.delivery_status = 'pending' OR fo.order_status = 'confirmed' THEN 'PENDING'
            ELSE 'OTHER'
        END as overall_status,
        CURRENT_TIMESTAMP() as processed_at
    FROM temp_stg_flower_orders fo
    LEFT JOIN temp_stg_flower_arrangements fa
        ON fo.arrangement_id = fa.arrangement_id
    LEFT JOIN temp_stg_delivery_info di
        ON fo.delivery_id = di.delivery_id;

    -- Data quality checks for joined data
    SELECT COUNT(*) INTO v_row_count
    FROM temp_int_flowers_orders_joined
    WHERE arrangement_name IS NULL;

    IF (v_row_count > 0) THEN
        INSERT INTO DATA_QUALITY_ISSUES (table_name, issue_type, issue_count, detected_at)
        VALUES ('int_flowers_orders_joined', 'MISSING_ARRANGEMENT', v_row_count, CURRENT_TIMESTAMP());
    END IF;

    -- Create int_flower_shop__orders_joined table if it doesn't exist
    CREATE TABLE IF NOT EXISTS int_flower_shop__orders_joined (
        flower_order_id VARCHAR(50) PRIMARY KEY,
        customer_name VARCHAR(200),
        customer_email VARCHAR(200) NOT NULL,
        customer_phone VARCHAR(50),
        arrangement_id VARCHAR(50),
        arrangement_name VARCHAR(200),
        arrangement_description TEXT,
        arrangement_base_price NUMBER(10,2),
        flower_ids TEXT,
        flower_quantities TEXT,
        size_category VARCHAR(20),
        occasion_type VARCHAR(50),
        is_custom BOOLEAN,
        quantity INTEGER,
        total_amount NUMBER(10,2),
        delivery_id VARCHAR(50),
        delivery_address TEXT,
        delivery_city VARCHAR(100),
        delivery_state VARCHAR(50),
        delivery_zipcode VARCHAR(20),
        delivery_date DATE,
        delivery_time VARCHAR(50),
        delivery_instructions TEXT,
        delivery_status VARCHAR(50),
        delivery_fee NUMBER(10,2),
        recipient_name VARCHAR(200),
        recipient_phone VARCHAR(50),
        occasion VARCHAR(100),
        promo_code VARCHAR(50),
        discount_amount NUMBER(10,2),
        order_date TIMESTAMP,
        order_status VARCHAR(50),
        net_product_amount NUMBER(10,2),
        pricing_tier VARCHAR(20),
        overall_status VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    -- Insert/Update int_flower_shop__orders_joined
    MERGE INTO int_flower_shop__orders_joined AS target
    USING temp_int_flowers_orders_joined AS source
    ON target.flower_order_id = source.flower_order_id
    WHEN MATCHED THEN
        UPDATE SET
            customer_name = source.customer_name,
            customer_email = source.customer_email,
            customer_phone = source.customer_phone,
            arrangement_id = source.arrangement_id,
            arrangement_name = source.arrangement_name,
            arrangement_description = source.arrangement_description,
            arrangement_base_price = source.arrangement_base_price,
            flower_ids = source.flower_ids,
            flower_quantities = source.flower_quantities,
            size_category = source.size_category,
            occasion_type = source.occasion_type,
            is_custom = source.is_custom,
            quantity = source.quantity,
            total_amount = source.total_amount,
            delivery_id = source.delivery_id,
            delivery_address = source.delivery_address,
            delivery_city = source.delivery_city,
            delivery_state = source.delivery_state,
            delivery_zipcode = source.delivery_zipcode,
            delivery_date = source.delivery_date,
            delivery_time = source.delivery_time,
            delivery_instructions = source.delivery_instructions,
            delivery_status = source.delivery_status,
            delivery_fee = source.delivery_fee,
            recipient_name = source.recipient_name,
            recipient_phone = source.recipient_phone,
            occasion = source.occasion,
            promo_code = source.promo_code,
            discount_amount = source.discount_amount,
            order_date = source.order_date,
            order_status = source.order_status,
            net_product_amount = source.net_product_amount,
            pricing_tier = source.pricing_tier,
            overall_status = source.overall_status,
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (flower_order_id, customer_name, customer_email, customer_phone,
                arrangement_id, arrangement_name, arrangement_description, arrangement_base_price,
                flower_ids, flower_quantities, size_category, occasion_type, is_custom,
                quantity, total_amount, delivery_id, delivery_address, delivery_city,
                delivery_state, delivery_zipcode, delivery_date, delivery_time,
                delivery_instructions, delivery_status, delivery_fee, recipient_name,
                recipient_phone, occasion, promo_code, discount_amount, order_date,
                order_status, net_product_amount, pricing_tier, overall_status,
                created_at, updated_at)
        VALUES (source.flower_order_id, source.customer_name, source.customer_email,
                source.customer_phone, source.arrangement_id, source.arrangement_name,
                source.arrangement_description, source.arrangement_base_price, source.flower_ids,
                source.flower_quantities, source.size_category, source.occasion_type,
                source.is_custom, source.quantity, source.total_amount, source.delivery_id,
                source.delivery_address, source.delivery_city, source.delivery_state,
                source.delivery_zipcode, source.delivery_date, source.delivery_time,
                source.delivery_instructions, source.delivery_status, source.delivery_fee,
                source.recipient_name, source.recipient_phone, source.occasion,
                source.promo_code, source.discount_amount, source.order_date,
                source.order_status, source.net_product_amount, source.pricing_tier,
                source.overall_status, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

    GET DIAGNOSTICS v_row_count = ROW_COUNT;
    INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, status, message)
    VALUES ('flower_shop_etl', CURRENT_TIMESTAMP(), 'INFO',
            'Processed ' || v_row_count || ' joined order records');

    -- ====================
    -- STEP 4: Final data validation and business rule checks
    -- ====================

    -- Check for orders with missing arrangements
    SELECT COUNT(*) INTO v_row_count
    FROM int_flower_shop__orders_joined
    WHERE arrangement_name IS NULL;

    IF (v_row_count > 0) THEN
        INSERT INTO DATA_QUALITY_ISSUES (table_name, issue_type, issue_count, detected_at)
        VALUES ('int_flower_shop__orders_joined', 'ORPHANED_ORDERS', v_row_count, CURRENT_TIMESTAMP());
    END IF;

    -- Check for negative net amounts
    SELECT COUNT(*) INTO v_row_count
    FROM int_flower_shop__orders_joined
    WHERE net_product_amount < 0;

    IF (v_row_count > 0) THEN
        INSERT INTO DATA_QUALITY_ISSUES (table_name, issue_type, issue_count, detected_at)
        VALUES ('int_flower_shop__orders_joined', 'NEGATIVE_NET_AMOUNT', v_row_count, CURRENT_TIMESTAMP());
    END IF;

    -- Check for future order dates
    SELECT COUNT(*) INTO v_row_count
    FROM int_flower_shop__orders_joined
    WHERE order_date > CURRENT_DATE();

    IF (v_row_count > 0) THEN
        INSERT INTO DATA_QUALITY_ISSUES (table_name, issue_type, issue_count, detected_at)
        VALUES ('int_flower_shop__orders_joined', 'FUTURE_ORDER_DATE', v_row_count, CURRENT_TIMESTAMP());
    END IF;

    -- Create processing stats table if it doesn't exist
    CREATE TABLE IF NOT EXISTS PROCESSING_STATS (
        stat_id NUMBER AUTOINCREMENT PRIMARY KEY,
        table_name VARCHAR(100),
        record_count INTEGER,
        processing_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );

    -- Update processing statistics
    INSERT INTO PROCESSING_STATS (table_name, record_count, processing_date)
    SELECT 'stg_flower_shop__flowers', COUNT(*), CURRENT_DATE() FROM stg_flower_shop__flowers
    UNION ALL
    SELECT 'stg_flower_shop__flower_arrangements', COUNT(*), CURRENT_DATE() FROM stg_flower_shop__flower_arrangements
    UNION ALL
    SELECT 'stg_flower_shop__flower_orders', COUNT(*), CURRENT_DATE() FROM stg_flower_shop__flower_orders
    UNION ALL
    SELECT 'stg_flower_shop__delivery_info', COUNT(*), CURRENT_DATE() FROM stg_flower_shop__delivery_info
    UNION ALL
    SELECT 'stg_flower_shop__supplies', COUNT(*), CURRENT_DATE() FROM stg_flower_shop__supplies
    UNION ALL
    SELECT 'int_flower_shop__orders_joined', COUNT(*), CURRENT_DATE() FROM int_flower_shop__orders_joined;

    -- Clean up temporary tables
    DROP TABLE IF EXISTS temp_stg_flowers;
    DROP TABLE IF EXISTS temp_stg_flower_arrangements;
    DROP TABLE IF EXISTS temp_stg_flower_orders;
    DROP TABLE IF EXISTS temp_stg_delivery_info;
    DROP TABLE IF EXISTS temp_stg_supplies;
    DROP TABLE IF EXISTS temp_int_flowers_orders_joined;

    -- Log successful completion
    v_end_time := CURRENT_TIMESTAMP();
    INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, end_time, status, message)
    VALUES ('flower_shop_etl', v_start_time, v_end_time, 'COMPLETED',
            'Flower shop ETL completed successfully in ' ||
            DATEDIFF('second', v_start_time, v_end_time) || ' seconds');

    RETURN 'SUCCESS: Flower shop ETL completed successfully at ' || v_end_time;

EXCEPTION
    WHEN OTHER THEN
        v_procedure_status := 'FAILED';
        v_error_message := SQLERRM;

        INSERT INTO ETL_AUDIT_LOG (procedure_name, start_time, end_time, status, message)
        VALUES ('flower_shop_etl', v_start_time, CURRENT_TIMESTAMP(), 'FAILED', v_error_message);

        RETURN 'ERROR: ' || v_error_message;
END;
$$;

-- Example usage:
-- CALL flower_shop_etl();
--
-- To check the results:
-- SELECT * FROM ETL_AUDIT_LOG WHERE procedure_name = 'flower_shop_etl' ORDER BY created_at DESC;
-- SELECT * FROM DATA_QUALITY_ISSUES ORDER BY detected_at DESC;
-- SELECT * FROM PROCESSING_STATS WHERE processing_date = CURRENT_DATE();