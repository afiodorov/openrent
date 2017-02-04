#!/usr/bin/python3

import argparse
import urllib.request
import urllib.error
from bs4 import BeautifulSoup
from collections import OrderedDict
import os
import json
import dateparser


def preprocess(soup):
    ticks = soup.find_all("i", attrs={'class': 'icon-ok'})
    for tick in ticks:
        if tick.text == "":
            tick.string = "yes"

    ticks = soup.find_all("i", attrs={'class': 'icon-remove'})
    for tick in ticks:
        if tick.text == "":
            tick.string = "no"


def property_filepath(property_id):
    outdir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "properties")
    return os.path.join(outdir, property_id)


def parse_location_table(soup):
    data = []
    table = soup.find('div', attrs={'id': 'LocalTransport'})
    if table:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols if ele])

    return data


def get_title(soup):
    return soup.find("h1", attrs={'class': "propertyTitle"}).text.strip()


def parse_feature_table(soup):
    data = []
    tables = soup.find('div', attrs={'id': 'Features'}).find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols if ele])
    return data


def available_from(features):
    date_text = [x[1] for x in features if x[0] == "Available From"][0]
    parsed = dateparser.parse(date_text)
    if not parsed:
        return date_text
    return str(parsed.date())


def EPC_rating(features):
    rating = [x[1] for x in features if x[0] == "EPC Rating"]
    if rating:
        return rating[0]


def has_garden(features):
    garden_found = [x[1] for x in features if x[0] == "Garden"]
    if garden_found:
        has_garden = None
        if garden_found[0] == "yes":
            has_garden = True
        elif garden_found[0] == "no":
            has_garden = False

        return has_garden


def parse_property_page(property_id, debug=False):
    print("Processing property:", property_id)

    if not debug:
        if os.path.isfile(property_filepath(property_id)):
            print("Skipping as it already exists")
            return

    try:
        html_doc = urllib.request.urlopen("http://www.openrent.co.uk/" +
                                          property_id).read()
    except urllib.error.HTTPError:
        print("Problem parsing %s." % property_id)
        return

    soup = BeautifulSoup(html_doc, 'html.parser')
    preprocess(soup)

    price = soup.find_all("h3", {"class": "banda perMonthPrice"})[0]
    price = float(price.text[1:].replace(',', ''))

    desc = soup.find_all("div", {"class": "well description hovertip"})[0]
    desc = desc.get_text().strip()
    desc.replace("\t", "")

    location = parse_location_table(soup)
    features = parse_feature_table(soup)

    prop = OrderedDict()
    prop['id'] = property_id
    prop['title'] = get_title(soup)
    prop['location'] = location
    prop['price'] = price
    prop['description'] = desc
    prop['available_from'] = available_from(features)
    prop['EPC'] = EPC_rating(features)
    prop['has_garden'] = has_garden(features)

    if not debug:
        with open(property_filepath(property_id), "w") as f:
            json.dump(prop, f, indent=4, ensure_ascii=False)
    else:
        print(json.dumps(prop, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("property_id", help='url to get', type=str)
    parser.add_argument("--debug", help='url to get', action='store_true',
                        default=False)
    args = parser.parse_args()
    property_id = args.property_id
    parse_property_page(property_id, debug=args.debug)
