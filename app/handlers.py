import os
import time
import re
import random
import PIL.Image

from dotenv import load_dotenv

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from app.states import Ai
from app.database.requests import set_user

import google.generativeai as genai


router = Router()
load_dotenv()
genai.configure(api_key=os.getenv('AI_TOKEN'))
model = genai.GenerativeModel('gemini-2.0-flash')


async def remove_markdown(text):
    text = re.sub(r'[_*`]', '', text)
    return text


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await set_user(message.from_user.id)
    await message.answer('Ехало, жду запросы)')
    await state.clear()


@router.message(Command('help'))
async def help(message: Message, state: FSMContext):
    await message.answer('Напиши любой вопрос и я отвечу на него или отправь изображение где я смогу описать его')
    await state.clear()


@router.message(F.photo)
@router.message(Ai.question, F.photo)
async def chatgpt_question_photo(message: Message, state: FSMContext):
    await state.set_state(Ai.answer)
    rrand = random.randint(1, 9999)
    ddate = time.time()
    await message.bot.download(file=message.photo[-1].file_id, destination=f'ph{rrand}{ddate}.jpg')
    img = PIL.Image.open(f'ph{rrand}{ddate}.jpg')
    response = model.generate_content(img)
    os.remove(f'ph{rrand}{ddate}.jpg')
    try:
        await message.answer(response.text, parse_mode='Markdown')
    except:
        try:
            await message.answer(await remove_markdown(response.text))
        except:
            try:
                await message.answer(response.text)
            except Exception as e:
                print(e)
                await message.answer('Ошибка. Пожалуйста обратитесь за поддержкой: @imkrww')
    await state.clear()


@router.message(Ai.answer)
async def answer(message: Message):
    await message.answer('Притормози, я еще не ответил на твой предыдущий запрос-_-')


@router.message(Ai.question)
@router.message(F.text)
async def ai(message: Message, state: FSMContext):
    await state.set_state(Ai.answer)
    try:
        chat = await state.get_data()['context']
        if len(chat.history) > 15:
            chat = model.start_chat(history=[])
        response = await chat.send_message_async(message.text)
        await state.update_data(context=chat)
    except:
        chat = model.start_chat(history=[])
        response = await chat.send_message_async(message.text)
        await state.update_data(context=chat)
    await message.answer(response.text)
    await state.set_state(Ai.question)
