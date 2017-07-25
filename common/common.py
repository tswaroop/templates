from sqlalchemy import create_engine
import pandas as pd
import json
from gramex import DB
import stats
import re
import yaml
import hashlib
import collections
from tornado.web import HTTPError


def create_groups():
    auth_groups = collections.OrderedDict()
    auth_groups['Group 1'] = ['my_view', 'my_view_manager', 'client_on_star', 'client_on_tv', 'client_overview',
                              'what_works', 'whom_to_target', 'my_reports_genre_performance', 'my_reports_detailed_revenue',
                              'my_reports_market_share', 'my_reports_program_ratings']

    auth_groups['Group 2'] = ['client_on_star', 'client_on_tv', 'client_overview', 'what_works', 'whom_to_target',
                              'my_reports_genre_performance', 'my_reports_market_share', 'my_reports_detailed_revenue',
                              'my_reports_program_ratings']

    auth_groups['Group 3'] = ['client_on_star', 'client_on_tv', 'client_overview', 'what_works', 'whom_to_target',
                              'my_reports_genre_performance', 'my_reports_market_share',
                              'my_reports_program_ratings']  # no revenue to this group in BO reports

    auth_groups['Group 4'] = ['client_on_tv', 'client_overview', 'what_works', 'whom_to_target',
                              'my_reports_genre_performance', 'my_reports_market_share',
                              'my_reports_program_ratings']  # no revenue in BO reports
    return auth_groups


def get_engine():
    try:
        with open('config.yml', 'r') as config:
            creds = yaml.load(config)
    except:
        with open('../../config.yml', 'r') as config:
            creds = yaml.load(config)

    conn_string = 'mysql://{user}:{password}@{host}:{port}/{name}'.format(
        user=creds['database']['user'],
        password=creds['database']['password'],
        host=creds['database']['host'],
        port=creds['database']['port'],
        name=creds['database']['name']
    )
    engine = create_engine(conn_string)
    return engine


def get_tg_mkt():
    if 'tg_mrkt' not in DB:
        engine = get_engine()
        data_tg = pd.read_sql('select * from REF_TG_MKT', engine)
        data_tg = data_tg[data_tg['SOURCE'] == 'CUST_SALES']
        data_tg = data_tg.set_index('TG_MARKET_DISPLAY_NAME')
        tg_mkt_dict = json.loads(data_tg.to_json(orient='index'))
        DB['tg_mrkt'] = tg_mkt_dict
    return DB['tg_mrkt']


def get_barc_mkt():
    if 'barc_mrkt' not in DB:
        engine = get_engine()
        data_barc = pd.read_sql('select * from REF_TG_MKT', engine)
        data_barc = data_barc[data_barc['SOURCE'] == 'CUST_SALES/BARC']
        data_barc = data_barc.set_index('TG_MARKET_DISPLAY_NAME')
        b_mkt_dict = json.loads(data_barc.to_json(orient='index'))
        DB['barc_mrkt'] = b_mkt_dict
    return DB['barc_mrkt']


def get_barc_tg_mrkt():
    if 'barc_tg_mrkt' not in DB:
        data = pd.read_csv('../../data/REF_CH_GROUP_TG_MKT_MY.csv')
        data = data[data['TG_DISPLAY_NAME'].str.startswith('b_')]
        data = data[['TG_MARKET_DISPLAY_NAME', 'TG_KEY', 'MARKET_KEY']]
        barc_tg = data.drop_duplicates(['TG_MARKET_DISPLAY_NAME',
                                        'TG_KEY',
                                        'MARKET_KEY'])
        barc_tg = barc_tg.set_index('TG_MARKET_DISPLAY_NAME')
        barc_tg_dict = json.loads(barc_tg.to_json(orient='index'))
        DB['barc_tg_mrkt'] = barc_tg_dict
    return DB['barc_tg_mrkt']


LAKHS = [
    {'above': 1e12, 'divideby': 1e12, 'unit': 'lk cr'},
    {'above': 1e7, 'divideby': 1e7, 'unit': 'cr'},
    {'above': 1e5, 'divideby': 1e5, 'unit': 'lk'},
    {'above': 1e3, 'divideby': 1e3, 'unit': 'k'},
    {'above': 1e0, 'divideby': 1e0, 'unit': ''},
]
st_unt = stats.units(LAKHS, format='{:,.1f}{:s}')


def read_hierarchy():
    engine = get_engine()
    if 'REF_EMPLOYEE_HIERARCHY' not in DB:
        data = pd.read_sql('select * from REF_EMPLOYEE_HIERARCHY', engine)
    for col in data.columns:
        data[col] = data[col].astype(str)
    DB['REF_EMPLOYEE_HIERARCHY'] = data


def get_emp_role(handler):
    if 'REF_EMPLOYEE_HIERARCHY' not in DB:
        read_hierarchy()
    data = DB['REF_EMPLOYEE_HIERARCHY']
    pattern = re.compile("starin[^\w']")
    user_id = pattern.sub('', handler.get_current_user()).upper()
    roles = data[data['EMPLOYEE_NT_ID'] == user_id][
        'EMPLOYEE_ROLE'].values.tolist()
    # roles = ['SALES EXECUTIVE', 'GROUP HEAD'] #testing
    # roles = ['SALES EXECUTIVE'] #testing
    return roles


def argsValidation(arg_dict):
    for k, v in arg_dict.items():
        default = True
        if k == '':
            k = v[1]
        if isinstance(k, (tuple)):
            for ele in k:
                res = default and (ele in v[0])
                if not res:
                    return res
        else:
            res = default and (k in v[0])
            if not res:
                return res
    return default

# function used for what works


def decode_special(val):
    try:
        val = val.decode('unicode_escape').encode('ascii', 'ignore')
    except:
        # print val, 'spcialllllll'
        val = ''
    return val


def ww_get_clients():
    if 'clients_what_works' not in DB:
        qry = """select ADVERTISERS_GROUP_DISPLAY_NAME client, ADVERTISERS_GROUP_KEY
                from prog_affinity_agg_yr group by ADVERTISERS_GROUP_KEY"""
        engine = get_engine()
        data = pd.read_sql(qry, engine)
        data['client'] = data['client'].apply(lambda v: decode_special(v))
        DB['clients_what_works'] = pd.Series(
            data.ADVERTISERS_GROUP_KEY.values,
            index=data.client.values).to_dict()
        engine.dispose()
    return DB['clients_what_works']


def ww_load_gnr_afnty():
    if 'what_wrks_gnr_afnty' not in DB:
        data = pd.DataFrame()
        try:
            engine = get_engine()
            qry = """select * from ww_genre_affinity"""
            data = pd.read_sql(qry, engine)
            data = data.rename(columns={'GENRE_DISPLAY_NAME': 'category',
                                        'NETWORK_DISPLAY_NAME': 'level'})
        except:
            print "error at load_gnr_afnty"
        DB['what_wrks_gnr_afnty'] = data
        engine = engine.dispose()
    return DB['what_wrks_gnr_afnty']


def ww_load_chnl_afnty():
    if 'what_wrks_chnl_afnty' not in DB:
        data = pd.DataFrame()
        try:
            engine = get_engine()
            qry = """ select * from ww_channel_affinity"""
            data = pd.read_sql(qry, engine)
            data = data.rename(
                columns={
                    'CHANNEL_GROUP_DISPLAY_NAME': 'category',
                    'GENRE_DISPLAY_NAME': 'level'})
        except:
            print "error at load_chnl_afnty"
        DB['what_wrks_chnl_afnty'] = data
        engine = engine.dispose()
    return DB['what_wrks_chnl_afnty']


def cotv_get_clients():
    """get clients for client on tv dashboard"""
    if 'clients_cotv' not in DB:
        engine = get_engine()
        try:
            clients = pd.read_sql('select ADVERTISERS_GROUP_KEY,\
                    ADVERTISERS_GROUP_DISPLAY_NAME from \
                    client_on_tv_cl_tbl', engine)
        except:
            clients = pd.read_sql('call get_clients_cotv()', engine)
        clients = clients.dropna()
        clients['ADVERTISERS_GROUP_DISPLAY_NAME'] = clients['ADVERTISERS_GROUP_DISPLAY_NAME'].apply(
            lambda x: x.decode('unicode_escape').encode('ascii', 'ignore'))
        engine.dispose()
        DB['clients_cotv'] = pd.Series(
            clients.ADVERTISERS_GROUP_KEY.values,
            index=clients.ADVERTISERS_GROUP_DISPLAY_NAME).to_dict()


def cotv_get_genres():
    """get genres for client on tv dashboard"""
    if 'genres_dict' not in DB:
        engine = get_engine()
        g_qry = "select * from ref_genre_tg_mkt"
        genres_get = pd.read_sql(g_qry, engine)
        DB['genres_dict'] = pd.Series(
            genres_get.GENRE_KEY.values,
            index=genres_get.GENRE_DISPLAY_NAME).to_dict()
        engine.dispose()


def get_client_cos():
    """get clients for client on star dashboard"""
    if 'client_mapping_cos' not in DB:
        engine = get_engine()
        qry = 'select distinct(ADVERTISERS_GROUP_KEY), ADVERTISERS_GROUP_DISPLAY_NAME from fact_cust_rev_agg_dly'
        mappings_cos = pd.read_sql(qry, engine)
        engine.dispose()
        mappings_cos['ADVERTISERS_GROUP_DISPLAY_NAME'] = mappings_cos['ADVERTISERS_GROUP_DISPLAY_NAME'].apply(
            lambda x: x.decode('unicode_escape').encode('ascii', 'ignore'))
        DB['client_mapping_cos'] = pd.Series(
            mappings_cos.ADVERTISERS_GROUP_KEY.values,
            index=mappings_cos.ADVERTISERS_GROUP_DISPLAY_NAME).to_dict()
    return DB['client_mapping_cos']


def get_user_access(current_user, dashboard):

    auth_groups = create_groups()

    if 'REF_EMPLOYEE_HIERARCHY' not in DB:
        read_hierarchy()

    emp_role, sec_role = 'NONE', 'NONE'

    try:
        check_user = current_user.split('\\')[1].upper()
        print check_user
    except:
        raise HTTPError(401)

    try:
        emp_role = DB['REF_EMPLOYEE_HIERARCHY'][DB['REF_EMPLOYEE_HIERARCHY'][
            'EMPLOYEE_NT_ID'] == check_user]['EMPLOYEE_ROLE'].iloc[0]
    except:
        pass
    try:
        sec_role = DB['REF_EMPLOYEE_HIERARCHY'][DB['REF_EMPLOYEE_HIERARCHY'][
            'EMPLOYEE_NT_ID'] == check_user]['SECONDARY_ROLE'].iloc[0]
    except:
        pass

    if emp_role.startswith("-"):
        emp_role = 'NONE'

    if sec_role.startswith("-"):
        sec_role = 'NONE'

    if 'group_dict' not in DB:
        if 'REF_EMPLOYEE_HIERARCHY' not in DB:
            read_hierarchy()

        DB['group_dict'] = DB['REF_EMPLOYEE_HIERARCHY'][['EMPLOYEE_NT_ID',
                                                         'AUTH_GROUP']].set_index('EMPLOYEE_NT_ID').to_dict()['AUTH_GROUP']

    try:
        grp = auth_groups[DB['group_dict'][check_user]]
        print auth_groups[DB['group_dict'][check_user]], "++++++++++++++++++++++++++++"
    except:
        raise HTTPError(401)

    if ((emp_role.upper() != 'SALES EXECUTIVE') & (sec_role.upper() != 'SALES EXECUTIVE')):
        try:
            grp.remove('my_view')
        except:
            pass
    if (((emp_role.upper() == 'SALES EXECUTIVE') & (sec_role.upper() == 'SALES EXECUTIVE')) | ((emp_role.upper() == 'SALES EXECUTIVE') & (sec_role.upper() == 'NONE'))):
        try:
            grp.remove('my_view_manager')
        except:
            pass

    if DB['group_dict'][check_user].upper() == 'GROUP 1':
        try:
            if emp_role.upper() not in ['CLUSTER HEAD', 'BRANCH HEAD', 'HO GROUP']:
                grp.remove('client_on_star')
        except:
            pass

    if dashboard == 'index':
        return grp

    if dashboard in grp:
        return True
    else:
        raise HTTPError(401)


def get_refresh_status(dashboard):

    if dashboard == 'what_works':
        raise HTTPError(307)
        # need to call the control table which will be defined by star team
    return True
    #raise HTTPError(307)

# -- this function is used for generating md5 hash for bypassing the authentication for manager to sales executive traversal--


def create_hash(emp_key):
    m = hashlib.md5()
    m.update(str(emp_key) + 'star_gramex')
    return m.hexdigest()

#-- this function is responsible for getting the employee_key from userid


def get_emp_key_from_userid(userid):
    try:
        return DB['REF_EMPLOYEE_HIERARCHY'][DB['REF_EMPLOYEE_HIERARCHY']['EMPLOYEE_NT_ID'] == userid.upper()]['EMPLOYEE_KEY'].iloc[0]
    except:
        raise HTTPError(400)


def date_threshold():
    if 'myview_break_max' not in DB:
        engine = get_engine()
        DB['myview_rev_max'] = pd.read_sql(
            "select PRG_DATE from fact_cust_rev_agg_dly order by PRG_DATE desc limit 1;", engine)['PRG_DATE'].iloc[0]
        DB['myview_break_max'] = pd.read_sql(
            "select PRG_DATE from fact_cust_break_agg_dly order by PRG_DATE desc limit 1;", engine)['PRG_DATE'].iloc[0]


def slug_special(s):
    return s.replace('&', 'and')
