DROP PROCEDURE IF EXISTS get_chnl_insights;
DELIMITER //
CREATE PROCEDURE get_chnl_insights(client_sel numeric, col_metric CHAR(40), tam_tg numeric,  tam_mkt numeric,  barc_tg numeric, barc_mkt numeric, s_wek_ky numeric, e_wek_ky numeric)
BEGIN
-- set user variable
DECLARE level_name CHAR(40);
DECLARE m_table_name CHAR(60);
DECLARE level_key CHAR(40);
DECLARE cat_key CHAR(40);
DECLARE cat_name CHAR(40);
DECLARE prog_table CHAR(60);

SET m_table_name = 'prog_affinity_agg_yr';
SET level_key = 'CHANNEL_GROUP_KEY';
SET cat_key = ' GENRE_KEY';
SET cat_name = 'CHANNEL_GROUP_DISPLAY_NAME';
SET level_name = 'GENRE_DISPLAY_NAME';
SET prog_table = 'genre_channel_afnty';

SET @tam_select = concat("TG_KEY IN ('",tam_tg,"') and MARKET_KEY IN ('",tam_mkt,"')");
SET @barc_select = concat("TG_KEY IN ('",barc_tg,"') and MARKET_KEY IN ('",barc_mkt,"')");

SET @clnt_prog_tam = concat("(select clnt.*, prog.prog_metric from (select NETWORK_DISPLAY_NAME ntwk, ",cat_key," cat_key,",level_key," level_key,
	",cat_name," category, ", level_name," level, sum(",col_metric,")client_metric from ", m_table_name, " where 
	",@tam_select," and WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky," and
	ADVERTISERS_GROUP_KEY='", client_sel, "'
	group by cat_key, level_key)clnt
    JOIN
    (select NETWORK_DISPLAY_NAME ntwk, ",cat_key," cat_key,",level_key," level_key,
	",cat_name," category, ", level_name," level, sum(",col_metric,")prog_metric from ", prog_table, " where 
	",@tam_select," and WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky,"
	group by cat_key, level_key)prog ON clnt.cat_key=prog.cat_key and clnt.level_key=prog.level_key)");

SET @clnt_prog_barc = concat("(select clnt.*, prog.prog_metric from (select NETWORK_DISPLAY_NAME ntwk, ",cat_key," cat_key,",level_key," level_key,
	",cat_name," category, ", level_name," level, sum(",col_metric,")client_metric from ", m_table_name, " where 
	",@barc_select," and WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky," and
	ADVERTISERS_GROUP_KEY='", client_sel, "'
	group by cat_key, level_key)clnt
    JOIN
    (select NETWORK_DISPLAY_NAME ntwk, ",cat_key," cat_key,",level_key," level_key,
	",cat_name," category, ", level_name," level, sum(",col_metric,")prog_metric from ", prog_table, " where 
	",@barc_select," and WEEK_KEY>=",s_wek_ky," and WEEK_KEY <=",e_wek_ky,"
	group by cat_key, level_key)prog ON clnt.cat_key=prog.cat_key and clnt.level_key=prog.level_key)");
/* qry for calculating client metric */
set @client_metric =concat("select category, level, cat_key, level_key, ntwk,
sum(client_metric)client_metric, sum(prog_metric)prog_metric from(",@clnt_prog_tam,
" UNION ",
@clnt_prog_barc,")client_grp group by cat_key, level_key");

/* qry for calculating client genre share */

#select  @client_metric;
PREPARE qry_stmt FROM @client_metric;
EXECUTE qry_stmt;

# select * from temp_agg_affinity;

# drop table if exists temp_agg_affinity;
END//
DELIMITER ;
