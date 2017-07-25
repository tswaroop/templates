import urllib2
import json
import xmltodict
import pandas as pd
from templates.common.common import get_engine
#import client_overview

def newsticker(searchitem):
    try:
        search_term = searchitem
        search_term = search_term.replace(' ','')
        dfnews = pd.read_csv('../../data/data_newsticker.csv')
        if search_term in dfnews['SearchTerm'].unique():
            dfnews = dfnews[dfnews['SearchTerm'] == search_term]
            newstitle = list(dfnews['Title'])
            link = list(dfnews['Link'])
            newstick = []
            for i in range(len(newstitle)):
                newshref = "href = %s"%link[i]
                newsanchor = '<a target = "blank" class="tab" {:s}>{:s}</a>'.format( newshref.encode('utf-8') , newstitle[i].encode('utf-8'))
                newstick.append(newsanchor)
            # print len(newstick),'test'
            newstickitems = newstick
        else:
            url = 'https://news.google.co.in/news?q=%s&output=rss'%(search_term)
            req = urllib2.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3')
            response = urllib2.urlopen(req)
            html = response.read()
            dictdata = xmltodict.parse(html)
            jdata =json.dumps(dictdata)
            jdata=json.loads(jdata)

            newstitle = []
            publishDate = []
            link= []
            source = []

            num_items = len(jdata['rss']['channel']['item'])
            if (num_items >= 10):
                range_val = 10
            else:
                range_val = num_items

            for x in range(range_val):
                newstitle.append(jdata['rss']['channel']['item'][x]['title'])
                publishDate.append(jdata['rss']['channel']['item'][x]['pubDate'])
                urlink = jdata['rss']['channel']['item'][x]['link']
                actlink = urlink.split("url=")[1]
                link.append(actlink)
                source_part =  jdata['rss']['channel']['item'][x]['description'].split('<b><font color="#6f6f6f">')
                actualSource = source_part[1].split('</font>')
                source.append(actualSource[0])
            newstick = []
            df = pd.DataFrame()
            df['Title'] = newstitle
            df['PublishDate'] = publishDate
            df['Link'] = link
            df['Source'] = source
            df['SearchTerm'] = search_term
            with open('../../data/data_newsticker.csv', 'a') as f:
              df.to_csv(f, header=False,index=False)
            for i in range(len(newstitle)):
                newshref = "href = %s"%link[i]
                newsanchor = '<a target = "blank" class="tab" {:s}>{:s}</a>'.format( newshref.encode('utf-8') , newstitle[i].encode('utf-8'))
                newstick.append(newsanchor)
            # print newstick,'test1'
            newstickitems = newstick

        return newstickitems
    except:
        return ['Not Available']

def update_newsticker():
    engine = get_engine()
    conn = engine.connection()
    create_table_sql = """CREATE TABLE IF NOT EXISTS star_custdb.newsticker(
            `Title` varchar(100),
            `PublishDate` varchar(100),
            `Link` varchar(200),
            `Source` varchar(100),  
            `SearchTerm` varchar(100))"""
    conn.execute(create_table_sql)
    conn.close()
    