import time
import requests
from random import randint
import pandas as pd
import os
from sqlalchemy import create_engine
from scraper import NewsTicker

mysql_engine = create_engine('mysql://star:star_sales@localhost/star_custdb')

conn = mysql_engine.connection()
create_table_sql = """
	CREATE TABLE IF NOT EXISTS star_custdb.newsticker_archive(
        `Title` varchar(100),
        `PublishDate` varchar(100),
        `Link` varchar(200),
        `Source` varchar(100),  
        `SearchTerm` varchar(100));

	ALTER TABLE star_custdb.newsticker_archive ADD CONSTRAINT UniqueNewsConstraint UNIQUE(Title, Source, Link, PublishDate, SearchTerm);
"""
conn.execute(create_table_sql)

for news in NewsTicker.query.all():
	insert_row_sql = """
		INSERT IGNORE INTO star_custdb.newsticker_archive('Title','PublishDate','Link','Source','SearchTerm')
		({},{},{},{},{})
	""".format(news.Title,news.PublishDate,news.Link,news.Source,news.SearchTerm)
	conn.execute(insert_row_sql)

conn.close()

start = time.clock()

print 'Scraping top 250 clients news items started ...'

for SearchTerm in pd.read_csv('top_250_clients.csv',header=None)[0]:
	print 'Scraping data for {}'.format(SearchTerm)
	url = 'http://api.newsticker.com:5000/api/newsticker?q={"filters":[{"name":"SearchTerm","op":"eq","val":"' + SearchTerm + '"}]}'
	requests.get(url)
	time.sleep(randint(50,60))

print 'Scraping complete !'

print 'Time taken - {}'.format(str(time.clock() - start))

