from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler

import os
import requests

TOKEN = os.getenv('TOKEN')
USERS = []
REQUESTS_COUNT = 0


def convert_currency(amount, from_currency, to_currency):
    url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
    response = requests.get(url).json()
    rates = response['rates']
    converted_amount = amount * rates[to_currency]
    return round(converted_amount, 2)


def inline_query(update, context):
    global USERS
    global REQUESTS_COUNT

    query = update.inline_query.query
    if len(query.split()) != 3:
        return

    user_id = update.inline_query.from_user.id
    username = update.inline_query.from_user.username

    if user_id not in USERS:
        USERS.append(user_id)
    REQUESTS_COUNT += 1

    print(f'::debug ::User ID: {user_id} [request] Username: @{username} | Query: \"{query}\" | [stats] Request:{REQUESTS_COUNT} Total Users:{len(USERS)}')

    amount, from_currency, to_currency = query.split()
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    from_currency_emoji = currency_to_flag(from_currency)
    to_currency_emoji = currency_to_flag(to_currency)

    try:
        amount = float(amount)
        converted_amount = convert_currency(amount, from_currency, to_currency)
        message = f'{from_currency_emoji} {amount:,.2f} {from_currency} \u27A1 {converted_amount:,.2f} {to_currency} {to_currency_emoji}'
        results = [
            InlineQueryResultArticle(
                id='1',
                title=message,
                input_message_content=InputTextMessageContent(message)
            )
        ]
        update.inline_query.answer(results)
    except Exception as e:
        print(e)


def currency_to_flag(currency_code):
    country_code = currency_code[:2]
    flag = ''.join(chr(127397 + ord(letter)) for letter in country_code)
    return flag


def main():
    print('::debug ::Exchange Currency bot started!')
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(InlineQueryHandler(inline_query))
    updater.start_polling()
    updater.idle()
    print('::debug ::Bot is terminated T^T')


if __name__ == '__main__':
    main()
