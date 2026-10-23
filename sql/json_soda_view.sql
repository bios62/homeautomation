create or replace view json_stats AS
/*  Extracting allsensorstats */
SELECT 
    'allsensorstats' AS STATNAME,
    sensorname       AS LABEL,
    TO_CHAR(temp)    AS VALUE1,
    time             AS VALUE2,
    created_on,
    id
FROM jiotlogs l,
JSON_TABLE(l.json_document, '$.allsensorstats[*]'
    COLUMNS (
        sensorname VARCHAR2(50) PATH '$.sensorname',
        temp       NUMBER       PATH '$.temp',
        time       VARCHAR2(50) PATH '$.time'
    )
) jt

UNION ALL

/* Extracting tpSockets */
SELECT 
    'tpSockets'      AS STATNAME,
    device           AS LABEL,
    relay_state      AS VALUE1,
    ip_address       AS VALUE2, -- Sockets don't have a top-level timestamp in your JSON
    created_on,
    id
FROM jiotlogs l,
JSON_TABLE(l.json_document, '$.tpSockets.*'
    COLUMNS (
        device      VARCHAR2(50) PATH '$.device',
        relay_state VARCHAR2(50) PATH '$.relay_state',
        ip_address  VARCHAR2(50) PATH '$.ipAddress'
    )
) jt

UNION ALL

/* Extracting ipaddresses */
SELECT 
    'ipaddresses'    AS STATNAME,
    'Cloud1'         AS LABEL,
    ip               AS VALUE1,
    'NA'             AS VALUE2,
    created_on,
    id
FROM jiotlogs l,
JSON_TABLE(l.json_document, '$.ipaddresses.ipaddressFromCloud1'
    COLUMNS (
        ip VARCHAR2(50) PATH '$.ip'
    )
) jt

UNION ALL

/* Extracting sensorstats (Object-based) */
SELECT 
    'sensorstats'    AS STATNAME,
    timestamp_lbl    AS LABEL, -- Using the JSON key 'timestamp' as label per your data
    TO_CHAR(temp)    AS VALUE1,
    'NA'             AS VALUE2,
    created_on,
    id
FROM jiotlogs l,
JSON_TABLE(l.json_document, '$.sensorstats.*'
    COLUMNS (
        temp          NUMBER       PATH '$.temp',
        timestamp_lbl VARCHAR2(50) PATH '$.timestamp'
    )
) jt

/* Extracting stats (old style) */
union ALL
SELECT
    'tempstats'    AS STATNAME,
    jt.roomname    AS LABEL,
    jt.temp        AS VALUE1,
    jt.time        AS VALUE2,
    CREATED_ON,
    id
FROM
    jiotlogs l,
    JSON_TABLE(
        l.json_document,
        '$.temp[*]'
        COLUMNS (
            roomname VARCHAR2(50) PATH '$.roomname',
            temp     VARCHAR2(30) PATH '$.temp',
            time     VARCHAR2(50) PATH '$.time'
        )
    ) jt
;


select * from json_stats where created_on =(select max(created_on) from jiotlogs);
Select id from jiotlogs where created_on = (select max(created_on) from jiotlogs);