import traceback
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.command import Command

import ynabamazonparser as yap


def get(class_name, count=None, require=True, predicate=None, wait=30):
    yap.utils.log('get', class_name)
    predicate = predicate or bool  # bool serves as the identity
    if wait:
        try:  # may stop waitin gwhen right class is found, but predicate is still failing...
            WebDriverWait(driver(), wait).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
        except BaseException:
            if require:
                yap.utils.log('element not found', class_name)
                yap.utils.log(traceback.format_exc())
                retry_message = ('%s elements not found, keep waiting? [y/N]' % class_name).lower()
                if input(retry_message).lower() == 'y':
                    get(class_name, predicate, count, wait)
                else:
                    yap.utils.quit()

    class_elements = driver().find_elements_by_class_name(class_name)
    matches = list(filter(predicate, class_elements))
    if require:
        assert matches
        if count is not None:
            assert len(matches) == count
    if len(matches) == 1:
        return matches[0]
    return matches


def get_by_placeholder(class_name, p, count=None, require=True):
    if isinstance(p, str):
        p = (p,)
    return get(class_name, count, require, lambda e: e.get_attribute('placeholder') in p)


def get_by_text(class_name, t, count=None, require=True, partial=False):
    if isinstance(t, str):
        t = (t,)
    if partial:
        return get(class_name, count, require, lambda e: any(T in e.text for T in t))
    return get(class_name, count, require, lambda e: e.text in t)


def click(element, n=1, pause=1):
    if type(element) in (tuple, list):
        element = element[0]
    for i in range(n):
        driver().execute_script('arguments[0].click();', element)
        if i != n - 1:
            time.sleep(pause)


def right_click(element):
    if type(element) in (tuple, list):
        element = element[0]
    actions = ActionChains(driver())
    actions.context_click(element).perform()


def send_keys(keys):
    actions = ActionChains(driver())
    actions.send_keys(keys).perform()


_driver = None


def driver():
    global _driver
    try:
        if is_alive(_driver):
            return _driver
        options = Options()
        options.add_argument('user-data-dir={}'.format(yap.settings.chrome_data_dir))
        options.add_argument('--disable-extensions')
        _driver = webdriver.Chrome(options=options)
    except BaseException:
        error = traceback.format_exc()
        if 'data directory is already in use' in error:
            yap.utils.log('ERROR: selenium controlled chrome still open. Close it and try again.')

            # TODO: retry?
            # TODO: general input() based retrier
        else:
            yap.utils.log(error)
        yap.utils.quit()
    return _driver


def is_alive(d):
    try:
        d.execute(Command.STATUS)
        return True
    except BaseException:
        return False
