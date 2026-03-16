# DataWorks Node Types — Complete Catalog

All 100+ node types from `CodeProgramType` enum in https://github.com/aliyun/dataworks-spec.

Use `catalog/node_types.yaml` for the curated subset with templates.
Use this file when you encounter an uncommon node type not in the YAML catalog.

## MaxCompute (ODPS)

| command | code | language | ext | content_format |
|---------|------|----------|-----|----------------|
| `ODPS_SQL` | 10 | `odps-sql` | .sql | plain_text |
| `ODPS_SPARK_SQL` | 226 | `odps-sql` | .sql | plain_text |
| `ODPS_SQL_SCRIPT` | 24 | `odps-script` | .ms | plain_text |
| `PY_ODPS` | 221 | `python3` | .py | plain_text |
| `PYODPS3` | 1221 | `python3` | .py | plain_text |
| `ODPS_SPARK` | 225 | `json` | .mc.spark.json | spark_json |
| `ODPS_MR` | 11 | `json` | .mr.sql | complex_json |
| `ODPS_XLIB` | 8 | `python3` | .mc.xlib.py | plain_text |
| `ODPS_SHARK` | 223 | `json` | .mc.shark.json | complex_json |
| `LIGHTNING_SQL` | 61 | `odps-sql` | .sql | plain_text |
| `EXTREME_STORAGE` | 30 | `shell-script` | .sh | plain_text |
| `COMPONENT_SQL` | 1010 | `odps-sql` | .sql | plain_text |
| `SQL_COMPONENT` | 3010 | `odps-sql` | .sql | plain_text |
| `DataService_studio` | 238 | `json` | .json | complex_json |
| `HIVE` | 3 | `hive-sql` | .sql | plain_text |

Resources: `ODPS_PYTHON`(12), `ODPS_JAR`(13), `ODPS_ARCHIVE`(14), `ODPS_FILE`(15), `ODPS_DDL`(18)
Other: `ODPS_TABLE`(16), `ODPS_FUNCTION`(17)

## EMR

| command | code | language | ext | content_format |
|---------|------|----------|-----|----------------|
| `EMR_HIVE` | 227 | `hive-sql` | .sql | emr_json |
| `EMR_SPARK_SQL` | 229 | `spark-sql` | .sql | emr_json |
| `EMR_SPARK` | 228 | `shell-script` | .sh | emr_json |
| `EMR_MR` | 230 | `shell-script` | .sh | emr_json |
| `EMR_SHELL` | 257 | `shell-script` | .sh | emr_json |
| `EMR_SPARK_SHELL` | 258 | `shell-script` | .sh | emr_json |
| `EMR_PRESTO` | 259 | `presto-sql` | .sql | emr_json |
| `EMR_IMPALA` | 260 | `impala-sql` | .sql | emr_json |
| `EMR_TRINO` | 267 | `trino-sql` | .sql | emr_json |
| `EMR_KYUUBI` | 268 | `spark-sql` | .sql | emr_json |
| `EMR_STREAMING_SQL` | 266 | `spark-sql` | .sql | emr_json |
| `EMR_SPARK_STREAMING` | 264 | `shell-script` | .sh | emr_json |
| `EMR_SCOOP` | 263 | — | — | emr_json |
| `EMR_HIVE_CLI` | 265 | `hive-sql` | — | emr_json |

Resources: `EMR_JAR`(231), `EMR_FILE`(232)

## Serverless Spark

| command | code | language |
|---------|------|----------|
| `SERVERLESS_SPARK_BATCH` | 2100 | `shell-script` |
| `SERVERLESS_SPARK_SQL` | 2101 | `spark-sql` |
| `SERVERLESS_SPARK_STREAMING` | 2102 | `shell-script` |
| `SERVERLESS_KYUUBI` | 2103 | `spark-sql` |

## CDH

| command | code | language | content_format |
|---------|------|----------|----------------|
| `CDH_HIVE` | 270 | `hive-sql` | emr_json (uses cdhJobConfig) |
| `CDH_SPARK` | 271 | `shell-script` | emr_json |
| `CDH_SPARK_SQL` | 272 | `spark-sql` | emr_json |
| `CDH_MR` | 273 | `shell-script` | emr_json |
| `CDH_SHELL` | 276 | `shell-script` | emr_json |
| `CDH_SPARK_SHELL` | 277 | `shell-script` | emr_json |
| `CDH_PRESTO` | 278 | `presto-sql` | emr_json |
| `CDH_IMPALA` | 279 | `impala-sql` | emr_json |

## Hologres

| command | code | language | content_format |
|---------|------|----------|----------------|
| `HOLOGRES_SQL` | 1093 | `hologres-sql` | plain_text |
| `HOLOGRES_DEVELOP` | 1091 | `hologres-sql` | plain_text |
| `HOLOGRES_SYNC_DDL` | 1094 | `json` | complex_json |
| `HOLOGRES_SYNC_DATA` | 1095 | `json` | complex_json |
| `HOLOGRES_SYNC_DATA_TO_MC` | 1070 | `json` | complex_json |

## Flink

| command | code | language | content_format |
|---------|------|----------|----------------|
| `FLINK_SQL_STREAM` | 2012 | `flink-sql` | complex_json |
| `FLINK_SQL_BATCH` | 2011 | `flink-sql` | complex_json |
| `BLINK_STREAM_SQL` | 2010 | `flink-sql` | complex_json |
| `BLINK_BATCH_SQL` | 2020 | `flink-sql` | complex_json |
| `BLINK_DATASTREAM` | 2019 | `java` | complex_json |

## Database SQL

All use engine `DATABASE`, content_format `plain_text`.

| command | code | language |
|---------|------|----------|
| `MySQL` | 1303 | `mysql-sql` |
| `POSTGRESQL` | 1302 | `postgresql-sql` |
| `Sql Server` | 1304 | `t-sql` |
| `Oracle` | 1305 | `plsql` |
| `StarRocks` | 1306 | `starrocks-sql` |
| `Doris` | 1308 | `doris-sql` |
| `DRDS` | 1307 | `mysql-sql` |
| `Mariadb` | 1309 | `mysql-sql` |
| `Selectdb` | 1310 | `doris-sql` |
| `Redshift` | 1311 | `postgresql-sql` |
| `Saphana` | 1312 | `sql` |
| `Vertica` | 1313 | `sql` |
| `OceanBase` | 1314 | `obmysql-sql` |
| `DB2` | 1315 | `sql` |
| `ADB for PostgreSQL` | 1316 | `postgresql-sql` |
| `ADB for MySQL` | 1317 | `adbmysql-sql` |
| `CLICK_SQL` | 1301 | `clickhouse-sql` |

## Script (General)

| command | code | language | content_format |
|---------|------|----------|----------------|
| `DIDE_SHELL` | 6 | `shell-script` | plain_text |
| `SHELL` | 2 | `shell-script` | plain_text |
| `PYTHON` | 1322 | `python3` | plain_text |
| `PERL` | 31 | `shell-script` | plain_text |
| `SSH` | 1321 | `shell-script` | plain_text |

## Control Flow

| command | code | special_field | content_format |
|---------|------|---------------|----------------|
| `VIRTUAL` | 99 | — | none |
| `CONTROLLER_BRANCH` | 1101 | `branch` | controller |
| `CONTROLLER_JOIN` | 1102 | `join` | controller |
| `CONTROLLER_ASSIGNMENT` | 1100 | — | plain_text (JSON) |
| `CONTROLLER_CYCLE` | 1103 | `do-while` | controller |
| `CONTROLLER_TRAVERSE` | 1106 | `for-each` | controller |
| `CONTROLLER_WAIT` | 1109 | — | controller |
| `PARAM_HUB` | 1115 | `param-hub` | controller |
| `COMBINED_NODE` | 98 | `combined` | controller |
| `SUB_PROCESS` | 1122 | — | none |
| `VIRTUAL_WORKFLOW` | 97 | — | none |
| `WORKFLOW` | 1001 | — | none |
| `SCHEDULER_TRIGGER` | 1114 | — | none |

## Data Integration

| command | code | content_format |
|---------|------|----------------|
| `DI` | 23 | di_json |
| `DATAX2` | 20 | di_json |
| `DATAX` | 4 | di_json |
| `CDP` | 22 | di_json |
| `RI` | 900 | di_json |
| `DT` | 21 | di_json |
| `DD_MERGE` | 222 | di_json |
| `TT_MERGE` | 200 | di_json |

## Algorithm / PAI

| command | code | language | content_format |
|---------|------|----------|----------------|
| `pai` | 1002 | `json` | complex_json |
| `pai_studio` | 1117 | `json` | complex_json |
| `PAI_FLOW` | 1250 | `yaml` | complex_json |
| `pai_dlc` | 1119 | `shell-script` | plain_text |
| `RECOMMEND_PLUS` | 1116 | `json` | complex_json |
| `alink` | 240 | `python3` | plain_text |
| `xlab` | 87 | `json` | complex_json |

## Other

| command | code | engine |
|---------|------|--------|
| `ADB Spark` | 1990 | ADB_SPARK |
| `ADB Spark SQL` | 1991 | ADB_SPARK |
| `CHECK` | 19 | General |
| `CHECK_NODE` | 241 | General |
| `FTP_CHECK` | 1320 | General |
| `OSS_INSPECT` | 239 | General |
| `CROSS_TENANTS` | 1089 | General |
| `CUSTOM` | 9999 | CUSTOM |
