import sqlite3
from urllib import response


conn = sqlite3.connect('db.db')
cursor = conn.cursor()


def create_table_tracked_feeds():
    """Создание таблицы с отслеживаемыми лентами, если она еще не существует"""
    try:
        cursor.execute('create table if not exists tracked_feeds(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, feed_name text NOT NULL, feed_url text NOT NULL, record_id text NOT NULL, record_title text NOT NULL, record_link text NOT NULL)')
        conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)


def write_feed_to_db(user_id, feed_name, feed_url, record):
    """Добавление новой записи в базу данных"""
    record_id = record['record_id']
    record_title = record['record_title']
    record_link = record['record_link']
    try:
        cursor.execute('INSERT INTO tracked_feeds (user_id, feed_name, feed_url, record_id, record_title, record_link) VALUES (?, ?, ?, ?, ?, ?)',
                       (user_id, feed_name, feed_url, record_id, record_title, record_link))
        conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)


def get_user_feed_list(user_id):
    """Получение из базы данных списка отслеживаемых пользователем лент"""
    user_rss_list = []
    for row in cursor.execute('SELECT feed_url FROM tracked_feeds WHERE user_id = ?', (user_id,)):
        if row[0] not in user_rss_list:
            user_rss_list.append(row[0])

    return user_rss_list


def delete_last_record(user_id, record_id):
    """Удаление старой записи из базы данных"""
    try:
        cursor.execute(
            'DELETE FROM tracked_feeds WHERE user_id = ? and record_id = ?', (user_id, record_id))
        conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)


def get_records_from_db(user_id, feed_url):
    """Получение последних записей пользователя из базы данных, по адресу ленты"""
    cursor.execute(
        'SELECT record_id, record_title, record_link FROM tracked_feeds WHERE user_id = ? and feed_url = ?', (user_id, feed_url))
    records = cursor.fetchall()

    return records


def check_new_records_from_db(user_id, feed_url, records):
    """Проверка новых записей в базе данных, путем сравнивая списка новостей из полученой ленты и списка новостей из базы данных. Возвращает два списка. В первом айди записей для добавляения в базу данных, во втором для удаления из базы."""
    new_id_list = []
    old_id_list = []
    for record in records:
        new_id_list.append(record['record_id'])
    records_from_db = get_records_from_db(user_id, feed_url)
    for record in records_from_db:
        old_id_list.append(record[0])

    id_to_add_list = list(set(new_id_list) - set(old_id_list))
    id_to_delete_list = list(set(old_id_list) - set(new_id_list))

    return id_to_add_list, id_to_delete_list


def get_all_user_feed(user_id):
    """Получение списка всех лет которые отслеживает пользователь"""
    cursor.execute(
        'SELECT feed_name, feed_url FROM tracked_feeds WHERE user_id = ? ', (user_id,))
    all_user_feed = cursor.fetchall()

    return list(set(all_user_feed))


def delete_user_feed(user_id, feed_url_to_delete):
    """Удаление отслеживаемой ленты пользователя из базы данных"""
    try:
        cursor.execute('DELETE FROM tracked_feeds WHERE user_id = ? and feed_url = ?',
                    (user_id, feed_url_to_delete))
        conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)

def check_feed_url_in_db(feed_url):
    """Проверка отслеживается ли лента"""
    cursor.execute(
        'SELECT feed_url from tracked_feeds WHERE feed_url = ?', (feed_url,))
    response = cursor.fetchone()

    return response


create_table_tracked_feeds()
