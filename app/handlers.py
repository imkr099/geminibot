import os
from dotenv import load_dotenv

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from app.states import Ai
from app.database.requests import set_user

import google.generativeai as genai


router = Router()
load_dotenv()
genai.configure(api_key=os.getenv('AI_TOKEN'))
model = genai.GenerativeModel('gemini-1.5-pro-latest')


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await set_user(message.from_user.id)
    await message.answer('Ехало, жду запросы)')
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
