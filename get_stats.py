from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup as bsoup
from datetime import datetime
from time import sleep
import re
import os.path
import weekly_stats


def retrieve():
    # Functionality to archive old stats
    now = datetime.now()

    # Ensure date format for filename: "2018-07-14"
    if now.month < 10:
        month = "0{}".format(now.month)
    else:
        month = str(now.month)
    if now.day < 10:
        day = "0{}".format(now.day)
    else:
        day = str(now.day)

    # Create Archive folder (if first time running)
    current_dir = os.getcwd()
    archive_dir = os.path.join(current_dir, 'Archive')
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    # Sample filename to check if data was already gathered on the current day
    filename = "Archive/{}-{}-{}_Month_All.csv".format(now.year, month, day)
    fileprefix = "Archive/{}-{}-{}_".format(now.year, month, day)

    # If it's the first run of the day on a Tuesday, post weekly breakdown
    if not os.path.isfile(filename) and datetime.now().weekday() == 1:
        weekly_stats.weekly_post()

    # Get filtered table data (requires click due to javascript)
    # Create a headless Firefox session
    options = Options()
    options.add_argument("--headless")
    print("Opening browser...")
    driver = webdriver.Firefox(firefox_options=options)
    driver.implicitly_wait(10)  # wait 10 seconds to open
    driver.get("https://www.overbuff.com/heroes")

    # Add "Last 3 Months" and "Last 6 Months" if wanted
    time_period = ["Month", "Week"]
    rank_list = ["Grandmaster", "Master", "Diamond", "Platinum", "Gold",
                 "Silver", "Bronze"]

    # Obtain all Statistical Data
    for time in time_period:
        # If want to get "Last 3 Months" and "Last 6 Months" data
        if len(time.split()) > 1:
            timer = time
        else:
            timer = "This {}".format(time)

        # Get "All" rank data for each time period
        all_button = driver.find_element_by_xpath("(//div[.='All'])[2]")
        all_button.click()
        sleep(0.2)
        time_button = driver.find_element_by_xpath("//*[contains(text(), '{}')]".format(timer))
        time_button.click()
        sleep(0.2)
        soup = bsoup(driver.page_source, 'html.parser')
        scrape_table(fileprefix+"{}_All.csv".format(time), soup)

        for rank in rank_list:
            print("\n"+time+" "+rank)
            button = driver.find_element_by_xpath("//span[contains(., '{}')]/parent::div"
                                                  "[contains(@class, 'filter-option')]".format(rank))
            button.click()
            sleep(0.2)
            soup = bsoup(driver.page_source, 'html.parser')
            scrape_table(fileprefix+"{}_{}.csv".format(time, rank), soup)


def scrape_table(filename, soup):
    # Get "Hero Stats" table data
    # All stats are in rows of the only <tbody> tag on the page
    t_body = soup.find_all("tbody")
    # Only one <tbody>, but index 0 must still be specified
    t_rows = t_body[0].find_all("tr")
    hero_number = len(t_rows)
    # Uncomment to check if number of heroes is correct:
    # hero_num_output = "There are {} heroes!\n".format(hero_number)
    # print(hero_num_output)

    f = open(filename, "w")
    headers = "Hero, Role, Pick Rate, Win Rate, Tie Rate, On Fire\n"
    f.write(headers)

    # Get data row by row
    for hero in range(0, hero_number):
        hero_data = t_rows[hero].find_all("span")
        # First span holds "NameRole" (returns one string: "ReinhardtTank")
        hero_data[0].text
        # Use regex to separate name and role, then store in hero_results list
        # McCree and D.Va need special treatment
        if len(re.findall('McCree*', hero_data[0].text)) > 0:
            hero_results = ['McCree', 'Damage']
        elif len(re.findall('D.Va*', hero_data[0].text)) > 0:
            hero_results = ['D.Va', 'Tank']
        elif len(re.findall('Wrecking*', hero_data[0].text)) > 0:
            hero_results = ['Wrecking Ball', 'Tank']
        else:
            hero_results = [i.strip(' \'') for i in
                            re.findall('[A-Z][^A-Z]*', hero_data[0].text)]
        # Next 4 spans hold Pick Rate, Win Rate, Tie Rate, and On Fire
        hero_results.append(hero_data[1].text)
        hero_results.append(hero_data[2].text)
        hero_results.append(hero_data[3].text)
        hero_results.append(hero_data[4].text)

        # Write results to file
        for x in range(0, len(hero_results)):
            if x == len(hero_results)-1:
                f.write(hero_results[x]+"\n")
            else:
                f.write(hero_results[x]+',')

    # print(hero_results)
    f.close()


if __name__ == '__main__':
    retrieve()
