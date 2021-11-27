from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_polling

from aiogram_keyboards import Keyboard, Button, setup_aiogram_keyboards, Orientation


# ====== initialization =======

bot = Bot('1729163324:AAHtCcEZYZ6yfBAKZhnyoTxMzFoqOpG69_M')
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

setup_aiogram_keyboards(dp)


# ====== keyboards init ======

class MainMenu(Keyboard):
    __text__ = 'Вот твоё меню'

    chose_crypto = Button('Выбрать криптовалююту')


class UndoKeyboard(Keyboard):
    __orientation__ = Orientation.BOTTOM

    undo = Button('Отмена')


class Cryptos(UndoKeyboard):
    __text__ = 'Выбери криптовалюту'

    BTC = Button('Биткоин', data='BTC')
    ETH = Button('Эфириум', data='ETH')


# =========== bind =============

MainMenu.chose_crypto >> Cryptos
UndoKeyboard.undo >> MainMenu


# ========== handlers ==========

# set entry point of MainMenu
@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    await MainMenu.process(message.chat.id)


# handle all answers contains in Cryptos keyboard
@Cryptos.handle()
async def crypto_handler(message: Message):
    # message.text in ('BTC', 'ETH')

    await message.answer(message.text)


# =========== polling ==========

start_polling(dp)
