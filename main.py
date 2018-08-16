#!/usr/bin/python3

import csv
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import *


def init():

    did_something = False
    files = os.listdir(DATA_DIR)

    tables = get_data()
    for table in tables:

        fname = table['slug'] + '.csv'
        if fname in files:
            continue

        did_something = True
        print("creating %s..." % fname)
        dst = os.path.join(DATA_DIR, fname)
        with open(dst, 'w') as fd:

            fieldnames = [row[0] for row in table['rows']]

            csvwriter = csv.DictWriter(fd, fieldnames=fieldnames)
            csvwriter.writeheader()

    return did_something


def get_data():
    tables = fetch_tables()
    parsed = [parse_table(t) for t in tables]
    return parsed


def fetch_tables():
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/chromium'
    options.add_argument('headless')

    driver = webdriver.Chrome(chrome_options=options)
    driver.get(URL)

    table = WebDriverWait(driver,
            20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    tables = driver.find_elements_by_class_name("table2")
    tables = [t.get_attribute('innerHTML') for t in tables]

    return tables


def parse_table(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    title = soup.table.th.string
    slug = slugify(title)
    rows = []
    for row in soup.table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) == 0:
            continue
        key, val = (c.string.strip() for c in cells)
        if key == '' or val == '':
            continue
        row = (key, val)
        rows.append(row)
    table = {"title": title, "rows": rows, "slug": slug}
    return table


def new_data(tables):
    table_with_time = None
    for t in tables:
        if 'navigation' in t['slug']:
            table_with_time = t
            break

    time = table_with_time['rows'][1][1]
    time = time.strip()

    fname = table_with_time['slug'] + '.csv'
    fname = os.path.join(DATA_DIR, fname)
    with open(fname, 'r') as fd:
        csv_data = csv.DictReader(fd)
        last_line = list(csv_data)[-1]
        previous_time = last_line['Time (UTC)']
        previous_time = previous_time.strip()

    return previous_time != time


def append_data(table):

    fname = table['slug'] + '.csv'

    fieldnames = [row[0] for row in table['rows']]
    data_dict = {}
    for row in table['rows']:
        data_dict[row[0]] = row[1]

    dst = os.path.join(DATA_DIR, fname)
    with open(dst, 'a') as fd:
        csvwriter = csv.DictWriter(fd, fieldnames=fieldnames)
        csvwriter.writerow(data_dict)


def slugify(not_slug):
    slug = not_slug.lower()
    slug = slug.split('(')[0]
    slug = slug.strip()
    slug = slug.replace(' ', '_')
    return slug


def main():
    first_run = init()
    tables = get_data()

    if not first_run:
        if not new_data(tables):
            return

    for table in tables:
        append_data(table)


if __name__ == '__main__':
    main()
