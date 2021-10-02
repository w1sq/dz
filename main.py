# coding=utf8
import asyncio
from asyncio import events
import logging
import aiogram.utils.markdown as fmt
from datetime import datetime
from aiogram import Bot, Dispatcher, executor,types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InputTextMessageContent, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultPhoto
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types.bot_command import BotCommand
from aiogram.types.inline_query_result import InlineQueryResultArticle
import requests
from bs4 import BeautifulSoup

def generate_keyboard (*answer):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    temp_buttons = []
    for i in answer:
        temp_buttons.append(KeyboardButton(text=i))
    keyboard.add(*temp_buttons)
    return keyboard

def generate_inline_keyboard (*answer):
    keyboard = InlineKeyboardMarkup()
    temp_buttons = []
    for i in answer:
        temp_buttons.append(InlineKeyboardButton(text=str(i[0]), callback_data=i[1]))
    keyboard.add(*temp_buttons)
    return keyboard

with open('key.txt','r') as file:
    API_KEY = file.readline()
logging.basicConfig(level=logging.INFO, filename='botlogs.log')
bot = Bot(token=API_KEY)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=MemoryStorage())
print('Bot started')

class GetNumber(StatesGroup):
    rus_ege_sdamgia_ru = State()

website_keyboard = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True).row(KeyboardButton('Сдам Гиа'))
sdamgia_subjects_keyboard = InlineKeyboardMarkup(resize_keyboard=True).row(InlineKeyboardButton(text='Русский',callback_data='sdamgia_rus'))
sdamgia_exams_keyboard = InlineKeyboardMarkup(resize_keyboard=True).row(InlineKeyboardButton(text='ЕГЭ',callback_data='sdamgia_ege'))


@dp.message_handler(commands=['start'])
async def start(message):
    await message.answer('Бот пока находится в разработке, не все предметы и сайты еще добавлены.\n\nВыберите желаемый сайт:',reply_markup=website_keyboard)

@dp.message_handler(text='Сдам Гиа')
async def search_serial(message):
    await message.delete()
    await message.answer('Выберите экзамен: ',reply_markup=sdamgia_exams_keyboard)

@dp.message_handler(state=GetNumber.rus_ege_sdamgia_ru)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        keyb =  InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(InlineKeyboardButton(text='Вернуться к выбору предмета',callback_data='sdamgia_ege')).row(InlineKeyboardButton(text='Вернуться к выбору экзамена',callback_data='choose_exam')).row(InlineKeyboardButton(text='Ввести номер нового задания',callback_data='sdamgia_rus True'))
        if message.text == 'cancel':
            await message.answer('Успешно отменено',reply_markup=keyb)
            await message.delete()
            data.state = None
        else:
            try:
                msg = int(message.text)
                webpage = requests.get(f'https://rus-ege.sdamgia.ru/problem?id={message.text}').text
                soup = BeautifulSoup (webpage, 'html.parser')
                anwswer = soup.find_all("div", class_="answer")[-1].text
                if anwswer:
                    await message.answer(f'Задание №{message.text}\n'+anwswer,reply_markup=keyb)
                    data.state = None
                else:
                    await message.answer('Задания не найдено, попробуйте снова\nвведите cancel для отмены')
            except ValueError:
                await message.answer('Неправильный формат ввода, попробуйте снова\nвведите cancel для отмены')

async def sdamgia_rus(call,mode=False,*args):
    message = call.message
    await GetNumber.rus_ege_sdamgia_ru.set()
    await message.answer('Введите номер задания')
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text=call.message.text, reply_markup=None)
    if not mode:
        await message.delete()

async def sdamgia_ege(call,*args):
    message = call.message    
    await message.answer('Выберите предмет',reply_markup = sdamgia_subjects_keyboard)
    await message.delete()

async def choose_exam(call,*args):
    message = call.message    
    await message.answer('Выберите экзамен',reply_markup = sdamgia_subjects_keyboard)
    await message.delete()

events = {'sdamgia_rus':sdamgia_rus,
    'sdamgia_ege':sdamgia_ege,
    'choose_exam':choose_exam
}

@dp.callback_query_handler(lambda call: True)
async def ans(call):
    command = call.data.split()
    await events[command[0]](call,*command[1:])

async def main():
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())