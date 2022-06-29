#WEB SCRAPING MTG/ALPHA

import pandas as pd
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import csv
import os

from discord import Webhook, RequestsWebhookAdapter

discord_url = '' #discord webhook link
web_url = 'https://www.cardkingdom.com/mtg/alpha'

# Set empty list to store data 
data = []

# The request code
def scraper(url):
    browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    browser.get(url)

    #click on dropdown 100 per page
    browser.find_element(By.XPATH,'//*[@id="main"]/div[4]/form[1]/div/div/select/option[3]').click()
    time.sleep(1)

    #infinite scrolling 
    SCROLL_PAUSE_TIME = 1
    last_height = browser.execute_script("return document.body.scrollHeight")
    while True: 
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = browser.execute_script("return document.body.scrollHeight")
        time.sleep(1)
        if new_height == last_height:
            break
        last_height = new_height

    #loop over each page 
    for i in [3,4,5,6]:
        try:
            page = browser.find_element(By.XPATH,f'//*[@id="main"]/div[6]/nav/ul/li[{i}]/a')
            browser.execute_script("arguments[0].click();",page)
            time.sleep(1)
            soup = BeautifulSoup(browser.page_source, 'html.parser')
            find_newCard(soup)
        except NoSuchElementException:
            continue

    browser.quit()
    savedata = pd.DataFrame(data)
    print(pd.value_counts(savedata.card))
    savedata.to_csv('data2.csv', sep=',', index=False)


# The scrap the new data
def find_newCard(soup):       
    cards = soup.findAll('div',class_="productItemWrapper productCardWrapper")
    for card in cards:
        title = card.find('span',class_="productDetailTitle").text
        ca = card.findAll('li',class_="itemAddToCart")
        for c in ca:
            try:
                cat = c["class"][1]
                qty = c.find('span',class_="styleQty").text
                avail = c.find('span',class_="styleQtyAvailText").text  
                p = c.find('span',class_="stylePrice").text
                
                entry = {'card': title,
                        'categories': cat,
                        'quantity': qty,
                        'status': avail,
                        'price': p,
                        }

                data.append(entry)
                print(entry)

            except AttributeError:
                continue


def DiscordNotify(url,mssg):
    webhook = Webhook.from_url(url, adapter=RequestsWebhookAdapter())
    webhook.send(mssg)

def newcard(old_csv, new_csv, changes_csv):
    with open(old_csv, newline="", encoding="utf8") as old_fp:
        csv_reader = csv.reader(old_fp)
        csv_headings = next(csv_reader)
        old_long_names = {row[0] for row in csv.reader(old_fp)}
    with open(new_csv, newline="", encoding="utf8") as new_fp:

        with open(changes_csv, "w", newline="", encoding="utf8") as changes_fp:
            writer = csv.writer(changes_fp)
            for row in csv.reader(new_fp):

                if row[0] not in old_long_names:
                    writer.writerow(row)
                    if row != ['card', 'categories', 'quantity', 'status', 'price']:
                        message = '|New card: '+str(row[0]) +' |categories: '+ str(row[1]) + ' |quantity: ' +str(row[2]) +' |price: '+ str(row[4])
                        print(message)
                        DiscordNotify(discord_url,message)
                    else:
                        continue

def main():
    scraper(web_url)
    newcard('data1.csv','data2.csv','new.csv')
    os.rename('data2.csv','data1.csv') #rename to data1.csv

if __name__ == '__main__':
    main()
