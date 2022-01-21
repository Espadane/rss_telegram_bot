import requests
import feedparser
from bs4 import BeautifulSoup


def get_records_from_rss(request_url):
    """Получение записей из ленты по ссылке на фид"""
    feed = feedparser.parse(f'{request_url}')
    news = feed['entries']
    records = []
    for new in news[0:5]:
        record_id = new['id']
        record_title = new['title']
        record_link = new['link']
        try:
            feed_name = get_feed_name(request_url)
        except:
            feed_name = ' '
        records.append({
            'feed_name': feed_name,
            'feed_url': request_url,
            'record_id': record_id,
            'record_title': record_title,
            'record_link': record_link,
        })

    return records


def get_feed_name(request_url):
    """Получение названия ленты"""
    r = requests.get(request_url)
    soup = BeautifulSoup(r.text, 'lxml')
    feed_name = soup.title.text

    return feed_name


def get_magnet_link(record_link):
    """Получение магнет ссылки"""
    r = requests.get(record_link)
    soup = BeautifulSoup(r.text, 'lxml')
    magnet_link = soup.find('a', class_='magnet-link').get('href')

    return magnet_link
