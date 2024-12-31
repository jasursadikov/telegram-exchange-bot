from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, ContextTypes, InlineQueryHandler
import logging
import os
import requests
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
request_no = 0

EXCHANGE_API_URL = 'https://api.exchangerate-api.com/v4/latest/{}'
TOKEN = os.getenv('TOKEN')


def sync_convert_currency(amount, from_currency, to_currency):
    response = requests.get(EXCHANGE_API_URL.format(from_currency)).json()
    rates = response['rates']
    converted_amount = amount * rates[to_currency]
    return round(converted_amount, 2)


def currency_to_flag(currency_code):
    country_code = currency_code[:2]
    flag = ''.join(chr(127397 + ord(letter)) for letter in country_code)
    return flag


async def convert_currency(amount, from_currency, to_currency):
    loop = asyncio.get_running_loop()
    converted_amount = await loop.run_in_executor(None, sync_convert_currency, amount, from_currency, to_currency)
    return converted_amount


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if len(query.split()) != 3:
        return

    global request_no

    user_id = update.inline_query.from_user.id
    username = update.inline_query.from_user.username

    logger.info(f'[#{request_no}] User ID: {user_id} | Username: @{username} | Query: \"{query}\"')
    request_no += 1

    invalid_query = '\u26d4 Invalid query, try \'@crcvbot 100 USD JPY\''
    amount, from_currency, to_currency = query.split()
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    from_currency_emoji = currency_to_flag(from_currency)
    to_currency_emoji = currency_to_flag(to_currency)

    try:
        amount = float(amount)
        converted_amount = await convert_currency(amount, from_currency, to_currency)
        message = f'{from_currency_emoji} {amount:,.2f} {from_currency} \u27A1 {converted_amount:,.2f} {to_currency} {to_currency_emoji}'
        results = [InlineQueryResultArticle(id='1', title=message, input_message_content=InputTextMessageContent(message))]
        await update.inline_query.answer(results)
    except Exception as e:
        results = [InlineQueryResultArticle(id='2', title=invalid_query, input_message_content=InputTextMessageContent(invalid_query))]
        logger.error(e)
        await update.inline_query.answer(results)

if __name__ == '__main__':
    logger.info('Currency Converter bot started!')
    application = Application.builder().token(TOKEN).build()
    application.add_handler(InlineQueryHandler(inline_query))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info('Bot is terminated!')
