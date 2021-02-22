import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
from colorama import init
import sys

init(strip=not sys.stdout.isatty())
from termcolor import cprint
from pyfiglet import figlet_format
from re import sub
from decimal import Decimal
from twilio.rest import Client
import config

# -----------------------------------------------------------------------------------------------------------------------
# Twilio API
account_sid = config.account_sid
auth_token = config.auth_token
client = Client(account_sid, auth_token)

# Welcome Banner
text = "NBA TOPShot Price Monitor"
cprint(figlet_format(text, font="standard"), "green")

# Prints description of the script
print("\n\nThis script checks an excel sheet for players and their corresponding prices."
      "\nThen searches NBATopShot to see if the price is lower than the ones from the excel."
      "\nIf the prices are lower then it will send a text and update the excel sheet!\n")

time.sleep(18)

# Chrome options if wanted to use it headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=192,1080")
chrome_options.add_argument("--start-maximized")

# Defines where the driver path is
driver_path = r"C:\Users\\Downloads\chromedriver_win32\chromedriver.exe"

# The first option is for headless the second option will display the browser

# browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=driver_path)
browser = webdriver.Chrome(executable_path=driver_path)

# To have a divider when providing output to screen
divider = "-----------------------------------------------------------------------------------------"
# To track how many times the script has checked prices
iteration = 0

site_maint = 0

# The beginning of the while loop to constantly check prices and update the excel sheet
while True:

    # Tracking how many iterations and printing it out
    iteration += 1
    print("\nIteration: " + str(iteration))

    # The three lines below define where the excel file and what to read from the excel file
    file_name = r'C:\Users\\Downloads\NBATopShot_V2\NBATopShot\input.xlsx'
    sheet = 'Input'
    sheet2 = 'Output'
    select_columns = 'A:D'

    # This reads the excel file into a dataframe to use the data in the code and prints out what the script is checking for
    df = pd.read_excel(io=file_name, sheet_name=sheet, usecols=select_columns)
    print("\nThe list of links and players it's checking for:\n")
    print(df)

    # This reads the second output sheet to make sure we don't overwrite the data when making updates
    trigger_df = pd.read_excel(io=file_name, sheet_name=sheet2, usecols=select_columns)

    # creates a list of items from the columns on the excel sheet
    links = df['Links'].tolist()
    prices = df['Prices'].tolist()
    players = df['Players'].tolist()

    # converting the prices from the excel from string to floats to be able to compare prices
    [float(i) for i in prices]

    # an empty list to store the prices of the moments from the website
    current_price_list = []

    # This for loop iterates through the list of links and pulls the price from each moment
    # it then converts those prices to decimal and appends it to the list above
    for i in range(len(links)):
        while True:
            try:
                browser.get(links[i])
                # Printing out the link it's pulling the price for so if the script breaks you can know which link isn't
                # working to remove from the excel sheet
                print("\n\nGetting the current price for: " + str(links[i]))
                # give the browser time to load the page before searching for the price
                time.sleep(2)
                # If the website makes any changes on how it displays data the line below might not work to pull the price
                # Also if the page does not load in time or if the site isn't responding it won't be able to  pull the price
                # If you see the page loaded but it didn't pull the price that means you need to increase the sleep time above
                span_element = browser.find_element_by_xpath(
                    "/html/body/div[1]/div/main/div[3]/div/div[3]/div/div[2]/div[1]/div[1]/span")
                current_price = span_element.text
                break
            except:
                site_maint += 1
                if site_maint == 1:
                    message = ("The site seems to be under maintenance. Will keep trying to load the site.")
                    txt_message = client.messages \
                        .create(
                        body=message,
                        from_=config.tw_cell,
                        to=config.per_cell
                    )
                    print(txt_message.sid)
                    continue
                else:
                    continue
                break

        current_price = Decimal(sub(r'[^\d.]', '', current_price))
        current_price_list.append(current_price)

    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet('Input')
    writer.sheets['Input'] = worksheet
    worksheet2 = workbook.add_worksheet('Output')
    writer.sheets['Output'] = worksheet2

    # This for loop compares the prices from the website to the ones on the excel sheet.
    for i in range(len(current_price_list)):
        if current_price_list[i] < prices[i]:
            print("\n\nThe price for: " + str(players[i]) + " is lower.")
            trigger_df = trigger_df.append(
                [{'Players': str(players[i]), 'Links': str(links[i]), 'Prices': str(prices[i])}], ignore_index=True)
            df = df[df.Links != links[i]]
            message = ("The current price for " + str(players[i]) + " has been triggered at: " + str(current_price_list[
                                                                                                         i]) + ". Here's the link to make the purchase if you would like to make a purchase: " + str(
                links[i]))
            txt_message = client.messages \
                .create(
                body=message,
                from_=config.tw_cell,
                to=config.per_cell
            )
            print(txt_message.sid)

        else:
            print("\nThe current price for " + str(players[i]) + " is higher than the check from the input.xlsx\n")

    print(divider)

    # Updating both excel sheet
    trigger_df.to_excel(writer, sheet_name='Output', startrow=0, startcol=0, index=False)
    df.to_excel(writer, sheet_name='Input', startrow=0, startcol=0, index=False)
    worksheet.set_column(0, 0, 15)
    worksheet.set_column(1, 1, 50)
    worksheet2.set_column(0, 0, 15)
    worksheet2.set_column(1, 1, 50)
    writer.save()

    # The time between each iteration
    time.sleep(21)