import requests
import config
from bs4 import BeautifulSoup


def get_posts_from_vk(request_url):
    """Получение постов из ленты пользователя или группы"""
    group_addr = get_group_addr(request_url)
    if 'id' in request_url:
        api_request = f'https://api.vk.com/method/wall.get?owner_id={group_addr}&count=5&access_token={config.vk_token}&v=5.131'
    else:
        api_request = f'https://api.vk.com/method/wall.get?domain={group_addr}&count=5&access_token={config.vk_token}&v=5.131'
    response = requests.get(api_request)
    api_data = response.json()
    entries = api_data['response']['items']
    posts = []
    for entrie in entries:
        if entrie.get('is_pinned') != None:
            continue
        post_id = str(entrie['id'])
        post_text = entrie['text']
        if post_text == '':
            post_text = 'Запись'
        post_title = post_text[0:25] + ' ...'
        post_owner_id = str(entrie['owner_id'])
        post_link = f'https://vk.com/id{post_owner_id.replace("-","")}?w=wall{post_owner_id}_{post_id}'
        group_name = get_group_name(request_url)
        posts.append({
            'feed_name': group_name,
            'feed_url': request_url,
            'record_id': group_name + '_' + post_id,
            'record_title': post_title,
            'record_link': post_link
        })
    return posts


def get_group_addr(request_url):
    """получение айди адреса группы или пользователя вк из ссылки"""
    group_addr = str(request_url.split('/')[-1])
    if 'id' in group_addr:
        group_addr = group_addr.replace('id', '')

    return group_addr


def get_group_name(request_url):
    """получение имени группы или пользователя"""
    r = requests.get(request_url)
    soup = BeautifulSoup(r.text, 'lxml')
    group_name = soup.title.text.split(' ')[0:2]

    return ' '.join(group_name)
