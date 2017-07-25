from sqlalchemy import create_engine
import pandas as pd
import time
import json
from gramex import DB
import stats
import numpy
from templates.common.common import st_unt, get_engine
from pandas.compat import u

import re

last = {'time': time.time()}

cat_level = {'GENRE_DISPLAY_NAME': ['Genre', 'Network'],
             'CHANNEL_GROUP_DISPLAY_NAME': ['Channel', 'Genre'],
             'PROGRAM_GROUP_DISPLAY_NAME': ['Show', 'Channel']}

met_dict = {'ADGRP': 'AD GRP', 'FCT': 'FCT', 'TVT': 'TVT'}

re_slug = re.compile(r'[^A-Za-z0-9_]+')


def slug(s):
    return re_slug.sub('', str(s))


def decode_special(val):
    try:
        val = val.decode('unicode_escape').encode('ascii', 'ignore')
    except:
        print val, 'spcialllllll'
        val = ''
    return val


def timer(msg):
    #global last_time
    new_time = time.time()
    print '{:,.3f}: {:s}'.format(new_time - last['time'], str(msg))
    last['time'] = new_time

# use get_conection from coomon
# def get_engine():
#     engine = get_engine()
#     return engine


def show_table_map(ntwk):
    m_table_name = 'FACT_TG_AFFINITY_AGG_WK'
    return m_table_name

def load_gnr_afnty():
    if 'what_wrks_gnr_afnty' not in DB:
        data = pd.DataFrame()
        try:
            engine = get_engine()
            qry = """select gnr.GENRE_KEY, gnr.GENRE_DISPLAY_NAME category, 
            gnr.NETWORK_KEY, NETWORK_DISPLAY_NAME level, 
            gnr.WEEK_KEY, SUM(ADGRP)ADGRP, SUM(FCT)FCT, SUM(TVT)TVT from
            genre_channel_afnty gnr 
            JOIN 
            ref_genre_tg_mkt ref
            where ref.GENRE_KEY=gnr.GENRE_KEY 
            and ref.TG_KEY=gnr.TG_KEY 
            and ref.MARKET_KEY=gnr.MARKET_KEY group by GENRE_KEY, NETWORK_KEY, WEEK_KEY"""
            data = pd.read_sql(qry, engine)
        except:
            print "error at load_gnr_afnty"
        DB['what_wrks_gnr_afnty'] = data
        engine = engine.dispose()
    return DB['what_wrks_gnr_afnty']


def load_chnl_afnty():
    if 'what_wrks_chnl_afnty' not in DB:
        data = pd.DataFrame()
        try:
            engine = get_engine()
            qry = """ select * from
            (select CHANNEL_GROUP_KEY, CHANNEL_GROUP_DISPLAY_NAME category, 
            TG_KEY, MARKET_KEY, GENRE_KEY, GENRE_DISPLAY_NAME level, WEEK_KEY, ADGRP, FCT, TVT from 
            genre_channel_afnty)chnl
            JOIN
            ref_ch_group_tg_mkt ref
            where ref.CHANNEL_GROUP_KEY=chnl.CHANNEL_GROUP_KEY 
            and ref.TG_KEY=chnl.TG_KEY 
            and ref.MARKET_KEY=chnl.MARKET_KEY"""
            data = pd.read_sql(qry, engine)
        except:
            print "error at load_chnl_afnty"
        DB['what_wrks_chnl_afnty'] = data
        engine = engine.dispose()
    return DB['what_wrks_chnl_afnty']

def get_gnr_afnty(metric, s_wk_ky, e_wk_ky):
    gnr_afnty_data = load_gnr_afnty()
    gnr_afnty_data = gnr_afnty_data[(gnr_afnty_data['WEEK_KEY']>=s_wk_ky) & 
                    (gnr_afnty_data['WEEK_KEY']<=e_wk_ky)]
    gnr_afnty_data['affinity_denom'] = gnr_afnty_data[metric]
    gnr_afnty_data = gnr_afnty_data[['category', 'level', 'affinity_denom']]           
    # gnr_afnty_data.to_csv('gnr_afnty_new.csv')
    return gnr_afnty_data

def get_chnl_afnty(metric, s_wk_ky, e_wk_ky):
    chnl_afnty_data = load_chnl_afnty()
    chnl_afnty_data = chnl_afnty_data[(chnl_afnty_data['WEEK_KEY']>=s_wk_ky) & 
                    (chnl_afnty_data['WEEK_KEY']<=e_wk_ky)]
    chnl_afnty_data['affinity_denom'] = chnl_afnty_data[metric] 
    chnl_afnty_data = chnl_afnty_data[['category', 'level', 'affinity_denom']]
    # chnl_afnty_data.to_csv('chnl_afnty_new.csv')
    return chnl_afnty_data

def get_show_fnty(metric, s_wk_ky, e_wk_ky, engine):
    qry = """select PROGRAM_GROUP_KEY, PROGRAM_GROUP_DISPLAY_NAME category, 
                CHANNEL_GROUP_KEY, CHANNEL_GROUP_DISPLAY_NAME level, 
                sum({:s})affinity_denom FROM show_affinity 
                where week_key>={:.0f} and week_key<={:.0f}
                group by PROGRAM_GROUP_KEY, CHANNEL_GROUP_KEY"""
    qry = qry.format(metric, s_wk_ky, e_wk_ky)
    # print qry
    shw_afnty_data = pd.read_sql(qry, engine)
    return shw_afnty_data


def get_afnty_data(cat_disply, cat_lev_lis, cat_lev_key_val, metric, s_wk_ky, e_wk_ky, engine):
    catgry_lis, level_name, level_value = [], [], []
    '''
    afnty_tab_map = {'GENRE_DISPLAY_NAME': ['NETWORK_DISPLAY_NAME', 'GENRE_NAME', 'REF_GENRE_TG_MKT'],
                     'CHANNEL_GROUP_DISPLAY_NAME': ['GENRE_DISPLAY_NAME', 'CHANNEL_GROUP_DISPLAY_NAME', 'REF_CH_GROUP_TG_MKT'],
                     'PROGRAM_GROUP_DISPLAY_NAME': ['CHANNEL_GROUP_DISPLAY_NAME', 'CHANNEL_GROUP_DISPLAY_NAME', 'REF_CH_GROUP_TG_MKT']}
    cat_level_dict = {'PROGRAM_GROUP_DISPLAY_NAME': ['CHANNEL_GROUP_KEY', 'PROGRAM_GROUP_KEY'],
                      'CHANNEL_GROUP_DISPLAY_NAME': ['CHANNEL_GROUP_KEY', 'GENRE_KEY'],
                      'GENRE_DISPLAY_NAME': ['GENRE_KEY', 'NETWORK_KEY']}
    key_name = cat_level_dict[cat_disply]
    afnty_table = afnty_tab_map[cat_disply][2]
    afnty_levl = afnty_tab_map[cat_disply][0]
    afnty_col_map = afnty_tab_map[cat_disply][1]
    afnty_qry = "select TG_MARKET_DISPLAY_NAME, TG_KEY, MARKET_KEY, SOURCE, {:s} category from {:s}".format(
        afnty_col_map, afnty_table)
    afnty_data = pd.read_sql(afnty_qry, engine)
    afnty_data['category'] = afnty_data[
        'category'].dropna().apply(lambda v: v.upper())
    afnty_data = afnty_data[~(afnty_data['category'].isnull())]
    afnty_data['category'] = map(u, afnty_data['category'])
    afnty_data = afnty_data.drop_duplicates()
    tam_afnty = afnty_data[afnty_data['SOURCE'] == 'CUST_SALES']
    barc_afnty = afnty_data[afnty_data['SOURCE'] == 'CUST_SALES/BARC']
    tam_aff_dict = json.loads(
        tam_afnty.set_index('category').to_json(orient='index'))
    barc_aff_dict = json.loads(
        barc_afnty.set_index('category').to_json(orient='index'))

    m_table_name = 'genre_channel_afnty'
    '''
    if cat_disply == 'GENRE_DISPLAY_NAME':
        afnty = get_gnr_afnty(metric, s_wk_ky, e_wk_ky)

    if cat_disply == 'CHANNEL_GROUP_DISPLAY_NAME':
        afnty = get_chnl_afnty(metric, s_wk_ky, e_wk_ky)

    if cat_disply == 'PROGRAM_GROUP_DISPLAY_NAME':
        afnty = get_show_fnty(metric, s_wk_ky, e_wk_ky, engine)
    '''
    for val, keys in zip(cat_lev_lis, cat_lev_key_val):
        # print keys
        cat_name, lev_name, cat_key, lev_key = key_name[
            0], key_name[1], keys[0], keys[1]
        if cat_disply == 'PROGRAM_GROUP_DISPLAY_NAME':
            ntwk = keys[2]
            cat_name, lev_name, cat_key, lev_key = key_name[
                1], key_name[0], keys[1], keys[0]
            m_table_name = show_table_map(ntwk)

        key = val[1] if cat_disply == 'PROGRAM_GROUP_DISPLAY_NAME' else val[0]
        key = key.upper()
        tam_tg_key, tam_mkt_key, barc_tg_key, barc_mkt_key = '0', '0', '0', '0'
        if key in tam_aff_dict:
            dict_res = tam_aff_dict[key]
            tam_tg_key = str(dict_res['TG_KEY'])
            tam_mkt_key = str(dict_res['MARKET_KEY'])
        if key in barc_aff_dict:
            dict_res = barc_aff_dict[key]
            barc_tg_key = str(dict_res['TG_KEY'])
            barc_mkt_key = str(dict_res['MARKET_KEY'])

        afnty_qry1 = """select sum({:s}) metric from {:s} where (TG_KEY, MARKET_KEY) IN (
                        ({:s}, {:s}), ({:s}, {:s})) and ({:s}, {:s})=({:.0f}, {:.0f}) and WEEK_KEY>={:.0f}
                         and WEEK_KEY<={:.0f}
                         """
        afnty_qry1 = afnty_qry1.format(metric, m_table_name, tam_tg_key,
                                       tam_mkt_key, barc_tg_key, barc_mkt_key, cat_name,
                                       lev_name, cat_key, lev_key, s_wk_ky, e_wk_ky)

        afnty_data1 = pd.read_sql(afnty_qry1, engine)
        catgry_lis.append(val[0])
        level_name.append(val[1])
        val_afnty = afnty_data1.ix[0].values[0]
        level_value.append(val_afnty)
    res_dict = {'category': catgry_lis,
                'level': level_name, 'affinity_denom': level_value}
    afnty = pd.DataFrame(res_dict)
    '''
    # engine.dispose()
    return afnty


def get_sql_data(client, metric, tam_tg_key, tam_mkt_key, barc_tg_key, barc_mkt_key, cat_disply, s_wk_ky, e_wk_ky):

    qry = 'CALL tg_affinity_wkl({:.0f}, "{:s}", {:.0f}, {:.0f}, {:.0f}, {:.0f}, "{:s}", {:.0f}, {:.0f})'
    qry = qry.format(
        client, metric, tam_tg_key, tam_mkt_key, barc_tg_key, barc_mkt_key, cat_disply, s_wk_ky, e_wk_ky)
    timer("t1")
    engine = get_engine()
    timer("******create_engine******")
    data = pd.read_sql(qry, engine)
    print qry
    timer("*****Test PRO_CLINT *****")
    data['category'] = data['category'].dropna()
    afnty_data_lst = data[
        ~(data['client_metric'].isnull())]
    if cat_disply == 'PROGRAM_GROUP_DISPLAY_NAME':
        afnty_data_lst = afnty_data_lst.sort(
            'prog_metric', ascending=False).head(100)
    cat_lev_lis = afnty_data_lst[['category', 'level', 'ntwk']].values
    cat_lev_key_val = afnty_data_lst[['cat_key', 'level_key', 'ntwk']].values
    afnty = get_afnty_data(
        cat_disply, cat_lev_lis, cat_lev_key_val, metric,  s_wk_ky, e_wk_ky, engine)
    timer("****Test afnty **")
    if data['client_metric'].sum() == 0:
        data = pd.DataFrame(columns=data.columns)
    if not data.empty:
        data = data.groupby(['category', 'level', 'genre', 'ntwk']).agg({'prog_metric': 'sum',
                                                                         'metric_share': 'mean',
                                                                         'client_metric': 'sum',
                                                                         'client_share': 'mean'
                                                                         })
        data = data.reset_index(level=[2, 3])
        afnty = afnty.groupby(['category', 'level'])['affinity_denom'].sum()
        data = data.join(afnty, how='left')
        data = data.reset_index()
        data['Genre Share'] = data['prog_metric'] / data['metric_share'] * 100
        data['Client Genre Share'] = data[
            'client_metric'] / data['client_share'] * 100
        data.to_csv('afnty_old.csv')
        data['Affinity'] = data['prog_metric'] / data['affinity_denom'] * 100
        tot_clnt_val = data['client_metric'].sum()
        data.loc[:, 'Overall Share'] = data.loc[:, 'client_metric'].apply(
            lambda v: (1. * v / tot_clnt_val * 100) if tot_clnt_val > 0 else 'NA')
        # data.to_csv('gnr_ntwk.csv', index=False)
        data = data[['category', 'level', 'prog_metric', 'Genre Share',
                     'Affinity', 'client_metric', 'Client Genre Share',
                     'Overall Share', 'genre', 'ntwk']]
        data['category'] = data['category'].apply(lambda v: decode_special(v))
        data['level'] = data['level'].apply(lambda v: decode_special(v))
    #data.to_csv('download.csv', index=False)
    # insights =
    engine.dispose()
    insight_res = []
    # handle special chars need to recheck on this

    if not data.empty:
        insight_res = get_insights(
            data, s_wk_ky, e_wk_ky, metric, cat_disply)

    timer("insights")
    return data, insight_res


def get_clients():
    if 'clients_what_works' not in DB:
        qry = """select ADVERTISERS_GROUP_DISPLAY_NAME client, ADVERTISERS_GROUP_KEY 
                from prog_affinity_agg_yr group by ADVERTISERS_GROUP_KEY"""
        engine = get_engine()
        data = pd.read_sql(qry, engine)
        DB['clients_what_works'] = pd.Series(data.ADVERTISERS_GROUP_KEY.values,
                                             index=data.client.values).to_dict()
        engine.dispose()
    return DB['clients_what_works']


def get_date_list():
    if 'date_what_works' not in DB:
        qry = "select max(week_key)max from genre_channel_afnty"
        engine = get_engine()
        data = pd.read_sql(qry, engine)
        dt_max = str(data.ix[0].values[0])
        DB['date_what_works'] = dt_max
        engine.dispose()
    return DB['date_what_works']


def get_insights(data, s_wk_ky, e_wk_ky, metric, cat_display):
    engine = get_engine()
    insight_res = []
    cat_list = cat_level[cat_display][0]
    # 1. Star Network garners x% of Total GRPs while client spends y% on STAR
    stmt = """Star Network market share is {:.2f}% of Total {:s}s 
    while client spends {:.2f}% on STAR"""
    star_data = data[data['ntwk'] == 'Star Network']
    star_spend = star_data['prog_metric'].sum()
    total_spend = data['prog_metric'].sum()
    star_val = star_spend / total_spend * 100
    data = data[~(data['client_metric'].isnull())]
    client_tot_spend = data['client_metric'].sum()
    client_star_spend = data[data['ntwk'] == 'Star Network'][
        'client_metric'].sum()
    try:
        clnt_val = client_star_spend / float(client_tot_spend) * 100
    except ZeroDivisionError:
        clnt_val = 0

    stmt = stmt.format(star_val, met_dict[metric], clnt_val)
    insight_res.append([stmt])

    stmt2 = """High Spend by client on low ROI competitive {:s}: Spend > [5] %, 
    and TG-Affinity < [50].""".format(cat_list)
    data_non_star = data[~(data['ntwk'] == 'Star Network')]

    '''
    data_non_starSum = data_non_star['client_metric'].sum()
    data_non_star.loc[:, 'spend'] = data_non_star.loc[:, 'client_metric'].apply(
        lambda v: float(v) / data_non_starSum * 100)
    '''
    data_non_star_res = data_non_star[
        (data_non_star['Overall Share'] > 5) & (data_non_star['Affinity'] < 50)]
    data_non_star_res = data_non_star_res.sort(
        'Overall Share', ascending=False).head(3)
    data_non_star_res = data_non_star_res.set_index(
        ['category', 'level'])[['Overall Share', 'Affinity']]
    if len(data_non_star_res) > 0:
        insight_res.append([stmt2, data_non_star_res])

    stmt3 = """Low Spend by client on high ROI Star {:s}: Spend < [5] %, 
            and TG-Affinity > [80].""".format(cat_list)
    data_star = data[(data['ntwk'] == 'Star Network')]
    '''
    data_starSum = data_star['client_metric'].sum()
    data_star.loc[:, 'spend'] = data_star.loc[:, 'client_metric'].apply(
        lambda v: float(v) / data_starSum * 100)
    '''
    data_star = data_star[
        (data_star['Overall Share'] < 5) & (data_star['Affinity'] > 80)]
    data_star = data_star.sort('Overall Share').head(3)
    data_star = data_star.set_index(
        ['category', 'level'])[['Overall Share', 'Affinity']]
    if len(data_star) > 0:
        insight_res.append([stmt3, data_star])

    stmt4 = """No of {:s} on STAR with TG-Affinity >= 100 : {:.0f}"""
    data_n_shws = len(star_data[star_data['Affinity'] >= 100])
    stmt4 = stmt4.format(cat_list, data_n_shws)
    if (cat_list != "Genre"):
        insight_res.append([stmt4])

    stmt5 = """Top 3 (by Client {:s}) client spend on
            {:s} on Competition with Affinity < 100""".format(met_dict[metric], cat_list)
    data_nstar_afnt_res = data_non_star[data_non_star['Affinity'] < 100]
    top_3_non_star = data_nstar_afnt_res.sort(
        'client_metric', ascending=False).head(3)
    top_3_non_star = top_3_non_star.set_index(
        ['category', 'level'])[['Overall Share', 'Affinity']]
    if len(top_3_non_star) > 0 and (cat_list != "Genre"):
        insight_res.append([stmt5, top_3_non_star])
    engine.dispose()
    return insight_res


def get_ntwk_cols():
    ntwk_colrs = DB.csv('NetworkColors.csv')
    if 'what_works_ntwk_colrs' not in DB:
        ntwk_colrs.loc[:, 'Network'] = ntwk_colrs.loc[:, 'Network'].apply(
            lambda v: v.lower())
        ntwk_colrs_dict = pd.Series(ntwk_colrs.HexCode.values,
                                    index=ntwk_colrs.Network).to_dict()
        DB['what_works_ntwk_colrs'] = ntwk_colrs_dict
    return DB['what_works_ntwk_colrs']


def get_col_rename(data, cat_display, metric):
    data['ntwk'] = data['ntwk'].str.lower()
    cat_list = cat_level[cat_display]
    clnt_mtrc = 'Client' + ' ' + met_dict[metric]
    prog_metric = 'Total' + ' ' + met_dict[metric]
    col_rename = {'category': cat_list[0], 'level': cat_list[1],
                  'prog_metric': prog_metric, 'client_metric': clnt_mtrc}
    data = data.rename(columns=col_rename)
    data = data.sort(clnt_mtrc, ascending=False)
    return data


def club_othrs(data, cat_display, metric):
    data_not_oth = data[~(data['ntwk'] == 'others')]
    cat_list = cat_level[cat_display]
    clnt_mtrc = 'Client' + ' ' + met_dict[metric]
    ntwks = data_not_oth[~(data_not_oth[clnt_mtrc].isnull())][['ntwk', clnt_mtrc]].groupby(
        'ntwk').sum().sort(clnt_mtrc, ascending=False).head(4).index
    data_dup = data
    data_dup['ntwk'] = data_dup['ntwk'].apply(
        lambda v: 'Others' if v not in ntwks else v)
    # if cat_list[1] == 'Network':
    #     data_dup[cat_list[1]] = data_dup[[cat_list[1], 'ntwk']].apply(
    # lambda v: 'Others' if v['ntwk']=='Others' else v[cat_list[1]], axis=1)
    data_club = data_dup.groupby(
        [cat_list[0], cat_list[1], 'genre', 'ntwk'], as_index=False).mean()
    return data_club, ntwks


def format_col(col, is_per, col_name):
    val = col
    if is_per and not numpy.isnan(col):
        col = int(round(col))
        val = "{:,.2f}".format(val)
        if col_name == 'Affinity':
            fmt = '{:,.0f}%'.format(col)
            return [val, fmt]
    t = type(col)
    if numpy.issubdtype(t, numpy.int):
        fmt = '{:,.0f}'.format(col)
        return [val, fmt]
    elif numpy.issubdtype(t, numpy.float):
        fmt = st_unt(col)
        val = "{:,.2f}".format(val)
        if numpy.isnan(col):
            return [0, 'NA']
        return [val, fmt]
    else:
        return [val, str(col)]

def db_load_first():
    timer('db load')
    get_clients()
    timer('get_clients')
    get_date_list()
    timer('get_date_list')
    get_ntwk_cols()
    timer('ntw_col')
    load_gnr_afnty()
    timer('load_gnr_afnty')
    load_chnl_afnty()
    timer('load_chnl_afnty')

