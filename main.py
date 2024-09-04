from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CallbackContext, CommandHandler
from telegram.error import Conflict, TelegramError
import logging
import os
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TOKEN')
CRYPTO_LIST = []


def fetch_crypto_list():
    global CRYPTO_LIST
    url = 'https://api.coingecko.com/api/v3/coins/list'
    response = requests.get(url).json()
    CRYPTO_LIST = [crypto['symbol'].upper() for crypto in response]


def is_crypto(currency_code):
    if not CRYPTO_LIST:
        fetch_crypto_list()
    return currency_code.upper() in CRYPTO_LIST


def get_crypto_rate(from_currency, to_currency):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={from_currency.lower()},{to_currency.lower()}&vs_currencies=usd'
    response = requests.get(url).json()
    return response[from_currency.lower()]['usd'], response[to_currency.lower()]['usd']


def convert_currency(amount, is_crypto, from_currency, to_currency):
    if is_crypto:
        from_rate, to_rate = get_crypto_rate(from_currency, to_currency)
        return round(amount * (from_rate / to_rate), 6)
    else:
        url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
        response = requests.get(url).json()
        rates = response['rates']
        converted_amount = amount * rates[to_currency]
        return round(converted_amount, 2)


def currency_to_emoji(currency_code):
    if is_crypto(currency_code):
        return currency_code
    else:
        country_code = currency_code[:2]
        flag = ''.join(chr(127397 + ord(letter)) for letter in country_code)
        return flag


def inline_query(update: Update, context: CallbackContext) -> None:
    global USERS, REQUESTS_COUNT
    query = update.inline_query.query
    if len(query.split()) != 3:
        return

    user_id = update.inline_query.from_user.id
    username = update.inline_query.from_user.username

    logger.info(f'User ID: {user_id} | Username: @{username} | Query: \"{query}\"')

    amount, from_currency, to_currency = query.split()
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    from_currency_emoji = currency_to_emoji(from_currency)
    to_currency_emoji = currency_to_emoji(to_currency)

    try:
        amount = float(amount)
        crypto = is_crypto(from_currency) or is_crypto(to_currency)
        converted_amount = convert_currency(amount, crypto, from_currency, to_currency)
        message = f'{from_currency_emoji} {amount:,.{2 if crypto else 6}f} {from_currency} \u27A1 {converted_amount:,.{2 if crypto else 6}f} {to_currency} {to_currency_emoji}'
        results = [
            InlineQueryResultArticle(
                id='1',
                title=message,
                input_message_content=InputTextMessageContent(message)
            )
        ]
        update.inline_query.answer(results)
    except Exception as e:
        logger.error(e, exc_info=False)


def main() -> None:
    logger.info('Exchange Currency bot started!')
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(InlineQueryHandler(inline_query))
    dp.add_error_handler(error_callback)
    updater.start_polling()
    updater.idle()
    logger.info('Bot is terminated.')


def error_callback(update, context):
    try:
        raise context.error
    except Conflict as e:
        logger.warning(f'Bot conflict detected: {e}. Ensure only one instance is running.')
    except TelegramError as e:
        logger.error(f'Telegram API error: {e}')
    except Exception as e:
        logger.error(f'Unexpected error: {e}')


if __name__ == '__main__':
    main()
