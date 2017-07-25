DROP PROCEDURE IF EXISTS temp_ww_prog;
DELIMITER //
CREATE PROCEDURE temp_ww_prog()
BEGIN
drop table if exists PROG_AFFINITY_AGG_YR;
SELECT 'MSG: drop table PROG_AFFINITY_AGG_YR done at',curtime();

/*
update fact_tg_affinity_agg_wk SET CALENDAR_YEAR = (CALENDAR_YEAR - 1) where 
	(MONTH IN ('Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec') or (MONTH='JAN' and BARC_WEEK>=50));
commit;
*/
UPDATE FACT_TG_AFFINITY_AGG_WK set WEEK_KEY = CONCAT(CALENDAR_YEAR,lpad(BARC_WEEK,2,0));
SELECT 'MSG: UPDTAE WEEK_KEY DONE at ', curtime();
commit;

/*
DELETE from fact_tg_affinity_agg_wk where week_key<=(select min_key from(select max(week_key)-200 min_key from FACT_TG_AFFINITY_AGG_WK)max_val);
commit;
*/

SELECT 'MSG: Unlock table DONE at ', curtime();

create table PROG_AFFINITY_AGG_YR ENGINE = MYISAM as 
(
select 
	GENRE_DISPLAY_NAME, GENRE_KEY, 
    NETWORK_DISPLAY_NAME, NETWORK_KEY, 
	CHANNEL_GROUP_DISPLAY_NAME, CHANNEL_GROUP_KEY, 
    WEEK_KEY, ADVERTISERS_GROUP_KEY, ADVERTISERS_GROUP_DISPLAY_NAME, TG_KEY, MARKET_KEY,
	sum(ADGRP) ADGRP, sum(FCT) FCT, sum(TVT) TVT
from FACT_TG_AFFINITY_AGG_WK
group by GENRE_KEY, NETWORK_KEY, CHANNEL_GROUP_KEY, TG_KEY, MARKET_KEY, WEEK_KEY, ADVERTISERS_GROUP_KEY);

SELECT 'MSG: TABLE CREATED FOR PROG_AFFINITY_AGG_YR; CREATING PARTITION',curtime();
ALTER TABLE PROG_AFFINITY_AGG_YR PARTITION BY KEY(TG_KEY, MARKET_KEY, ADVERTISERS_GROUP_KEY) PARTITIONS 300;

SELECT 'MSG: CREATING INDEX idx_week_key_prog at', curtime();
ALTER TABLE PROG_AFFINITY_AGG_YR ADD KEY idx_week_key_pog (WEEK_KEY) USING BTREE;
/*
SELECT 'MSG: CREATING INDEX idx_tg_mkt_prog at', curtime();
ALTER TABLE PROG_AFFINITY_AGG_YR ADD KEY idx_tg_mkt_prog (SOURCE_TG_NAME) USING HASH;
*/
/*
SELECT 'MSG: CREATING INDEX idx_gnt_ntwk at', curtime();
ALTER TABLE PROG_AFFINITY_AGG_YR ADD KEY idx_gntgmkt (GENRE_KEY, NETWORK_KEY) USING BTREE;

SELECT 'MSG: CREATING INDEX idx_chnl_gnr at', curtime();
ALTER TABLE PROG_AFFINITY_AGG_YR ADD KEY idx_afnty_chnl(CHANNEL_GROUP_KEY, GENRE_KEY) USING BTREE;

SELECT 'MSG: CREATING INDEX idx_advt_key at', curtime();
ALTER TABLE PROG_AFFINITY_AGG_YR ADD KEY idx_advt (ADVERTISERS_GROUP_KEY) USING HASH;
*/
SELECT COUNT(*) FROM PROG_AFFINITY_AGG_YR;

drop table if exists genre_channel_afnty;
/* table for genre channel affinity calculations */
SELECT 'MSG: CREATING Table genre_channel_afnty at', curtime();
create table genre_channel_afnty ENGINE = MYISAM as 
(
select 
	GENRE_DISPLAY_NAME, GENRE_KEY, 
    NETWORK_DISPLAY_NAME, NETWORK_KEY, 
	CHANNEL_GROUP_DISPLAY_NAME, CHANNEL_GROUP_KEY, 
    WEEK_KEY, TG_KEY, MARKET_KEY,
	sum(ADGRP) ADGRP, sum(FCT) FCT, sum(TVT) TVT
from PROG_AFFINITY_AGG_YR
group by GENRE_KEY, NETWORK_KEY, CHANNEL_GROUP_KEY, TG_KEY, MARKET_KEY, WEEK_KEY);

SELECT 'MSG: TABLE CREATED FOR genre_channel_afnty; CREATING PARTITION',curtime();
ALTER TABLE genre_channel_afnty PARTITION BY KEY(TG_KEY, MARKET_KEY) PARTITIONS 60;

SELECT 'MSG: CREATING INDEX idx_week_key_prog at', curtime();
ALTER TABLE genre_channel_afnty ADD KEY idx_week_key_pog (WEEK_KEY) USING BTREE;
/*
SELECT 'MSG: CREATING INDEX idx_chnl_gnr at', curtime();
ALTER TABLE genre_channel_afnty ADD KEY idx_afnty_chnl(CHANNEL_GROUP_KEY, GENRE_KEY) USING HASH;

SELECT 'MSG: CREATING INDEX idx_gnt_ntwk at', curtime();
ALTER TABLE genre_channel_afnty ADD KEY idx_gntgmkt (GENRE_KEY, NETWORK_KEY) USING HASH;
*/
SELECT 'MSG: Running show_prog table scripts at', curtime();

drop table if exists show_prog;
create table show_prog ENGINE = MYISAM as 
	SELECT TG_KEY, MARKET_KEY, PROGRAM_GROUP_KEY, PROGRAM_GROUP_DISPLAY_NAME, 
	CHANNEL_GROUP_KEY, CHANNEL_GROUP_DISPLAY_NAME,
	NETWORK_DISPLAY_NAME, GENRE_DISPLAY_NAME,
	WEEK_KEY, sum(ADGRP) ADGRP, sum(FCT) FCT, sum(TVT) TVT  
	FROM fact_tg_affinity_agg_wk 
	group by TG_KEY, MARKET_KEY, PROGRAM_GROUP_KEY, CHANNEL_GROUP_KEY,
	WEEK_KEY;


SELECT 'MSG: TABLE CREATED FOR star_network; CREATING PARTITION',curtime();
ALTER TABLE show_prog PARTITION BY KEY(TG_KEY, MARKET_KEY) PARTITIONS 256;

SELECT 'MSG: CREATING INDEX idx_week_key_prog at', curtime();
ALTER TABLE show_prog ADD KEY idx_week_key_pog (WEEK_KEY) USING BTREE;

SELECT 'MSG: Running show_afnty table scripts at', curtime();

END//
DELIMITER ;

DROP PROCEDURE IF EXISTS temp_ww_afnty;
DELIMITER //
CREATE PROCEDURE temp_ww_afnty()
BEGIN
drop table if exists show_affinity;
create table show_affinity ENGINE = MYISAM as 
(	select star.* from
	(SELECT TG_KEY, MARKET_KEY, PROGRAM_GROUP_KEY, PROGRAM_GROUP_DISPLAY_NAME, CHANNEL_GROUP_KEY, 
		CHANNEL_GROUP_DISPLAY_NAME, WEEK_KEY, ADGRP, FCT, TVT
	FROM show_prog)star 
	JOIN
	ref_ch_group_tg_mkt ref
	where star.TG_KEY=ref.TG_KEY and star.MARKET_KEY=ref.MARKET_KEY 
	and star.CHANNEL_GROUP_KEY=ref.CHANNEL_GROUP_KEY);

SELECT 'MSG: TABLE CREATED FOR show_affinity; CREATING PARTITION',curtime();
ALTER TABLE show_affinity PARTITION BY KEY(TG_KEY, MARKET_KEY) PARTITIONS 128;

SELECT 'MSG: CREATING INDEX idx_week_key at', curtime();
ALTER TABLE show_affinity ADD KEY idx_week_key (WEEK_KEY) USING BTREE;

drop table if exists ww_channel_affinity;
create table ww_channel_affinity ENGINE = MYISAM as 
(select chnl.* from
            (select CHANNEL_GROUP_KEY, CHANNEL_GROUP_DISPLAY_NAME, 
            TG_KEY, MARKET_KEY, GENRE_KEY, GENRE_DISPLAY_NAME, WEEK_KEY, ADGRP, FCT, TVT from 
            genre_channel_afnty)chnl
            JOIN
            ref_ch_group_tg_mkt ref
            where ref.CHANNEL_GROUP_KEY=chnl.CHANNEL_GROUP_KEY 
            and ref.TG_KEY=chnl.TG_KEY 
            and ref.MARKET_KEY=chnl.MARKET_KEY);

drop table if exists ww_genre_affinity;
create table ww_genre_affinity ENGINE = MYISAM as 
(select gnr.GENRE_KEY, gnr.GENRE_DISPLAY_NAME, 
            gnr.NETWORK_KEY, NETWORK_DISPLAY_NAME, 
            gnr.WEEK_KEY, SUM(ADGRP)ADGRP, SUM(FCT)FCT, SUM(TVT)TVT from
            genre_channel_afnty gnr 
            JOIN 
            ref_genre_tg_mkt ref
            where ref.GENRE_KEY=gnr.GENRE_KEY 
            and ref.TG_KEY=gnr.TG_KEY 
            and ref.MARKET_KEY=gnr.MARKET_KEY group by GENRE_KEY, NETWORK_KEY, WEEK_KEY);

END//
DELIMITER ;

