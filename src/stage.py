"""PySpark schema validation, explicit quality flags, and typed staging."""
import json,time
from pathlib import Path
from pyspark.sql import SparkSession,functions as F,types as T
ROOT=Path(__file__).resolve().parents[1]

def run():
    t=time.perf_counter()
    spark=(SparkSession.builder.master('local[2]').appName('ITCS544-staging')
           .config('spark.driver.memory','2g').config('spark.sql.shuffle.partitions','8')
           .config('spark.sql.session.timeZone','UTC').config('spark.ui.enabled','false').getOrCreate())
    spark.sparkContext.setLogLevel('ERROR')
    schema=T.StructType([T.StructField(x,T.StringType()) for x in
       ['source_row','event_time','event_type','product_id','category_id','category_code','brand','price','user_id','user_session']])
    raw=spark.read.option('header',True).schema(schema).csv(str(ROOT/'data/staging/sample.csv'))
    df=(raw.withColumn('source_row',F.col('source_row').cast('long'))
        .withColumn('event_ts',F.to_timestamp('event_time',"yyyy-MM-dd HH:mm:ss 'UTC'"))
        .withColumn('product_id',F.col('product_id').cast('long'))
        .withColumn('category_id',F.col('category_id').cast('long'))
        .withColumn('user_id',F.col('user_id').cast('long'))
        .withColumn('price',F.col('price').cast('decimal(18,2)'))
        .withColumn('brand_missing',F.col('brand').isNull())
        .withColumn('category_missing',F.col('category_code').isNull())
        .withColumn('brand',F.coalesce('brand',F.lit('Unknown')))
        .withColumn('category_code',F.coalesce('category_code',F.lit('Unknown'))))
    valid=(F.col('event_ts').isNotNull() & F.col('product_id').isNotNull() & F.col('user_id').isNotNull()
           & F.col('user_session').isNotNull() & F.col('price').isNotNull() & (F.col('price')>=0)
           & F.col('event_type').isin('view','cart','purchase','remove_from_cart'))
    df=df.withColumn('is_valid',F.coalesce(valid,F.lit(False)))
    # Identical observed events are retained: no retry ID exists to prove duplication.
    df.repartition(8).write.mode('overwrite').parquet(str(ROOT/'data/staging/events'))
    profile=df.agg(F.count('*').alias('sample_rows'),F.sum(F.col('is_valid').cast('int')).alias('valid_rows'),
         F.sum(F.col('brand_missing').cast('int')).alias('brand_missing'),
         F.sum(F.col('category_missing').cast('int')).alias('category_missing')).first().asDict()
    profile['seconds']=time.perf_counter()-t
    (ROOT/'results/staging_quality.json').write_text(json.dumps(profile,indent=2,default=str))
    print(profile,flush=True);spark.stop()

if __name__=='__main__':run()
