# from abc import ABCMeta, abstractmethod
import re

from lxml.cssselect import CSSSelector
from lxml.html import fromstring
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import *
from gray.common.data_utils import clear_text, time_measure, get_domain, first_match, parse_number
from gray.rear.keaboard_emulation import *


class Node:
    def __init__(self, el_source, provider_type=None,
                 dynamic_for_browser=True, waited_el_css=None,
                 page_load_timeout=30, ajax_timeout=5):
        """
        :param provider_type: ['requests', 'chrome', 'phantomjs']
        """
        str_node_source = str(el_source)
        if str_node_source.startswith("C:") or str_node_source.startswith("D:"):
            node_source_type = "file"
        elif str_node_source.startswith("http") or str_node_source.startswith("www"):
            node_source_type = "url"
        else:
            self.el = el_source
            return

        if node_source_type == "url":
            if provider_type == Provider.REQUESTS:
                self.timeout = page_load_timeout
            else:
                self.browser = Browser(provider_type, page_load_timeout, ajax_timeout)
            self.navigate(el_source, dynamic_for_browser, waited_el_css)
        elif node_source_type == "file":
            self.el = fromstring(open(el_source, encoding="utf-8"))
        else:
            raise ValueError("node_source_type not in ['node', 'url', 'file']")

    def navigate(self, url, dynamic_for_browser=True, waited_el_css=None):
        start_time = time.time()
        if self.browser:
            self.browser.navigate(url, waited_el_css)
            driver = self.browser.driver
            self.el = driver if dynamic_for_browser else fromstring(driver.page_source)
        else:
            for attempts in range(5, 0, -1):
                try:
                    response = requests.get(url, timeout=self.timeout)
                    self.el = fromstring(response.text)
                except Exception as e:
                    print("Bad navigation attempt", e)
                    time.sleep(self.timeout << 1)
        time_measure(url, start_time)
        return self.__create_node__(self.el)

    def get_html_snapshot(self):
        return self.__create_node__(fromstring(self.browser.driver.page_source))

    def wait(self, css_of_waited):
        self.browser.wait(css_of_waited)

    def save_as(self, file_name=None, delay_before_win_enter=2):
        self.browser.save_as(file_name, delay_before_win_enter)

    def shutdown(self):
        self.browser.shutdown()
        self.el = None

    def select_list(self, css_query):
        if self.el is None:
            return NodeList([self.__create_node__(None)])
        if hasattr(self, 'browser'):
            result_els = __safe_execution__(self.el.find_elements_by_css_selector, css_query)
        else:
            selector = CSSSelector(css_query)
            result_els = __safe_execution__(selector, self.el)
        return NodeList(map(lambda el: self.__create_node__(el), result_els))

    def select(self, query, is_browser_css_query=True):
        # "{0}:contains('{1}')" "//{0}[contains(., '{1}')]"
        if self.el is None:
            return self.__create_node__(None)
        if hasattr(self, 'browser'):
            if ":contains" in query:
                # "h1:contains('job is private')""
                possible_tag = re.sub(":contains\(.+?\)", "", query)
                if " " not in possible_tag and "." not in possible_tag \
                        and ":" not in possible_tag and ">" not in possible_tag:
                    contains_text = first_match("(?<=:contains\(.)[^'\"]+", query)
                    by = By.XPATH
                    query = "//{0}[contains(., '{1}')]".format(possible_tag, contains_text)
                else:
                    raise ValueError("could not rewrite ':contains' in xpath")
            else:
                by = By.CSS_SELECTOR if is_browser_css_query else By.XPATH
            result_el = __safe_execution__(self.el.find_element, by, query)
        else:
            selector = CSSSelector(query)
            result_els = __safe_execution__(selector, self.el)  # check for None
            result_el = result_els[0] if result_els else None
        return self.__create_node__(result_el)

    def children(self, idx=None):
        if self.el is None:
            return self.__create_node__(None) if idx else NodeList([self.__create_node__(None)])
        if hasattr(self, 'browser'):
            children_els = self.el.find_elements_by_xpath("*")
        else:
            children_els = self.el.getchildren()
        if not children_els:
            return self.__create_node__(None)
        if idx:
            return self.__create_node__(children_els[idx]) if idx < len(children_els) else self.__create_node__(None)
        return NodeList(map(lambda el: self.__create_node__(el), children_els))

    def text(self, pattern=None, safe=True):
        if safe and self.el is None:
            return ""
        text = first_match(pattern, self.el.text) if pattern else self.el.text  # coincidence of selenium and lxml
        if hasattr(self, 'browser'):
            return text
        return clear_text(text)

    def attr(self, attr_name, safe=True):
        if safe and self.el is None:
            return ""
        if hasattr(self, 'browser'):
            return self.el.get_attribute(attr_name)
        return self.el.get(attr_name)

    def abs_url(self, url):
        domain_url = get_domain(url)
        if domain_url.endswith("/"):
            raise ValueError("Url with redundant '//'")
        href = self.attr("href")
        if href == "":
            raise ValueError("Href is empty")
        if hasattr(self, 'browser'):
            return href
        return domain_url + href

    def number(self, pattern=None, prec=0, attr_name=None):
        if attr_name:
            str_number = first_match(pattern, self.attr(attr_name)) if pattern else self.attr(attr_name)
        else:
            str_number = self.text(pattern)
        if not str_number:
            return None
        return parse_number(str_number, prec)

    def send_keys(self, val):
        throw_error_if_not = self.browser
        self.el.send_keys(val)

    def __create_node__(self, el):
        result_node = Node(el)
        if hasattr(self, 'browser'):
            result_node.browser = self.browser
        return result_node

    def __bool__(self):
        return self.el is not None


class NodeList(list):
    def texts(self, one_line=True):
        result = list(map(lambda node: node.text(), self))  # list.__getitem__(self, key-1)
        return " | ".join(result) if one_line else result

    def attrs(self, attr_name, one_line=True):
        result = list(map(lambda node: node.attr(attr_name), self))
        return " | ".join(result) if one_line else result

    def __getitem__(self, key):
        try:
            return list.__getitem__(self, key)
        except Exception:
            return None


class Browser:
    def __init__(self, provider_type, page_load_timeout, ajax_timeout):
        if provider_type == Provider.CHROME:
            options = webdriver.ChromeOptions()
            options.add_argument('--lang=en')
            executable_path = "D:\\dev\\projects\\Python\\robots\\resources\\chromedriver.exe"
            self.driver = webdriver.Chrome(chrome_options=options, executable_path=executable_path)
        elif provider_type == Provider.PHANTOMJS:
            webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.Accept-Language'] = 'en-US'
            executable_path = "D:\\dev\\projects\\Python\\robots\\resources\\phantomjs.exe"
            self.driver = webdriver.PhantomJS(executable_path)
        else:
            raise ValueError("browser type must be in ['chrome', 'phantomjs']")
        self.driver.set_page_load_timeout(page_load_timeout)
        self.waiter = WebDriverWait(self.driver, ajax_timeout)

    def navigate(self, url, css_of_waited=None):
        for attempts in range(5, 0, -1):
            try:
                self.driver.get(url)
                if css_of_waited:
                    self.waiter.until(lambda x: self.driver.find_element_by_css_selector(css_of_waited))
                # print(url)
                return
            except Exception as e:
                print("Bad navigation attempt", e)
                time.sleep(30)
                # if captcha_occurs: return self.__common_select__(el, query, select_type, need_wait, captcha_occurs=False)

    def wait(self, css_of_waited):
        self.waiter.until(lambda x: self.driver.find_elements_by_css_selector(css_of_waited))
        # if need_wait:
        #     self.waiter.until(lambda x: el.find_elements(by, query) and
        #                             el.find_element(by, query) != self._last_el)
        #     self.waiter.until(lambda x: el.find_elements_by_css_selector(query) and
        #                             el.find_elements_by_css_selector(query)[-1] != self._list_last_el)

    def save_as(self, file_name=None, delay_before_win_enter=2):
        save_as_dialog = ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL)
        save_as_dialog.perform()
        time.sleep(delay_before_win_enter)
        if file_name:
            do_button_stream(file_name)
        press_enter()
        time.sleep(1)

    def shutdown(self):
        self.driver.quit()


def __safe_execution__(func, *args):  # , need_wait=False, captcha_occurs=True
    try:
        return func(*args)
    except (TimeoutException, NoSuchElementException):
        return None
    except Exception as e:
        raise e


class Provider:
    REQUESTS = "requests"
    CHROME = "chrome"
    PHANTOMJS = "phantomjs"
