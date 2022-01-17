import requests
import feedparser
from bs4 import BeautifulSoup
from db_worker import *


def get_records(feed_url):
    """Получение записей из ленты по ссылке на фид"""
    feed = feedparser.parse(f'{feed_url}')
    news = feed['entries']
    records = []

    for new in news:
        record_id = new['id']
        record_title = new['title']
        record_link = new['link']
        if 'rutracker' in record_link:
            try:
                magnet_link = get_magnet_link(record_link)
            except:
                magnet_link = ''
        else:
            magnet_link = ''

        records.append({'record_id': record_id,
                        'record_title': record_title,
                        'record_link': record_link,
                        'magnet_link': magnet_link
                        })

    return records


def get_feed_name(feed_url):
    """Получение названия ленты"""
    r = requests.get(feed_url)
    soup = BeautifulSoup(r.text, 'lxml')
    feed_name = soup.title.text

    return feed_name


def get_magnet_link(record_link):
    """Получение магнет ссылки"""
    r = requests.get(record_link)
    soup = BeautifulSoup(r.text, 'lxml')
    magnet_link = soup.find('a', class_='magnet-link').get('href')

    return magnet_link
