import requests
from bs4 import BeautifulSoup


def get_records_from_telegram(request_url):
    preview_url = 'https://t.me/s/' + request_url.split('/')[-1]
    tg_posts = []
    r = requests.get(preview_url)
    soup = BeautifulSoup(r.text, 'lxml')
    posts = soup.find_all('div', class_='tgme_widget_message_wrap')
    feed_name = soup.title.text
    for post in posts[len(posts)-5:len(posts)]:
        post_title_chunks = post.find(
            'div', class_='js-message_text').text.split(' ')
        post_title = ' '.join(post_title_chunks[0:7]) + ' ...'
        post_id = post.find(
            'div', class_='tgme_widget_message').get('data-post')
        post_link = f'https://t.me/{post_id}'
        tg_posts.insert(0, {
            'feed_name': feed_name,
            'feed_url': preview_url,
            'record_id': post_id,
            'record_title': post_title,
            'record_link': post_link
        })
    return tg_posts
