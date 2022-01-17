from os import getenv
from sys import exit
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from rss_parser import *
from db_worker import *


bot_token = getenv("TEST_TOKEN")
if not bot_token:
    exit("Ошибка - нет токена для бота.")

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_command(msg: types.Message):
    """Обработчик команды '/start' и запуск цикла процесса проверки новых записей во всех лентах пользователя"""
    await msg.answer(f"Привет, {msg.from_user.first_name}!\nЯ бот который работает с RSS лентами. Просто пришли мне ссылку и я буду отслеживать для тебя новости.\nПожалуйста, если у тебя есть пожелания напиши: t.me/espadane", disable_web_page_preview=True)
    user_id = msg.from_user.id
    loop = asyncio.get_event_loop()
    loop.create_task(check_new_records(user_id))


@dp.message_handler(commands=['help'])
async def help_command(msg: types.Message):
    """Обработчик команды '/help'"""
    await msg.answer(f"Просто пришли мне ссылку на RSS лоенту и я буду проверять для тебя новости. \nЧтобы посмотреть ленты за которыми ты следишь набери команду '/all'. \nПо нажатию на кнопку можно прекратить отлеживание.'")


@dp.message_handler(commands=['all'])
async def all_command(msg: types.Message):
    """Обработчик команды '/all'для вывода всех отслеживаемых лент с кнопками 'удалить' и 'последние записи'"""
    user_id = msg.from_user.id
    all_user_feed = get_all_user_feed(user_id)
    if len(all_user_feed) < 1:
        await msg.answer('Нет ресурсов для отслеживания')
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
    feed_url = msg.text
    response = check_feed_url_in_db(feed_url)
    if response == None:
        records = get_records(msg.text)
        if records != []:
            try:
                feed_name = get_feed_name(feed_url)
                title = records[0]['record_title']
                link = records[0]['record_link']
                magnet_link = records[0]['magnet_link']
                await msg.answer(f'Корректная ссылка на канал "{feed_name}"')
                await msg.answer(f'Последняя новость в канале:\n<a href="{link}">{title}</a>\n\n{magnet_link}\n', parse_mode='HTML')
                for record in records:
                    write_feed_to_db(user_id, feed_name, feed_url, record)
            except:
                await msg.answer('Ссылка на канал не корректна')
    else:
        await msg.answer(f'Данная лента уже отслеживается')



async def check_new_records(user_id):
    """Проверка новых записей в ленте по id записи и сверка их с записями в базе данных для каждого пользователя отдельно. Если новых записей нет, не происходит ничего. Если новые записи есть, то они записываются в базу данных, а старые записи удаляются на тоже количество. Отправка новых записей пользователю. По умолчанию проверка выполняется раз в пол часа."""
    while True:
        user_feed_list = get_user_feed_list(user_id)
        if len(user_feed_list) >= 1:
            for feed_url in user_feed_list:
                feed_name = get_feed_name(feed_url)
                records = get_records(feed_url)
                id_to_add_list, id_to_delete_list = check_new_records_from_db(
                    user_id, feed_url, records)
                print(f'Новых записей - {len(id_to_add_list)}')
                for id_to_delete in id_to_delete_list:
                    delete_last_record(user_id, id_to_delete)
                for new_record in records:
                    for id_to_add in id_to_add_list:
                        if id_to_add == new_record['record_id']:
                            write_feed_to_db(
                                user_id, feed_name, feed_url, new_record)
                            title = new_record['record_title']
                            link = new_record['record_link']
                            if 'rutracker' in link:
                                magnet_link = new_record['magnet_link']
                                await bot.send_message(user_id, f'#{feed_name.replace(" ", "_")}\n\n<a href="{link}">{title}</a>\nМагнет ссылка:\n{magnet_link}\n', parse_mode='HTML', disable_web_page_preview=True)
                            else:
                                await bot.send_message(user_id, f'#{feed_name.replace(" ", "_")}\n\n<a href="{link}">{title}</a>\n', parse_mode='HTML')

        await asyncio.sleep(1800)


if __name__ == '__main__':
    executor.start_polling(dp)
