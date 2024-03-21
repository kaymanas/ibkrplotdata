A python script to generate a pdf of plots for your stocks on Interactive Brokers. The stock price history along with buys and sells will be shown with green and red dots respectively,
as well as the number of shares purchased or sold. 

To create the correct data for import, create a custom statement using only the "Trades" option on Interactive Brokers. 
Output these yearly (as that is the maximum allowed). 

For simplicity I have hardcoded the script to import files named "Sheet_#" where # is the number of the sheet, ie 1,2,3 etc. 
Please follow this notation for as many statements as you wish to include.

Output is a pdf document with the plots for each stock you have held in your portfolio. 

Some options are shown at the top of the file after the imports. 

It uses Yahoo Finance to generate the stock price history, hence you may need to adjust the syntax manipulation as these have only been tested
on a limited number of NYSE and TSX stocks. 
