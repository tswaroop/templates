# Instructions for use

# Please install flask,flask-restless,flask-script,BeautifulSoup and lxml. 
# Please run the flask server like the following - python scraper.py
# Please go to the following url
# http://localhost:5000/api/newsticker?q={"filters":[{"name":"SearchTerm","op":"eq","val":"india"}]}
# for getting all the news for india
# if the search term's data is not present in the DB it will automatically
# scrap news.google.com's rss feed and store it in a sqlite DB in the same dir as the flask server
# Next time we run the same url it will execute faster

import flask
import pandas as pd
import requests
import csv

from waitress import serve
from urllib import quote
from datetime import datetime, timedelta
from flask.ext.restless import APIManager
from sqlalchemy import Integer, Text, DateTime, create_engine
from sqlalchemy.sql.schema import Column,UniqueConstraint
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from lxml import etree
from bs4 import BeautifulSoup

app = flask.Flask(__name__)
app.debug = True

engine = create_engine('sqlite:///newsticker.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

class NewsTicker(Base):
    __tablename__ = 'newsticker'
    uid = Column(Integer,autoincrement=True,primary_key=True)
    Title = Column(Text,nullable=False)
    PublishDate = Column(DateTime, nullable=False)
    Link = Column(Text, nullable=False)
    Source = Column(Text, nullable=False)
    SearchTerm = Column(Text, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('Title','PublishDate','Link','Source','SearchTerm',name='unique_news_item'),
    )

def get_news(search_params):
    if search_params.has_key('filters'):
        searchterm = search_params['filters'][0]['and'][0]['val'].lower()
        search_params['filters'][0]['and'][0]['val'] = searchterm
        cnt = 0
        pub_dt_threshold = (datetime.now() - timedelta(weeks=2))
        for news in  NewsTicker.query.filter_by(SearchTerm=searchterm):
            if news.PublishDate > pub_dt_threshold:
                cnt += 1
        if cnt == 0:

            url = "http://news.google.co.in/news?q={}&output=rss".format(quote(searchterm.encode('utf-8')))
            tree = etree.fromstring(requests.get(url,verify=False).text).getchildren()[0]
            news_items = [item for item in tree if item.tag == 'item']

            for news_item in news_items:
                news_item = {attr.tag.capitalize():attr.text for attr in news_item.getchildren()}
                
                new_row = NewsTicker(
                    Title = news_item['Title'],
                    PublishDate = datetime.strptime(news_item['Pubdate'],'%a, %d %b %Y %H:%M:%S %Z'),
                    Link = news_item['Link'],
                    Source = BeautifulSoup(news_item['Description'],'lxml').find(color="#6f6f6f").string,
                    SearchTerm = searchterm
                )

                db_session.add(new_row)
                db_session.commit()

api_manager = APIManager(app, session=db_session)
api_manager.create_api(NewsTicker, methods=['GET'],preprocessors={'GET_MANY': [get_news]})

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine,checkfirst=True)
    #app.run(host='0.0.0.0',port=9876)
    serve(app,host='0.0.0.0',port=9876,threads=4)