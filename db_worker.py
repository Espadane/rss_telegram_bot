import sqlite3


conn = sqlite3.connect('db.db')
cursor = conn.cursor()

sources_names = ['rss', 'vk', 'tg']


def create_table_tracked_feeds():
    """Создание таблицы с отслеживаемыми лентами, если она еще не существует"""
    try:
        cursor.execute('create table if not exists rss_sources(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, feed_name text NOT NULL, feed_url text NOT NULL, record_id text NOT NULL, record_title text NOT_NULL, record_link text NOT NULL)')
        cursor.execute('create table if not exists vk_sources(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, feed_name text NOT NULL, feed_url text NOT NULL, record_id text NOT NULL, record_title text NOT_NULL, record_link text NOT NULL )')
        cursor.execute('create table if not exists tg_sources(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, feed_name text NOT NULL, feed_url text NOT NULL, record_id text NOT NULL, record_title text NOT_NULL, record_link text NOT NULL )')
        conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)


def write_record_to_db(user_id, record, source_name):
    """Добавление новой записи в базу данных"""
    feed_name = record['feed_name']
    feed_url = record['feed_url']
    record_id = record['record_id']
    record_title = record['record_title']
    record_link = record['record_link']
    try:
        cursor.execute(f'INSERT INTO {source_name}_sources (user_id, feed_name, feed_url, record_id, record_title, record_link) VALUES (?, ?, ?, ?, ?, ?)',
                       (user_id, feed_name, feed_url, record_id, record_title, record_link))
        conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)


def get_user_feed_list(user_id):
    """Получение из базы данных списка отслеживаемых пользователем источников"""
    user_source_list = []
    for source_name in sources_names:
        for row in cursor.execute(f'SELECT feed_url FROM {source_name}_sources WHERE user_id = ?', (user_id,)):
            if row[0] not in user_source_list:
                user_source_list.append(row[0])

    return user_source_list


def delete_last_record(user_id, record_id):
    """Удаление старой записи из базы данных"""
    try:
        for source_name in sources_names:
            cursor.execute(
                f'DELETE FROM {source_name}_sources WHERE user_id = ? and record_id = ?', (user_id, record_id))
            conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)


def get_records_from_db(user_id, feed_url):
    """Получение последних записей пользователя из базы данных, по адресу ленты"""
    records = []
    for source_name in sources_names:
        for row in cursor.execute(f'SELECT record_id, record_title, record_link  FROM {source_name}_sources WHERE user_id = ? and feed_url = ?', (user_id, feed_url)):
            records.append(row)

    return records


def check_new_records_from_db(user_id, feed_url, records):
    """Проверка новых записей в базе данных, путем сравнивая списка новостей из полученного источника и списка новостей из базы данных. Возвращает два списка. В первом айди записей для добавляения в базу данных, во втором для удаления из базы."""
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


def get_all_user_feed(user_id, source_name):
    """Получение списка всех источников которые отслеживает пользователь"""
    cursor.execute(
        f'SELECT feed_name, feed_url FROM {source_name}_sources WHERE user_id = ? ', (user_id,))
    all_user_feed = cursor.fetchall()

    return list(set(all_user_feed))


def delete_user_feed(user_id, feed_url_to_delete):
    """Удаление отслеживаемого источника пользователя из базы данных"""
    try:
        for source_name in sources_names:
            cursor.execute(f'DELETE FROM {source_name}_sources WHERE user_id = ? and feed_url = ?',
                           (user_id, feed_url_to_delete))
            conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)


def check_feed_url_in_db(user_id, request_url):
    """Проверка отслеживается ли источник"""
    for source_name in sources_names:
        cursor.execute(
            f'SELECT feed_url from {source_name}_sources WHERE user_id= ? AND feed_url = ?', (user_id, request_url))
        response = cursor.fetchone()
        if response != None:
            break

    return response


def get_users_list():
    users = []
    for source_name in sources_names:
        for row in cursor.execute(
                f'SELECT user_id from {source_name}_sources'):
            users.append(row[0])

    return set(users)


create_table_tracked_feeds()
