import requests
import feedparser
from bs4 import BeautifulSoup
from db import *


def get_news(feed_url):
    feed = feedparser.parse(f'{feed_url}')
    records = feed['entries']
    news = []

    for record in records:
        record_id = record['id']
        record_title = record['title']
        record_link = record['link']
        if 'rutracker' in record_link:
            try:
                magnet_link = get_magnet_link(record_link)
            except:
                magnet_link = ''
        else:
            magnet_link = ''

        news.append({'record_id' : record_id,
                    'record_title' : record_title,
                    'record_link' : record_link,
                    'magnet_link' : magnet_link
                        })

    return news

def get_feed_name(feed_url):
    r = requests.get(feed_url)
    soup = BeautifulSoup(r.text, 'lxml')
    feed_name = soup.title.text

    return feed_name

def get_magnet_link(record_link):
    r = requests.get(record_link)
    soup = BeautifulSoup(r.text, 'lxml')
    magnet_link = soup.find('a', class_='magnet-link').get('href')

    return magnet_link
