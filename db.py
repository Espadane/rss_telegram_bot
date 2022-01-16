import sqlite3


conn = sqlite3.connect('db.db')
cursor = conn.cursor()


def create_table_rss():
    """Созадние базы данных если она еще не существует"""
    cursor.execute('create table if not exists tracked_rss(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, feed_name text NOT NULL, feed_url text NOT NULL, last_rss_record_id text NOT NULL, last_rss_record_title text NOT NULL, last_rss_record_link text NOT NULL)')
    conn.commit()

def write_rss_to_db(user_id, feed_name, feed_url, news):
    print(news)
    record_id = news['record_id']
    record_title = news['record_title']
    record_link = news['record_link']
    try:
        cursor.execute('INSERT INTO tracked_rss (user_id, feed_name, feed_url, last_rss_record_id, last_rss_record_title, last_rss_record_link) VALUES (?, ?, ?, ?, ?, ?)', (user_id, feed_name, feed_url, record_id, record_title, record_link))
        print(f'Запись {record_title} добавлена в базу')
        conn.commit()
    except sqlite3.Error as error:
        print("Ошибка", error)

def get_user_rss_list(user_id):
    user_rss_list = []
    for row in cursor.execute('SELECT feed_url FROM tracked_rss WHERE user_id = ?', (user_id,)):
        if row[0] not in user_rss_list:
            user_rss_list.append(row[0])

            
    return user_rss_list

def delete_last_record(user_id, last_rss_record_id):
    cursor.execute('DELETE FROM tracked_rss WHERE user_id = ? and last_rss_record_id = ?', (user_id, last_rss_record_id))
    print(f'Запись {last_rss_record_id} удалена')
    conn.commit()

def get_old_news(user_id, feed_url):
    cursor.execute('SELECT last_rss_record_id, last_rss_record_title, last_rss_record_link FROM tracked_rss WHERE user_id = ? and feed_url = ?', (user_id, feed_url))
    r = cursor.fetchall()
    return r

def check_new(user_id, feed_url, news):
    new_id_list = []
    old_id_list = []
    for new in news:
        new_id_list.append(new['record_id'])
    old_news = get_old_news(user_id, feed_url)
    for old in old_news:
        old_id_list.append(old[0])

    id_to_add=list(set(new_id_list) - set(old_id_list))
    id_to_delete=list(set(old_id_list) - set(new_id_list))

    return id_to_add, id_to_delete


def get_all_user_feed(user_id):
    cursor.execute('SELECT feed_name, feed_url FROM tracked_rss WHERE user_id = ? ', (user_id,))
    all_user_feed = cursor.fetchall()


    return list(set(all_user_feed))

def delete_user_feed(user_id, feed_url_to_delete):
    cursor.execute('DELETE FROM tracked_rss WHERE user_id = ? and feed_url = ?', (user_id, feed_url_to_delete))
    print(f'{feed_url_to_delete} удален')
    conn.commit()



create_table_rss()