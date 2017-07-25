from sqlalchemy import create_engine
import pandas as pd
import time
import json
from gramex import DB
import stats
import numpy
from templates.common.common import *

import re

last = {'time': time.time()}

cat_level = {'GENRE_DISPLAY_NAME': ['Genre', 'Network'],
             'CHANNEL_GROUP_DISPLAY_NAME': ['Channel', 'Genre'],
             'PROGRAM_GROUP_DISPLAY_NAME': ['Show', 'Channel']}

met_dict = {'ADGRP': 'AD GRP', 'FCT': 'FCT', 'TVT': 'TVT'}

re_slug = re.compile(r'[^A-Za-z0-9_]+')


def slug(s):
    return re_slug.sub('', str(s))


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
    return ww_load_gnr_afnty()


def load_chnl_afnty():
    return ww_load_chnl_afnty()


def get_gnr_afnty(metric, s_wk_ky, e_wk_ky):
    gnr_afnty_data = load_gnr_afnty()
    gnr_afnty_data = gnr_afnty_data[(gnr_afnty_data['WEEK_KEY'] >= s_wk_ky) &
                                    (gnr_afnty_data['WEEK_KEY'] <= e_wk_ky)]
    gnr_afnty_data['affinity_denom'] = gnr_afnty_data[metric]
    gnr_afnty_data = gnr_afnty_data[['category', 'level', 'affinity_denom']]
    # gnr_afnty_data.to_csv('gnr_afnty_new.csv')
    return gnr_afnty_data


def get_chnl_afnty(metric, s_wk_ky, e_wk_ky):
    chnl_afnty_data = load_chnl_afnty()
    chnl_afnty_data = chnl_afnty_data[(chnl_afnty_data['WEEK_KEY'] >= s_wk_ky) &
                                      (chnl_afnty_data['WEEK_KEY'] <= e_wk_ky)]
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


def get_afnty_data(cat_disply, metric, s_wk_ky, e_wk_ky, engine):

    if cat_disply == 'GENRE_DISPLAY_NAME':
        afnty = get_gnr_afnty(metric, s_wk_ky, e_wk_ky)

    if cat_disply == 'CHANNEL_GROUP_DISPLAY_NAME':
        afnty = get_chnl_afnty(metric, s_wk_ky, e_wk_ky)

    if cat_disply == 'PROGRAM_GROUP_DISPLAY_NAME':
        afnty = get_show_fnty(metric, s_wk_ky, e_wk_ky, engine)

    # engine.dispose()
    return afnty


def get_sql_data(
        client, metric, tam_tg_key, tam_mkt_key,
        barc_tg_key, barc_mkt_key, cat_disply, s_wk_ky, e_wk_ky):

    qry = 'CALL tg_affinity_wkl({:.0f}, "{:s}", {:.0f}, {:.0f}, {:.0f}, {:.0f}, "{:s}", {:.0f}, {:.0f})'
    qry = qry.format(
        client, metric, tam_tg_key, tam_mkt_key, barc_tg_key, barc_mkt_key, cat_disply, s_wk_ky, e_wk_ky)
    timer("t1")
    engine = get_engine()
    timer("******create_engine******")
    data = pd.read_sql(qry, engine)
    print qry
    timer("*****Test PRO_CLINT *****")
    # cat_lev_lis = afnty_data_lst[['category', 'level', 'ntwk']].values
    # cat_lev_key_val = afnty_data_lst[['cat_key', 'level_key', 'ntwk']].values
    afnty = get_afnty_data(
        cat_disply, metric,  s_wk_ky, e_wk_ky, engine)
    timer("****Test afnty **")
    if data['client_metric'].fillna(0).sum() == 0:
        data = pd.DataFrame(columns=data.columns)
    else:
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
        chnl_ins = pd.DataFrame()

        if cat_disply == 'GENRE_DISPLAY_NAME':
            chnl_ins = get_channel_insights(client, metric, tam_tg_key,
                                            tam_mkt_key, barc_tg_key, barc_mkt_key, s_wk_ky, e_wk_ky)

        insight_res = get_insights(
            data, s_wk_ky, e_wk_ky, metric, cat_disply, chnl_ins)

    timer("insights")
    return data, insight_res


def get_clients():
    return ww_get_clients()


def get_date_list():
    if 'date_what_works' not in DB:
        qry = "select max(week_key)max from genre_channel_afnty"
        engine = get_engine()
        data = pd.read_sql(qry, engine)
        dt_max = str(data.ix[0].values[0])
        DB['date_what_works'] = dt_max
        engine.dispose()
    return DB['date_what_works']


def get_channel_insights(client, metric, tam_tg_key,
                         tam_mkt_key, barc_tg_key, barc_mkt_key, s_wk_ky, e_wk_ky):
    engine = get_engine()
    qry = """call get_chnl_insights({:.0f}, '{:s}', {:.0f},  {:.0f},  {:.0f}, {:.0f}, {:.0f}, {:.0f})"""
    qry = qry.format(client, metric, tam_tg_key,
                     tam_mkt_key, barc_tg_key, barc_mkt_key, s_wk_ky, e_wk_ky)
    print qry
    data = pd.read_sql(qry, engine)
    data = data.groupby(['category', 'level', 'ntwk']).agg({'client_metric': 'sum',
                                                            'prog_metric': 'sum'})
    data = data.reset_index(level=[2])
    tot_clnt_val = data['client_metric'].sum()
    data.loc[:, 'Overall Share'] = data.loc[:, 'client_metric'].apply(
        lambda v: (1. * v / tot_clnt_val * 100) if tot_clnt_val > 0 else 'NA')
    chnl_afnty = get_chnl_afnty(metric, s_wk_ky, e_wk_ky)
    chnl_afnty = chnl_afnty.groupby(
        ['category', 'level']).agg({'affinity_denom': 'sum'})
    data = data.join(chnl_afnty, how='left')
    data['Affinity'] = data['prog_metric'] / data['affinity_denom'] * 100
    data = data.reset_index()
    engine.dispose()
    return data


def get_insights(data, s_wk_ky, e_wk_ky, metric, cat_display, chnl_ins):
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
    star_data_clnt = star_data[~(star_data['client_metric'].isnull())]
    data_n_shws = len(star_data_clnt[star_data_clnt['Affinity'] >= 100])
    cat_disp = cat_list
    if cat_list == "Genre":
        data_n_shws = len(chnl_ins[(chnl_ins['Affinity'] >= 100)
                                   & (chnl_ins['ntwk'] == 'Star Network')])
        cat_disp = 'Channel'
    stmt4 = stmt4.format(cat_disp, data_n_shws)
    insight_res.append([stmt4])

    stmt5 = """Top 3 (by Client {:s}) client spend on
            {:s} on Competition with Affinity < 100""".format(met_dict[metric], cat_disp)
    if cat_disp == 'Channel' and cat_list == "Genre":
        data_non_star = chnl_ins[~(chnl_ins['ntwk'] == 'Star Network')]
    data_nstar_afnt_res = data_non_star[data_non_star['Affinity'] < 100]
    top_3_non_star = data_nstar_afnt_res.sort(
        'client_metric', ascending=False).head(3)
    top_3_non_star = top_3_non_star.set_index(
        ['category', 'level'])[['Overall Share', 'Affinity']]
    if len(top_3_non_star) > 0:
        insight_res.append([stmt5, top_3_non_star])
    engine.dispose()
    return insight_res


def get_ntwk_cols():
    ntwk_colrs = pd.read_csv('NetworkColors.csv')
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
    ntwks = data_not_oth[~(
        data_not_oth[clnt_mtrc].isnull())][['ntwk', clnt_mtrc]].groupby(
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
    if is_per and not numpy.isnan(col) and not numpy.isinf(col):
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
        val = "{:,.0f}".format(val)
        if numpy.isnan(col):
            return [0, 'NA']
        return [val, fmt]
    else:
        return [val, str(col)]


def get_ref_mapping(data, col_name, col_source, col_tg_mkt):
    res_dict = {}
    tam_barc_dict = {'CUST_SALES': 'tam', 'CUST_SALES/BARC': 'barc'}
    for i, row in data.iterrows():
        name, source, tg_mrkt = row[col_name], row[col_source], row[col_tg_mkt]
        temp = {'tam': '', 'barc': ''}
        src = tam_barc_dict[source]
        if name not in res_dict:
            temp[src] = tg_mrkt
            res_dict[name] = temp
        else:
            res_dict[name][src] = tg_mrkt
    return res_dict


def get_ref_gnrtgmkt():
    if 'ww_ref_gnr' not in DB:
        qry = "select * from ref_genre_tg_mkt"
        engine = get_engine()
        data = pd.read_sql(qry, engine)
        DB['ww_ref_gnr'] = get_ref_mapping(
            data, 'GENRE_DISPLAY_NAME',
            'SOURCE', 'TG_MARKET_DISPLAY_NAME')
        engine.dispose()
    return DB['ww_ref_gnr']


def get_ref_chnltgmkt():
    if 'ww_ref_chnl' not in DB:
        qry = "select * from ref_ch_group_tg_mkt"
        engine = get_engine()
        data = pd.read_sql(qry, engine)
        DB['ww_ref_chnl'] = get_ref_mapping(
            data, 'CHANNEL_GROUP_DISPLAY_NAME',
            'SOURCE', 'TG_MARKET_DISPLAY_NAME')
        engine.dispose()
    return DB['ww_ref_chnl']


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
    get_ref_gnrtgmkt()
    timer('load_ref_gnr')
    get_ref_chnltgmkt()
    timer('load_ref_chnl')
