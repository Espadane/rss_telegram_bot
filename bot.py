import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
import config
from rss import *
from telegram import get_records_from_telegram
from vk import *
from db_worker import *


bot_token = config.bot_token
if not bot_token:
    exit("Ошибка - нет токена для бота.")

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_command(msg: types.Message):
    """Обработчик команды '/start' и запуск цикла процесса проверки новых записей во всех лентах пользователя"""
    await msg.answer(f"Привет, {msg.from_user.first_name}!\nЯ новостной бот. Умею работать с RSS, VK. Просто пришли мне ссылку и я буду отслеживать для тебя новости.\nПожалуйста, если у тебя есть пожелания напиши: t.me/espadane", disable_web_page_preview=True)


@dp.message_handler(commands=['help'])
async def help_command(msg: types.Message):
    """Обработчик команды '/help'"""
    await msg.answer(f"Просто пришли мне ссылку на RSS ленту, аккаунт в VK и я буду проверять для тебя новости. \nЧтобы посмотреть источники за которыми ты следишь набери команду '/all_названиеисточника'. \nПо нажатию на кнопку можно прекратить отлеживание или посмотреть последние записи'")


@dp.message_handler(commands=['all_rss'])
@dp.message_handler(commands=['all_vk'])
@dp.message_handler(commands=['all_tg'])
async def all_command(msg: types.Message):
    """Обработчик команды '/all'для вывода всех отслеживаемых лент с кнопками 'удалить' и 'последние записи'"""
    user_id = msg.from_user.id
    source_name = msg.text.split('_')[1]
    all_user_feed = get_all_user_feed(user_id, source_name)
    if len(all_user_feed) < 1:
        await msg.answer('Нет отслеживаемых источников')
    else:
        for user_feed in all_user_feed:
            user_feed_name = user_feed[0]
            user_feed_url = user_feed[1]
            btn_delete = (types.InlineKeyboardButton(
                text=f"Перестать отслеживать", callback_data='delete_feed'))
            btn_last = (types.InlineKeyboardButton(
                text=f"Последние записи", callback_data='last_feed'))
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(btn_last, btn_delete)
            await msg.answer(f'{user_feed_name}\n{user_feed_url}', reply_markup=keyboard, disable_web_page_preview=True)


@dp.callback_query_handler(text='delete_feed')
async def delete_feed(call: types.callback_query):
    """Удаление остлеживаемых лент пользователя из базы данных по клику на кнопку"""
    feed_title_to_delete = str(call.message.text).split('\n')[0]
    feed_url_to_delete = str(call.message.text).split('\n')[1]
    user_id = str(call.message.chat.id)
    delete_user_feed(user_id, feed_url_to_delete)
    await call.answer(str(f'RSS лента больше не отслеживается: {feed_title_to_delete}'), show_alert=True)


@dp.callback_query_handler(text='last_feed')
async def last_feed(call: types.callback_query):
    '''Вывод последних записей в ленте пользователя из базы данных по клику на кнопку'''
    feed_url = str(call.message.text).split('\n')[1]
    user_id = str(call.message.chat.id)
    records = get_records_from_db(user_id, feed_url)
    for record in records:
        record_title = record[1]
        record_link = record[2]
        await bot.send_message(user_id, f'<a href="{record_link}">{record_title}</a>\n', parse_mode='HTML', disable_web_page_preview=True)


@dp.message_handler(Text)
async def add_feed(msg: types.Message):
    """Проверка сообщения пользователя, если сообщение является ссылкой на ленту, добавление ленты в отслеживаемые. Если лента уже отслеживается - сообщение пользователю. Небольшое дополнение для рутрекера с магнет ссылкой"""
    user_id = msg.from_user.id
    request_url = msg.text
    response = check_feed_url_in_db(user_id, request_url)
    if response == None:
        records_list, feed = get_records_list(request_url)
        if records_list != []:
            try:
                feed_name = records_list[0]['feed_name']
                title = records_list[0]['record_title']
                link = records_list[0]['record_link']
                if 'rutracker' in link:
                    try:
                        magnet_link = get_magnet_link(link)
                    except:
                        magnet_link = ''
                else:
                    magnet_link = ''
                await msg.answer(f'Корректная ссылка на источник "{feed_name}"')
                await msg.answer(f'Последняя новость:\n<a href="{link}">{title}</a>\n\n{magnet_link}\n', parse_mode='HTML')
                for record in records_list:
                    write_record_to_db(user_id, record, feed)
            except:
                await msg.answer('К сожалению данный источник отслеживать мы не имеем возможности.')
    else:
        await msg.answer(f'Данный источник уже отслеживается')


def get_records_list(request_url):
    """Получение записей в зависимости от источника"""
    if 'vk' in request_url:
        records_list = get_posts_from_vk(request_url)
        source_name = 'vk'
    elif 't.me' in request_url:
        records_list = get_records_from_telegram(request_url)
        source_name = 'tg'
    else:
        source_name = 'rss'
        records_list = get_records_from_rss(request_url)

    return records_list, source_name


async def check_new_records(user_id):
    """Проверка новых записей в ленте по id записи и сверка их с записями в базе данных для каждого пользователя отдельно. Если новых записей нет, не происходит ничего. Если новые записи есть, то они записываются в базу данных, а старые записи удаляются на тоже количество. Отправка новых записей пользователю. По умолчанию проверка выполняется раз в пол часа."""
    while True:
        user_feed_list = get_user_feed_list(user_id)
        if len(user_feed_list) >= 1:
            for feed_url in user_feed_list:
                feed_name = get_feed_name(feed_url)
                records, source_name = get_records_list(feed_url)
                id_to_add_list, id_to_delete_list = check_new_records_from_db(
                    user_id, feed_url, records)
                print(f'Новых записей - {len(id_to_add_list)}')
                for id_to_delete in id_to_delete_list:
                    delete_last_record(user_id, id_to_delete)
                for new_record in records:
                    for id_to_add in id_to_add_list:
                        if id_to_add == new_record['record_id']:
                            write_record_to_db(
                                user_id, new_record, source_name)
                            title = new_record['record_title']
                            link = new_record['record_link']
                            if 'rutracker' in link:
                                magnet_link = get_magnet_link(link)
                                await bot.send_message(user_id, f'#{feed_name}\n\n<a href="{link}">{title}</a>\nМагнет ссылка:\n{magnet_link}\n', parse_mode='HTML', disable_web_page_preview=True)
                            else:
                                await bot.send_message(user_id, f'#{feed_name}\n\n<a href="{link}">{title}</a>\n', parse_mode='HTML')

        await asyncio.sleep(1200)


def create_loops():
    users_list = get_users_list()
    if users_list != []:
        for user in users_list:
            loop = asyncio.get_event_loop()
            loop.create_task(check_new_records(user))


if __name__ == '__main__':
    create_loops()
    executor.start_polling(dp)
