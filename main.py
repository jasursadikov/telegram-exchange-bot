from datetime import datetime

import os
import requests
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, ContextTypes, InlineQueryHandler

request_no = 0

EXCHANGE_API_URL = 'https://api.exchangerate-api.com/v4/latest/{}'
TOKEN = os.getenv('TOKEN')


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	global request_no

	query = update.inline_query.query
	user_id = update.inline_query.from_user.id
	username = update.inline_query.from_user.username

	log(f'[#{request_no}] User ID: {user_id} | Username: @{username} | Query: \"{query}\"')
	request_no += 1

	try:
		if len(query.split()) != 3:
			raise IndexError("Query is too short")
		
		invalid_query = '\u26d4 Invalid query, try \'@crcvbot 100 USD JPY\''
		amount, from_currency, to_currency = query.split()
		from_currency = from_currency.upper()
		to_currency = to_currency.upper()
		from_currency_emoji = currency_to_flag(from_currency)
		to_currency_emoji = currency_to_flag(to_currency)

		amount = float(amount)
		response = requests.get(EXCHANGE_API_URL.format(from_currency)).json()
		rates = response['rates']
		converted_amount = round(amount * rates[to_currency], 2)
		message = f'{from_currency_emoji} {amount:,.2f} {from_currency} \u27A1 {converted_amount:,.2f} {to_currency} {to_currency_emoji}'
		results = [InlineQueryResultArticle(id='1', title=message, input_message_content=InputTextMessageContent(message))]
		await update.inline_query.answer(results)
	except Exception as e:
		results = [InlineQueryResultArticle(id='2', title=invalid_query, input_message_content=InputTextMessageContent(invalid_query))]
		await update.inline_query.answer(results)


def currency_to_flag(currency_code):
	country_code = currency_code[:2]
	flag = ''.join(chr(127397 + ord(letter)) for letter in country_code)
	return flag


def log(str: str) -> None:
	now = datetime.now()
	print(now, " ", str)


if __name__ == '__main__':
	log('Currency Converter bot started!')
	application = Application.builder().token(TOKEN).build()
	application.add_handler(InlineQueryHandler(inline_query))
	application.run_polling(allowed_updates=Update.ALL_TYPES)
	log('Bot is terminated!')
