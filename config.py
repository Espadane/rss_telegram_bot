from os import getenv
from sys import exit


bot_token = getenv("RSS_BOT_TOKEN")
if not bot_token:
    exit("Ошибка - нет токена для бота.")

vk_token = getenv('VK_BOT_TOKEN')
if not vk_token:
    print('Ошибка - нет токена для vk.') 