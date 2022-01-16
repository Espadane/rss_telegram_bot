from os import getenv
from sys import exit
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from rss_parser import *
from db import *


bot_token = getenv("RSS_BOT_TOKEN")
if not bot_token:
    exit("Ошибка - нет токена для бота.")

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_command(msg: types.Message):
    """Обработчик команды '/start'"""
    await msg.answer(f"Привет, {msg.from_user.first_name}!\nЯ бот который работает с RSS лентами. Просто пришли мне ссылку и я буду отслеживать для тебя новости.\nПожалуйста, если у тебя есть пожелания напиши: t.me/espadane",disable_web_page_preview=True)
    user_id = msg.from_user.id
    print(user_id)
    loop = asyncio.get_event_loop()
    loop.create_task(check_new_records(user_id))


@dp.message_handler(commands=['help'])
async def help_command(msg: types.Message):
    """Обработчик команды '/help'"""
    await msg.answer(f"Просто пришли мне ссылку на RSS и я буду проверять для тебя новости. \nЧтобы посмотреть потоки за которыми ты следишь набири команду '/all'. \nПо нажатию на кнопку можно прекратить отлеживание.'",disable_web_page_preview=True)

@dp.message_handler(commands=['all'])
async def process_start_command(msg: types.Message):
    """Обработчик команды '/all'для удаления всех отслеживаемых объявлений"""
    user_id = msg.from_user.id
    all_user_feed = get_all_user_feed(user_id)
    if len(all_user_feed) < 1:
        await msg.answer('Нет ресурсов для отслеживания')
    else:
        for user_feed in all_user_feed:
            user_feed_name = user_feed[0]
            user_feed_url = user_feed[1]
            button=(types.InlineKeyboardButton(text=f"Перестать отслеживать", callback_data='delete_feed'))
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(button)
            await msg.answer(f'{user_feed_name}\n{user_feed_url}', reply_markup=keyboard,disable_web_page_preview=True)

@dp.callback_query_handler(text='delete_feed')
async def delete_ad(call: types.callback_query):
    """Удаление остлеживаемых feed по клику на кнопку"""
    feed_title_to_delete = str(call.message.text).split('\n')[0]
    feed_url_to_delete = str(call.message.text).split('\n')[1]
    user_id = str(call.message.chat.id)
    delete_user_feed(user_id, feed_url_to_delete)
    await call.answer(str(f'Объявление больше не отслеживается: {feed_url_to_delete}'), show_alert=True)


@dp.message_handler(Text)
async def add_rss(msg:types.Message):
    user_id = msg.from_user.id
    if 'feed' in msg.text:
        feed_url = msg.text
        news = get_news(msg.text)
        if news != []:
            feed_name = get_feed_name(feed_url)
            title = news[0]['record_title']
            link = news[0]['record_link']
            magnet_link = news[0]['magnet_link']
            await msg.answer(f'Корректная ссылка на канал "{feed_name}"')
            await msg.answer(f'Последняя новость в канале:\n<a href="{link}">{title}</a>\n{magnet_link}\n',parse_mode = 'HTML')
            for new in news:
                write_rss_to_db(user_id, feed_name, feed_url, new)

        else:
            await msg.answer('Ссылка на канал не корректна')

async def check_new_records(user_id):
    while True:
        user_rss_list = get_user_rss_list(user_id)
        if len(user_rss_list) >= 1:
            for feed_url in user_rss_list:
                feed_name = get_feed_name(feed_url)
                news = get_news(feed_url)
                id_to_add, id_to_delete = check_new(user_id, feed_url, news)
                print(f'новости для добавления в базу: {id_to_add}')
                for i in id_to_delete:
                    delete_last_record(user_id, i)
                for new in news:
                    for i in id_to_add:
                        if i == new['record_id']:
                            write_rss_to_db(user_id, feed_name, feed_url, new)
                            title = new['record_title']
                            link = new['record_link']
                            if 'rutracker' in link:
                                magnet_link = new['magnet_link']
                                await bot.send_message(user_id, f'#{feed_name}\n\n<a href="{link}">{title}</a>\nМагнет ссылка:\n{magnet_link}\n',parse_mode = 'HTML', disable_web_page_preview=True)
                            else:
                                await bot.send_message(user_id, f'#{feed_name}\n\n<a href="{link}">{title}</a>\n',parse_mode = 'HTML')

        await asyncio.sleep(1800)


if __name__ == '__main__':
    executor.start_polling(dp)
# http://feed.rutracker.cc/atom/f/635.atom
# https://losst.ru/feed