import traceback
import pdb
import os
import time

from ynabamazonparser import utils, gui
from ynabamazonparser.config import settings
from ynabamazonparser.amazon.item import Item
from ynabamazonparser.amazon.order import Order

import glob
import csv
import collections


def get_downloaded_csv_filenames():
    return set(
        glob.glob(os.path.join(settings.downloads_dir, '*.csv')))


def wait_for_download(timeout=30):
    filenames_before = get_downloaded_csv_filenames()
    for i in range(timeout):
        filenames = get_downloaded_csv_filenames()
        new_filenames = filenames - filenames_before
        if new_filenames:
            assert len(new_filenames) == 1
            break
        time.sleep(1)
    return new_filenames.pop()


def parse_items(item_dicts):
    return list(map(Item.from_dict, item_dicts))


def parse_orders(order_dicts):
    orders = list(map(Order.from_dict, order_dicts))
    return combine_orders(orders)


data_parsers = {'items': parse_items, 'orders': parse_orders}
' TODO: get refunds, returns '
csv_paths = {k: os.path.join(settings.data_dir, k + '.csv')
             for k in data_parsers}


def missing_csv(data_type):
    return not os.path.exists(csv_paths[data_type])


def read(p):
    with open(p, newline='\n') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        return list(reader)



def combine_orders(orders):
    combined = {}
    for order in orders:
        if order.order_id in combined:
            combined[order.order_id] += order
        else:
            combined[order.order_id] = order
    return list(combined.values())


def load(data_type):
    assert data_type in data_parsers
    target_path = csv_paths[data_type]
    try:
        if settings.force_download_amazon or missing_csv(data_type):
            d = gui.driver()
            url = 'https://smile.amazon.com/gp/b2b/reports'
            if d.current_url != url:
                d.get(url)

            d.find_element_by_id('report-last30Days').click()
            d.find_element_by_id('report-type').click()
            d.find_element_by_id('report-type').send_keys(data_type)
            d.find_element_by_id('report-confirm').click()
            path = wait_for_download()
            os.rename(path, target_path)

    except BaseException:
        if input('One more try?').lower() != 'q':
            load(data_type)
        else:
            utils.quit()

    return data_parsers[data_type](read(target_path))
