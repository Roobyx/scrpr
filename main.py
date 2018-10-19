from bs4 import BeautifulSoup as soup
# import urllib.request as uReq
import urllib.request
# from urllib.request import urlopen as urllib.request.urlopen
import codecs
import time
from datetime import date
import sqlite3
import os
import msvcrt as m
import webbrowser
import random

# print('Started at: ' + str(time.clock()))

current_date = str(date.today())
db_category_index = 0
db_category = ('laptops', 'tv')
url_category = ('laptopi', 'televizori')

# db_category = ('laptops')
db_category = ('laptops', 'tv')
# url_category = ('laptopi')
url_category = ('laptopi', 'televizori')
# Used to start scraping not from 0:
start_page = 0
db_connection = sqlite3.connect('./scrapped/db/emag_products.db')
db_cursor = db_connection.cursor()


def wait():
	m.getch()


for cat in url_category:
	startUrl = 'https://www.emag.bg/' + cat + '/c'
	current_page = 1

	db_cursor.execute('CREATE TABLE IF NOT EXISTS parent_dates (id integer PRIMARY KEY, name text);')

	date_query = ('INSERT OR IGNORE INTO parent_dates VALUES (NULL, \'' + current_date + '\');')
	# print(date_query)

	db_cursor.execute(date_query)
	db_connection.commit()

	db_cursor.execute(
		'CREATE TABLE IF NOT EXISTS {0} ('
		'id integer PRIMARY KEY, '
		'parent_id text,'
		'name text, '
		'today_price text, '
		'old_price text, '
		'claimed_deal text, '
		'limited integer, '
		'thumbnailUrl text);'.format(
			db_category[db_category_index]))

	def get_page_count(page_url):
		try:
			u_req_client = urllib.request.urlopen(page_url)
			pages_raw_html = u_req_client.read()
			u_req_client.close()
		except urllib.request.error.HTTPError:
			# if err.code == 511:
			print('Check browser for captcha')
			webbrowser.open_new(page_url)
			wait()
			u_client = urllib.request.urlopen(page_url)
			# else:
			# 	raise

		pages_soup = soup(pages_raw_html, 'html.parser')
		products_count = pages_soup.find('h1', {'class': 'listing-page-title'}).find('span', {'class': 'title-phrasing-sm'}).text.split(' ')[0]

		pages_count = int(products_count) / 60

		if isinstance(pages_count, float):
			pages_count = int(pages_count) + 1

		print(str(pages_count) + ' pages to scrape')
		return pages_count


	def strip_all(target):
		return target.replace('.', '').replace('\n', '').replace('(', '').replace(')', '').replace('-', '').replace('%', '').replace(' ', '').replace('%', '')


	def extract_price(tag):
		if tag is not None:
			if len(tag.contents) > 1:
				if tag.findAll('span', {'class': 'font-size-sm'}):
					main = strip_all(tag.contents[1])
					change = tag.contents[2].text
					symbol = tag.contents[4].text
					return main, change, symbol
				else:
					main = strip_all(tag.contents[0])
					change = tag.contents[1].text
					symbol = tag.contents[3].text
					return main, change, symbol

			else:
				main = strip_all(tag.contents[0])
				return main, '%'
		else:
			return '', ''


	def scrape(url_to_scrape, fname):
		f = codecs.open(fname, "w", 'utf-8')

		# Get html
		try:
			u_client = urllib.request.urlopen(url_to_scrape)
		# except uReq.error.HTTPError as err:
		except urllib.request.error.HTTPError:
		# except Exception, e:
			# if err.code == 511:
			print('Check browser for captcha')
			webbrowser.open_new(url_to_scrape)
			wait()
			u_client = urllib.request.urlopen(url_to_scrape)
			# else:
			# 	raise

		raw_html = u_client.read()
		u_client.close()

		# Parse to html
		page_soup = soup(raw_html, "html.parser")

		# Find product item
		containers = page_soup.findAll("div", {"class": "card-section-wrapper"})

		for container in containers:
			product_name = container.findAll("a", {"class": "product-title"})[0].text.replace('\n', ' ').replace('\r', '').replace(',', '').replace('\'', '"')

			# Get claimed old price
			if container.find("div", {"class": "card-section-btm"}).find('p', {'class': 'product-old-price'}):
				op_container = container.find("div", {"class": "card-section-btm"}).find('p', {
					'class': 'product-old-price'}).find('s')
				op_deal_container = container.find("div", {"class": "card-section-btm"}).find('p', {
					'class': 'product-old-price'}).find('span', {'class': 'product-this-deal'})

				product_old_price_list = extract_price(op_container)
				product_old_price = product_old_price_list[0] + '.' + product_old_price_list[1]

				claimed_deal_list = extract_price(op_deal_container)
				claimed_deal = claimed_deal_list[0] + '.' + claimed_deal_list[1]

				if product_old_price is '.':
					product_old_price = '0'

				if claimed_deal is '.':
					claimed_deal = '0'

				if claimed_deal[-1] is '%':
					claimed_deal = claimed_deal.replace('.', '')

			else:
				product_old_price = '0'
				claimed_deal = '0'

			# Get current price
			np_container = container.find("div", {"class": "card-section-btm"}).find("p", {"class": "product-new-price"})
			product_price_list = extract_price(np_container)
			product_price = product_price_list[0] + '.' + product_price_list[1]

			# Get qty
			if container.find("div", {"class": "label-limited_stock_qty"}):
				limited = '1'
			else:
				limited = '0'

			# Get img url
			# product_image = container.find('div', {'class': 'thumbnail'}).find('img')['src']
			# print(container.find('div', {'class': 'thumbnail'}).find('img'))

			if container.find('div', {'class': 'thumbnail'}).find('img') is None:
				product_image = str(container.find('div', {'class': 'thumbnail'}).find('div', {'class', 'bundle-image'})['style'].replace('\n', ' ').replace('\r', '').replace(' ', '').replace('url(', '').replace(')', '').replace('background-image:', '').replace(',', ' / ').replace(';', ''))
			else:
				product_image = str(container.find('div', {'class': 'thumbnail'}).find('img')['src'])

			# DB
			# ---------------------------------
			query = 'INSERT INTO ' + db_category[db_category_index] + ' VALUES (NULL, \'' + current_date + '\',\'' + product_name + '\',' + product_price + ',' + product_old_price + ',\'' + claimed_deal + '\',' + limited + ',\'' + product_image + '\');'
			# print(query)

			db_cursor.execute(query)
			db_connection.commit()
			# ---------------------------------

			f.write(
				product_name + ' | ' + product_price + ' | ' + product_old_price + ' | ' + claimed_deal + ' | ' + limited + ' | ' + product_image + ' | ' + current_date + '\n')

		f.close()
		print("Done")


	today_dir = './scrapped/files/' + db_category[db_category_index] + '/scraped_' + str(date.today())

	if not os.path.exists(today_dir):
		os.makedirs(today_dir)

	print('SCRAPING CATEGORY: ' + cat)
	for page in range(start_page, get_page_count(startUrl)):
	# for page in range(start_page, 1):
		url = 'https://www.emag.bg/laptopi/p' + str(current_page) + '/c'
		filename = today_dir + '/' + db_category[db_category_index] + '_' + str(current_page) + '.txt'

		print('Scraping page: ' + str(current_page))
		scrape(url, filename)
		current_page += 1
		wait_time = random.randint(10, 30)
		print('Waiting ' + str(wait_time) + 's for next page')
		time.sleep(wait_time)

db_connection.close()
# print('Ended at: ' + str(time.clock()))
