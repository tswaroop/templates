Requirement
-------

>To create a client specific newsticker that scrolls down in the dashboard & to capture the  following details in the database

* News Title
* Publish Date
* Link


Learnings
-------

* Google has deprecate google news api
* Next alternative we have is using Google RSS to scrap news
* Google news RSS link - https://news.google.com/news?q=apple&output=rss


 Approch
--------

* To scrap html source from google news RSS
* Convert xml to json and parse and gather the details for top 10 news items for the client
* Do this for all the clients
* Store it in DB
 
Pyhton Packages Used
----

* json
* xmltojson
* urllib2


Computation Time
---
* It takes about 0.01 seconds to gather 10 news items along with all the other relative measure and write it into a csv file for a single client

Architecture
---
*Check for the csv files for the client
*If news items are present pick the news items from the csv file and use it for newsticker
*else scrap the news from google news for the client append it in csv file and then use it for newsticker
*csv file will be refreshed weekly through scheduled job

 
