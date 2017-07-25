DROP PROCEDURE IF EXISTS tg_affinity_wkl;
DELIMITER //
CREATE PROCEDURE tg_affinity_wkl(client_sel numeric, col_metric CHAR(40), tam_tg numeric,  tam_mkt numeric,  barc_tg numeric, barc_mkt numeric, cat_name CHAR(100), s_wek_ky numeric, e_wek_ky numeric)
BEGIN
-- set user variable
DECLARE prog_table CHAR(60);
DECLARE level_name CHAR(40);
DECLARE m_table_name CHAR(60);
DECLARE level_key CHAR(40);
DECLARE cat_key CHAR(40);
SET m_table_name = 'prog_affinity_agg_yr';
SET prog_table = 'prog_affinity_agg_yr';
if (cat_name='GENRE_DISPLAY_NAME') then
	SET level_name = 'NETWORK_DISPLAY_NAME';
    SET level_key = 'NETWORK_KEY';
    SET cat_key = 'GENRE_KEY';
    SET prog_table = 'genre_channel_afnty';
elseif (cat_name = 'CHANNEL_GROUP_DISPLAY_NAME') then
	SET level_name = 'GENRE_DISPLAY_NAME';
	SET level_key = 'GENRE_KEY';
    SET cat_key = 'CHANNEL_GROUP_KEY';
    SET prog_table = 'genre_channel_afnty';
else 
	SET level_name = 'CHANNEL_GROUP_DISPLAY_NAME';
    SET m_table_name = 'FACT_TG_AFFINITY_AGG_WK';
	SET level_key = 'PROGRAM_GROUP_KEY';
    SET cat_key = 'CHANNEL_GROUP_KEY';
    SET prog_table = 'show_prog';
end if;
SET @tam_select = concat("TG_KEY IN ('",tam_tg,"') and MARKET_KEY IN ('",tam_mkt,"')");
SET @barc_select = concat("TG_KEY IN ('",barc_tg,"') and MARKET_KEY IN ('",barc_mkt,"')");
/* table for affinity calculation 
CREATE TEMPORARY TABLE temp_agg_affinity(
	category varchar(100) DEFAULT NULL
	, level varchar(100) DEFAULT NULL
	, prog_metric decimal(22,7) DEFAULT NULL
	, metric_share decimal(22,7) DEFAULT NULL
	, client_metric  decimal(22,7) DEFAULT NULL
	, client_share decimal(22,7) DEFAULT NULL
	,  ntwk varchar(100) DEFAULT NULL
	, Affinity varchar(1000) DEFAULT NULL
    ); 
*/
/* IN takes long time use union instead */

/* qry for calculating total adgrp */
SET @prog_all = concat("(select category, level,  cat_key, level_key, 
genre, ntwk, sum(prog_metric)prog_metric from(
select ",cat_key," cat_key,",level_key," level_key,", cat_name, " category, ", level_name," level, 
GENRE_DISPLAY_NAME genre, sum(", col_metric, ")prog_metric,
NETWORK_DISPLAY_NAME ntwk
from ",prog_table," where 
	",@tam_select," and
	WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky,"
    group by cat_key, level_key, genre, ntwk
    
    UNION
    
select ",cat_key," cat_key,",level_key," level_key,", cat_name, " category, ", level_name," level, 
GENRE_DISPLAY_NAME genre, sum(", col_metric, ")prog_metric,
NETWORK_DISPLAY_NAME ntwk
from ",prog_table," where 
    ",@barc_select," and
	WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky,"
    group by cat_key, level_key, genre, ntwk 
    )prog_grp group by cat_key, level_key
)prog_all");

/* query for calculating program metric genre share*/ 
SET @prog_share = concat("(select genre, sum(metric_share)metric_share from (
select GENRE_DISPLAY_NAME genre, sum(",col_metric,")metric_share 
from genre_channel_afnty where 
    ",@tam_select," and
    WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky,"
    group by genre
    
    UNION
    
select GENRE_DISPLAY_NAME genre, sum(",col_metric,")metric_share 
from genre_channel_afnty where 
    ",@barc_select," and
    WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky,"
    group by genre
    )prog_shr_grp group by genre
)prog_share");

/* qry for calculating client metric */
set @client_metric =concat("(select category, level, cat_key, level_key, 
sum(client_metric)client_metric from(
select ",cat_key," cat_key,",level_key," level_key,",cat_name," category, ", level_name," level, sum(",col_metric,")client_metric from ", m_table_name, " where 
",@tam_select," and WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky," and
    ADVERTISERS_GROUP_KEY='", client_sel, "'
    group by cat_key, level_key
    
    UNION

select ",cat_key," cat_key,",level_key," level_key,",cat_name," category, ", level_name," level, sum(",col_metric,")client_metric from ", m_table_name, " where 
",@barc_select," and WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky," and
    ADVERTISERS_GROUP_KEY='", client_sel, "'
    group by cat_key, level_key
	)client_grp group by cat_key, level_key
)client_metric");

/* qry for calculating client genre share */
SET @client_share = concat("(select genre, sum(client_share)client_share from (
select GENRE_DISPLAY_NAME genre, sum(",col_metric,")client_share from prog_affinity_agg_yr where ",@tam_select," and 
    WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky," and
    ADVERTISERS_GROUP_KEY='", client_sel, "'
    group by genre
    
    UNION
    
select GENRE_DISPLAY_NAME genre, sum(",col_metric,")client_share from prog_affinity_agg_yr where ",@barc_select," and 
    WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky," and
    ADVERTISERS_GROUP_KEY='", client_sel, "'
    group by genre
    )clnt_shr_grp group by genre
)client_share_gen");

SET @qry = concat("select prog_all.category, prog_all.level, prog_all.cat_key, prog_all.level_key,
prog_all.prog_metric, metric_share, client_metric, client_share, prog_all.genre, ntwk from ", @prog_all," JOIN ", @prog_share, " ON prog_all.genre = prog_share.genre "
" LEFT JOIN ", @client_metric, " ON prog_all.cat_key = client_metric.cat_key and 
prog_all.level_key = client_metric.level_key 
LEFT JOIN ", @client_share, " ON prog_all.genre = client_share_gen.genre");

/*SET @prog_clnt = concat("INSERT INTO temp_agg_affinity(category, level, prog_metric, 
				metric_share, client_metric, client_share, ntwk)",@qry); */
-- prepared statement
#select  @qry;
PREPARE qry_stmt FROM @qry;
EXECUTE qry_stmt;

# select * from temp_agg_affinity;

# drop table if exists temp_agg_affinity;
END//
DELIMITER ;
