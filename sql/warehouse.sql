-- Executed analytical warehouse: DuckDB. Source domains are deliberately separate.
CREATE TABLE dim_source(source_key INTEGER PRIMARY KEY, name VARCHAR, grain VARCHAR, labels_available BOOLEAN);
INSERT INTO dim_source VALUES (1,'REES46 October 2019','observed clickstream event',false),(2,'ULB Worldline','card transaction',true);

CREATE TEMP TABLE e AS SELECT source_row,event_ts,event_type,product_id,coalesce(category_id,-1) category_id,
 category_code,brand,price,user_id,user_session,brand_missing,category_missing
 FROM read_parquet('data/staging/events/*.parquet') WHERE is_valid;
CREATE TABLE rejected_events AS SELECT * FROM read_parquet('data/staging/events/*.parquet') WHERE NOT is_valid;

-- Version descriptive state in observed event order, including deterministic ties.
CREATE TEMP TABLE changes AS SELECT *,
 CASE WHEN lag(struct_pack(c:=category_id,n:=category_code,b:=brand)) OVER win1
 IS DISTINCT FROM struct_pack(c:=category_id,n:=category_code,b:=brand) THEN 1 ELSE 0 END change_flag
 FROM e WINDOW win1 AS(PARTITION BY product_id ORDER BY event_ts,source_row);
CREATE TEMP TABLE ev AS SELECT *,sum(change_flag) OVER(PARTITION BY product_id ORDER BY event_ts,source_row ROWS UNBOUNDED PRECEDING)::BIGINT product_version FROM changes;
CREATE TABLE dim_category_group(group_key BIGINT PRIMARY KEY,group_name VARCHAR UNIQUE);
INSERT INTO dim_category_group SELECT row_number() OVER(ORDER BY g),g FROM (SELECT DISTINCT split_part(category_code,'.',1) g FROM ev);
CREATE TABLE dim_category(category_key BIGINT PRIMARY KEY,source_category_id BIGINT,category_code VARCHAR,group_key BIGINT REFERENCES dim_category_group(group_key));
INSERT INTO dim_category SELECT row_number() OVER(ORDER BY category_id,category_code),category_id,category_code,g.group_key
 FROM (SELECT DISTINCT category_id,category_code FROM ev) c JOIN dim_category_group g ON g.group_name=split_part(c.category_code,'.',1);
CREATE TABLE dim_brand(brand_key BIGINT PRIMARY KEY,brand_name VARCHAR UNIQUE);
INSERT INTO dim_brand SELECT row_number() OVER(ORDER BY brand),brand FROM (SELECT DISTINCT brand FROM ev);
CREATE TABLE dim_product(product_key BIGINT PRIMARY KEY,source_key INTEGER REFERENCES dim_source(source_key),product_id BIGINT,
 product_version BIGINT,category_key BIGINT REFERENCES dim_category(category_key),brand_key BIGINT REFERENCES dim_brand(brand_key),
 effective_ts TIMESTAMP, effective_event_id BIGINT, expiry_ts TIMESTAMP,expiry_event_id BIGINT,is_current BOOLEAN,
 UNIQUE(product_id,product_version));
INSERT INTO dim_product
WITH states AS(SELECT product_id,product_version,category_id,category_code,brand,min(event_ts) start_ts,
 arg_min(source_row,struct_pack(t:=event_ts,r:=source_row)) start_row FROM ev GROUP BY ALL),
validity AS(SELECT *,lead(start_ts) OVER win2 end_ts,lead(start_row) OVER win2 end_row FROM states WINDOW win2 AS(PARTITION BY product_id ORDER BY product_version))
SELECT row_number() OVER(ORDER BY product_id,product_version),1,product_id,product_version,c.category_key,b.brand_key,start_ts,start_row,end_ts,end_row,end_ts IS NULL
FROM validity v JOIN dim_category c ON v.category_id=c.source_category_id AND v.category_code=c.category_code JOIN dim_brand b ON b.brand_name=v.brand;

CREATE TABLE dim_user(user_key BIGINT PRIMARY KEY,source_key INTEGER REFERENCES dim_source(source_key),user_id BIGINT UNIQUE);
INSERT INTO dim_user SELECT row_number() OVER(ORDER BY user_id),1,user_id FROM(SELECT DISTINCT user_id FROM ev);
CREATE TEMP TABLE gaps AS SELECT *,epoch(event_ts-lag(event_ts) OVER win3) gap,
 CASE WHEN lag(product_id) OVER win3=product_id AND lag(event_type) OVER win3=event_type AND lag(event_ts) OVER win3=event_ts THEN 1 ELSE 0 END repeated_same_second
 FROM ev WINDOW win3 AS(PARTITION BY user_id,user_session ORDER BY event_ts,source_row);
CREATE TEMP TABLE visits AS SELECT *,sum(CASE WHEN gap IS NULL OR gap>1800 THEN 1 ELSE 0 END)
 OVER(PARTITION BY user_id,user_session ORDER BY event_ts,source_row ROWS UNBOUNDED PRECEDING)::BIGINT visit_no FROM gaps;
CREATE TABLE dim_session(session_key BIGINT PRIMARY KEY,user_key BIGINT REFERENCES dim_user(user_key),source_session_id VARCHAR,
 visit_no BIGINT,start_ts TIMESTAMP,end_ts TIMESTAMP,UNIQUE(user_key,source_session_id,visit_no));
INSERT INTO dim_session SELECT row_number() OVER(ORDER BY v.user_id,user_session,visit_no),u.user_key,user_session,visit_no,min(event_ts),max(event_ts)
 FROM visits v JOIN dim_user u ON u.user_id=v.user_id GROUP BY v.user_id,u.user_key,user_session,visit_no;
CREATE TABLE dim_date(date_key INTEGER PRIMARY KEY,calendar_date DATE UNIQUE,year INTEGER,month INTEGER,day INTEGER,iso_week INTEGER,weekday INTEGER);
INSERT INTO dim_date SELECT strftime(d,'%Y%m%d')::INTEGER,d,year(d),month(d),day(d),week(d),isodow(d)
FROM(SELECT DISTINCT event_ts::DATE d FROM ev);
CREATE TABLE dim_time(time_key INTEGER PRIMARY KEY,hour INTEGER,minute INTEGER);
INSERT INTO dim_time SELECT i,i//60,i%60 FROM range(1440) t(i);
CREATE TABLE dim_event_type(event_type_key INTEGER PRIMARY KEY,event_type VARCHAR UNIQUE);
INSERT INTO dim_event_type VALUES(1,'view'),(2,'cart'),(3,'purchase'),(4,'remove_from_cart');
CREATE TABLE fact_event(source_event_id BIGINT PRIMARY KEY,source_key INTEGER REFERENCES dim_source(source_key),
 event_ts TIMESTAMP,event_date DATE,date_key INTEGER REFERENCES dim_date(date_key),time_key INTEGER REFERENCES dim_time(time_key),
 event_type_key INTEGER REFERENCES dim_event_type(event_type_key),product_key BIGINT REFERENCES dim_product(product_key),
 session_key BIGINT REFERENCES dim_session(session_key),price DECIMAL(18,2),brand_missing BOOLEAN,category_missing BOOLEAN,
 gap_seconds DOUBLE,repeated_same_second INTEGER,CHECK(price>=0));
INSERT INTO fact_event SELECT v.source_row,1,v.event_ts,v.event_ts::DATE,strftime(v.event_ts,'%Y%m%d')::INTEGER,
 hour(v.event_ts)*60+minute(v.event_ts),t.event_type_key,p.product_key,s.session_key,v.price,v.brand_missing,v.category_missing,
 CASE WHEN v.gap>1800 THEN NULL ELSE v.gap END,v.repeated_same_second
 FROM visits v JOIN dim_product p USING(product_id,product_version)
 JOIN dim_user u ON u.user_id=v.user_id
 JOIN dim_session s ON s.user_key=u.user_key AND s.source_session_id=v.user_session AND s.visit_no=v.visit_no
 JOIN dim_event_type t ON t.event_type=v.event_type;

-- No exact calendar or customer linkage is invented for ULB's elapsed seconds.
CREATE TABLE dim_elapsed_period(period_key INTEGER PRIMARY KEY,relative_day INTEGER,hour_in_day INTEGER);
INSERT INTO dim_elapsed_period SELECT i+1,i//24,i%24 FROM range(49) t(i);
CREATE TABLE fact_card_transaction(transaction_key BIGINT PRIMARY KEY,source_key INTEGER REFERENCES dim_source(source_key),
 elapsed_seconds DOUBLE,period_key INTEGER REFERENCES dim_elapsed_period(period_key),amount DOUBLE,pca_features DOUBLE[]);
CREATE TABLE card_outcome(transaction_key BIGINT PRIMARY KEY REFERENCES fact_card_transaction(transaction_key),is_fraud INTEGER CHECK(is_fraud IN (0,1)));
CREATE TEMP TABLE card AS SELECT row_number() OVER() transaction_key,* FROM read_csv_auto('data/raw/creditcard.csv');
INSERT INTO fact_card_transaction SELECT transaction_key,2,Time,floor(Time/3600)::INTEGER+1,Amount,
 [V1,V2,V3,V4,V5,V6,V7,V8,V9,V10,V11,V12,V13,V14,V15,V16,V17,V18,V19,V20,V21,V22,V23,V24,V25,V26,V27,V28] FROM card;
INSERT INTO card_outcome SELECT transaction_key,Class FROM card;
CREATE TABLE metadata_measure(measure VARCHAR,definition VARCHAR,source_key INTEGER REFERENCES dim_source(source_key));
INSERT INTO metadata_measure VALUES ('event_count','Count of observed events; not unique orders',1),
 ('purchase_event_value','Sum of observed purchase-event price; quantity, settlement, currency code and returns unavailable',1),
 ('session_conversion','Visits containing >=1 purchase / visits in the explicitly stated cohort',1),
 ('card_amount','Source transaction amount; do not combine monetarily with REES46 price',2),
 ('fraud_label','ULB source Class: 1 fraud, 0 normal; not available for REES46',2);
