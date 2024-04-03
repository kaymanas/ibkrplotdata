#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 14:20:44 2024
"""


import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import ScalarFormatter
# for better annotations
import textalloc as ta
from adjustText import adjust_text
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import dates
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from pandas.plotting import register_matplotlib_converters
from collections import Counter
import time
import math
import random
register_matplotlib_converters()
#IMPORT DIRECTLY FROM YAHOO
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import dateutil.parser as dt


# Some setup and options:

# The name of the document should be sheet_1, sheet_2 etc. 
# Count up to the number of sheets here, should make a filter to automate this...
sheets = ["1","2","3","4","5"]

# Screen printing options
print_stock_sheets = 0
fetch_yahoo_data = 1
print_yahoo_hist = 0

# set the start and end date if needed for the plots
use_explicit_start = 1
explicit_start = '2020-1-1'

use_explicit_end = 0
explicit_end = '2024-3-1'

# output options
plotCurrentPortfolioOnly = 0

# where to save pdf of graphs, path is relative to this file location
pdffile = 'ibkrdata/results.pdf'



#################################################################################
# IMPORT IBKR SHEETS AND SORT DATA
#################################################################################



# read in IBKR csv files
data = {}

for sheet in sheets:
	data[sheet] = pd.read_csv("ibkrdata/sheet_{}.csv".format(sheet),header=6)#None, skiprows=6)
	data[sheet] = data[sheet][['Symbol','Quantity','Date/Time','T. Price', 'Currency', 'Realized P/L', 'Basis']]
	data[sheet] = data[sheet].drop(data[sheet][data[sheet]['Symbol'] == 'Symbol'].index)
	data[sheet].dropna(inplace = True)
	#print(data[sheet])
	
	
# remove the time from the date column
	data[sheet]["Date/Time"] = pd.to_datetime(data[sheet]["Date/Time"]).dt.date
	#print(data[sheet])

# convert Quantity and T. Price to floats from string
	data[sheet]['Quantity'] = data[sheet]['Quantity'].replace(',', '', regex=True)
	data[sheet]['Quantity'] = pd.to_numeric(data[sheet]['Quantity'])
	data[sheet]['T. Price'] = data[sheet]['T. Price'].replace(',', '', regex=True)
	data[sheet]['T. Price'] = pd.to_numeric(data[sheet]['T. Price'])
	data[sheet]['Realized P/L'] = data[sheet]['Realized P/L'].replace(',', '', regex=True)
	data[sheet]['Realized P/L'] = pd.to_numeric(data[sheet]['Realized P/L'])
	data[sheet]['Basis'] = data[sheet]['Basis'].replace(',', '', regex=True)
	data[sheet]['Basis'] = pd.to_numeric(data[sheet]['Basis'])


# merge all the sheets into one
data_array = []

for sheet in sheets:
	data_array.append(data[sheet])
	 
all_data = pd.concat(data_array)
#print(all_data)


# seperate the USD and CAD stocks
all_stocks = {}

all_stocks['CAD'] = all_data[all_data['Currency'] == 'CAD']
all_stocks['USD'] = all_data[all_data['Currency'] == 'USD']



	
# merge the same dates into one line (add quantity)
	
aggregation_functions = {'Date/Time': 'first', 'Quantity': 'sum', 'T. Price': 'first', 'Realized P/L': 'sum', 'Basis': 'sum'}

stocks = {}
for currency in all_stocks:

	#data_single = all_data.groupby(all_data['Symbol']).aggregate(aggregation_functions)
	data_single = all_stocks[currency].groupby(all_stocks[currency]['Symbol']).aggregate(aggregation_functions)
	data_single = data_single.reset_index()

# pass the symbols into a list of the symbols
	stocks_np = data_single[['Symbol']].to_numpy() 
	stocks[currency] = stocks_np.tolist()

# make separate dataframes for each stock
stocks_by_currency = {}
stock_sheets = {}
realizedpl = {}
currentQuantity = {}
costBasis = {}

for currency in stocks:
	for stock in stocks[currency]:
		
		this_stock = stock[0]
		this_stock_currency = this_stock + ' - {}'.format(currency)
		stock_sheets[this_stock_currency] = all_stocks[currency][all_stocks[currency]['Symbol'] == this_stock]
		
		# merge same dates together
		aggregation_functions = {'Symbol': 'first', 'Quantity': 'sum', 'T. Price': 'first', 'Realized P/L': 'sum', 'Basis': 'sum'}
		stock_sheets[this_stock_currency] = stock_sheets[this_stock_currency].groupby(stock_sheets[this_stock_currency]['Date/Time']).aggregate(aggregation_functions)
		
		aggregation_functions = {'Quantity': 'sum', 'T. Price': 'first', 'Realized P/L': 'sum', 'Basis': 'sum'}
		temp_sheet = stock_sheets[this_stock_currency].groupby(stock_sheets[this_stock_currency]['Symbol']).aggregate(aggregation_functions)
		realizedpl[this_stock_currency] = '${:.2f}'.format(temp_sheet['Realized P/L'].iloc[0])
		currentQuantity[this_stock_currency] = temp_sheet['Quantity'].iloc[0]
		costBasis[this_stock_currency] = temp_sheet['Basis'].iloc[0]
		
		if print_stock_sheets:
			print(stock_sheets[this_stock])
	

#################################################################################
# GET STOCK PRICE HISTORY FROM YAHOO FINANCE
#################################################################################

# clean up the stored name of each stock so it can be read later
stocklist = []

if fetch_yahoo_data:
	
	s = requests.Session()
	retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
	s.mount('https://', HTTPAdapter(max_retries=retries))
	
	print("Archived YAHOO price history for:")
	for currency in stocks:
		
		for stock in stocks[currency]:
			
			this_stock = stock[0]
				
			date1 = datetime.datetime.strptime('{} 00:00:00'.format(datetime.date.today()), '%Y-%m-%d %H:%M:%S')
			temp = datetime.datetime(1970, 1, 1)
			delta = date1 - temp
			t1 = (delta.days+1)* 86400 #convert days to seconds since 1/1/1970 (unix timestamp)
			#using +1 as yahoo keeps giving me a day old result... this keeps it up to date
			
		
			this_stock_old = this_stock
			this_stock = this_stock.replace('.','-')
			first_pass = this_stock
			if(currency=='CAD'):
				this_stock = this_stock + '.TO'
		
			
			headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'} # This is chrome, you can set whatever browser you like

			
			url_history = 'https://query1.finance.yahoo.com/v7/finance/download/{}?period1=570326400&period2={}&interval=1d&events=history'.format(this_stock,t1)
			r_history = s.get(url_history,headers=headers)
		
			error1 = '404 Not Found: No data found, symbol may be delisted'
			error2 = '404 Not Found: Timestamp data missing.'
			if r_history.text == error1 or r_history.text==error2:
				this_stock = first_pass + '.NE'
				url_history = 'https://query1.finance.yahoo.com/v7/finance/download/{}?period1=570326400&period2={}&interval=1d&events=history'.format(this_stock,t1)
				r_history = s.get(url_history,headers=headers)
				if r_history.text == error1 or r_history.text== error2:
					this_stock = first_pass + '.TO'
					url_history = 'https://query1.finance.yahoo.com/v7/finance/download/{}?period1=570326400&period2={}&interval=1d&events=history'.format(this_stock,t1)
					r_history = s.get(url_history,headers=headers)
					if r_history.text == error1 or r_history.text== error2:	
						print("cannot find {}".format(this_stock_old))
						continue
			
	
			stocklist.append('{} - {}'.format(this_stock_old,currency))
			
			fname = 'ibkrdata/data_daily_{}.csv'.format('{} - {}'.format(this_stock_old,currency))
			f = open(fname, 'wb')
			f.write(r_history.content)
			f.close()
			print("-> {}".format(this_stock))
			s.close()
		

#################################################################################
# READ IN YAHOO FINANCE DATA AND CONVERT TO DATAFRAME
#################################################################################

data_daily = {}

# column headings can be changed here, these are for the YAHOO finance csv
adjust_column = 'Close' #'Adj Close'
date_column = 'Date'
high_column = 'High'
low_column = 'Low'


for stock in stocklist:

	data_daily[stock] = pd.read_csv('ibkrdata/data_daily_{}.csv'.format(stock))
	data_daily[stock]['datetime'] = pd.to_datetime(data_daily[stock][date_column])
	data_daily[stock] = data_daily[stock].set_index('datetime')
	data_daily[stock].drop([date_column], axis=1, inplace=True)
	data_daily[stock].dropna(inplace = True)
	data_daily[stock].sort_values(by=['datetime'],ascending=True,inplace=True)
	
	if use_explicit_start:
		data_daily[stock] = data_daily[stock].truncate(before=pd.Timestamp(explicit_start))

	if use_explicit_end:
		data_daily[stock] = data_daily[stock].truncate(after=pd.Timestamp(explicit_end))
		
	if print_yahoo_hist:
		print("Printing read in data: {}".format(stock))
		print(data_daily[stock])




##################################################################################################
#### PLOT DATA
##################################################################################################


print('Begin publishing pdf')


pp = PdfPages(pdffile)

for stock in stocklist:
	

	fig, ax = plt.subplots(figsize=(18, 8))
	
	line2, = ax.plot(data_daily[stock][adjust_column],label="{} stock price".format(stock), alpha = 0.8, linewidth=0.35)

	stock_sheets[stock] = stock_sheets[stock].reset_index()
	
	# realized profit/loss:
	ax.text(0.2,0.94,'Realized P/L: {}'.format(realizedpl[stock]), transform=ax.transAxes, fontsize=13, style='italic')
	
	# unrealized profit/loss:
	if currentQuantity[stock]>0:
		price = data_daily[stock][adjust_column].iloc[-1]
		unrealizedpl = currentQuantity[stock] * price - costBasis[stock]
		ax.text(0.2,0.88,'Unrealized P/L: ${:.2f}'.format(unrealizedpl), transform=ax.transAxes, fontsize=13, style='italic')
		
		
	def plot(**kwargs):

		purchases = stock_sheets[stock][stock_sheets[stock]['Quantity'] > 0]
		sales = stock_sheets[stock][stock_sheets[stock]['Quantity'] < 0]
		#print(purchases)
		
		xs, ys = (stock_sheets[stock]['Date/Time'], stock_sheets[stock]['T. Price'])
		xs1, ys1 = (purchases['Date/Time'], purchases['T. Price'])
		xs2, ys2 = (sales['Date/Time'], sales['T. Price'])
		
		ax.scatter(xs1, ys1, c='green', edgecolor=(1,1,1,0), label='buy', s=15)
		ax.scatter(xs2, ys2, c='red', edgecolor=(1,1,1,0), label='sell', s=15)
		
		texts = []
		for x, y, l in zip(xs, ys, stock_sheets[stock]['Quantity']):
			texts.append(plt.text(x, y, l, size=10, style='oblique'))
			
		adjust_text(texts, arrowprops=dict(arrowstyle='simple, head_width=0.25, tail_width=0.05', color='k', lw=0.5, alpha=.5), **kwargs, expand=[2.3,2.3])
			
		
	plot()
	

	
	
	fig.autofmt_xdate()
	fig.set_dpi(130)
	fig.set_size_inches(18, 8)
	
	locator = dates.AutoDateLocator(minticks=20, maxticks=40)
	formatter = dates.ConciseDateFormatter(locator)
	ax.xaxis.set_major_locator(locator)
	ax.xaxis.set_major_formatter(formatter)
	
	
	ax.set_title("{}$".format(stock), fontsize=21)
	ax.set_ylabel(r'Stock Price ($)', fontsize=18)
	ax.grid(True,which='minor',linewidth=0.05)
	ax.grid(True,which='major',linewidth=0.22)
	ax.legend(loc='upper left')
	
	if plotCurrentPortfolioOnly:
		if currentQuantity[stock]==0:
			plt.close()
			continue
		
	pp.savefig(fig)
	
	plt.close()
		

pp.close()

print('{} saved...'.format(pdffile))

