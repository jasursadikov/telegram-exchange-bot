from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CallbackContext, CommandHandler
import logging
import os
import requests

# Set up basic logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TOKEN')
USERS = []
REQUESTS_COUNT = 0

def convert_currency(amount, from_currency, to_currency):
	url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
	response = requests.get(url).json()
	rates = response['rates']
	converted_amount = amount * rates[to_currency]
	return round(converted_amount, 2)

def currency_to_flag(currency_code):
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

	if user_id not in USERS:
		USERS.append(user_id)
	REQUESTS_COUNT += 1

	logger.info(f'User ID: {user_id} | Username: @{username} | Query: \"{query}\" | Request:{REQUESTS_COUNT} | Total Users:{len(USERS)}')

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
		logger.error(e)

def main() -> None:
	logger.info('Exchange Currency bot started!')
	updater = Updater(TOKEN)
	dp = updater.dispatcher
	dp.add_handler(InlineQueryHandler(inline_query))
	updater.start_polling()
	updater.idle()
	logger.info('Bot is terminated.')

if __name__ == '__main__':
	main()