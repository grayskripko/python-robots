from abc import ABCMeta, abstractmethod
import win32api
import bs4
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import *

from gray.common.data_utils import clear_text
from gray.rear.keaboard_emulation import *


class Node:
    def __init__(self, node_source, node_source_type="node", provider_type=None,
                 page_load_timeout=30, ajax_timeout=5):
        """
        :param node_source_type: ['node', 'url', 'file']
        :param provider_type: ['requests', 'chrome', 'phantomjs']
        """

        if node_source_type == "node":
            self.node = node_source
        elif node_source_type == "url":
            if provider_type == "requests":
                self.provider = Requests(page_load_timeout)
            else:
                self.provider = Browser(provider_type, page_load_timeout, ajax_timeout)
            self.provider_navigate(node_source)
        elif node_source_type == "file":
            self.node = bs4.BeautifulSoup(open(node_source, encoding="utf-8"))
        else:
            raise ValueError("node_source_type not in ['node', 'url', 'file']")

    def provider_navigate(self, url):
        self.node = self.provider.navigate(url)
        return Node(self.node)

    def provider_save_as(self, file_name=None, delay_before_win_enter=2):
        self.provider.save_as(file_name, delay_before_win_enter)

    def provider_shutdown(self):
        self.provider.shutdown()
        self.node = None

    def select_list(self, css_query, need_wait=False, captcha_occurs=True):
        return list(map(lambda el: Node(el), self.provider.select_list(self.node, css_query, need_wait, captcha_occurs)))

    def select(self, css_path, need_wait=False, captcha_occurs=True):
        return Node(self.provider.select(self.node, css_path, need_wait, captcha_occurs))

    def select_by_tag_text(self, tag, el_text, need_wait=False, captcha_occurs=True):
        return Node(self.provider.select_by_tag_text(self.node, tag, el_text, need_wait, captcha_occurs))

    def text(self, safe=True):
        return self.provider.text(self.node, safe)

    def attr(self, attr_name, safe=True):
        return self.provider.attr(self.node, attr_name, safe)


class AbstractDocumentProvider(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def navigate(self, url): pass

    @abstractmethod
    def save_as(self, file_name=None, delay_before_win_enter=2): pass

    @abstractmethod
    def shutdown(self): pass

    @abstractmethod
    def select_list(self, node, css_query, need_wait=False, captcha_occurs=True): pass

    @abstractmethod
    def select(self, node, css_query, need_wait=False, captcha_occurs=True): pass

    @abstractmethod
    def select_by_tag_text(self, node, tag, el_text, need_wait=False, captcha_occurs=True): pass

    @abstractmethod
    def text(self, node, safe=True): pass

    @abstractmethod
    def attr(self, node, attr_name, safe=True): pass


class Requests(AbstractDocumentProvider):
    def __init__(self, timeout=20):
        self.timeout = timeout

    def navigate(self, url):
        for attempts in range(5, 0, -1):
            try:
                response = requests.get(url, timeout=self.timeout)
                return bs4.BeautifulSoup(response.text)
            except Exception as e:
                print("Bad navigation attempt", e)
                time.sleep(self.timeout << 1)

    def save_as(self, file_name=None, delay_before_win_enter=2):
        raise ValueError("Not applicable for Requests")

    def shutdown(self):
        raise ValueError("Not applicable for Requests")

    def select_list(self, node, css_query, need_wait=False, captcha_occurs=True):
        return node.select(css_query)

    def select(self, node, css_query, need_wait=False, captcha_occurs=True):
        results = self.select_list(node, css_query)
        return results[0] if results else None

    def select_by_tag_text(self, node, tag, el_text, need_wait=False, captcha_occurs=True):
        return self.select(node, "{0}:contains('{1}')".format(tag, el_text))

    def text(self, node, safe=True):
        if safe and not node:
            return ""
        node_text = node.get_text()
        return clear_text(node_text)

    def attr(self, node, attr_name, safe=True):
        return node.attrs.get(attr_name) if node or not safe else None


class Browser(AbstractDocumentProvider):
    def __init__(self, provider_type, page_load_timeout, ajax_timeout):
        if provider_type == "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument('--lang=en')
            executable_path = "D:\\dev\\projects\\Python\\robots\\resources\\chromedriver.exe"
            self.driver = webdriver.Chrome(chrome_options=options, executable_path=executable_path)
        elif provider_type == "phantomjs":
            webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.Accept-Language'] = 'en-US'
            executable_path = "D:\\dev\\projects\\Python\\robots\\resources\\phantomjs.exe"
            self.driver = webdriver.PhantomJS(executable_path)
        else:
            raise ValueError("browser type must be in ['chrome', 'phantomjs']")
        self.driver.set_page_load_timeout(page_load_timeout)
        self.waiter = WebDriverWait(self.driver, ajax_timeout)
        self._last_el = None
        self._list_last_el = None

    def navigate(self, url):
        for attempts in range(5, 0, -1):
            try:
                return self.driver.get(url)
            except Exception as e:
                print("Bad navigation attempt", e)
                time.sleep(30)

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

    def __common_select__(self, node, query, select_type, need_wait=False, captcha_occurs=True):
        """
        :param select_type: ['select_list', 'select', 'select_xpath']
        """
        try:
            if select_type == "select_list":
                if need_wait:
                    self.waiter.until(lambda x: node.find_elements_by_css_selector(query) and
                                            node.find_elements_by_css_selector(query)[-1] != self._list_last_el)
                result = node.find_elements_by_css_selector(query)
                self._list_last_el = result[-1] if need_wait else self._list_last_el
            elif select_type in ["select", "select_xpath"]:
                by = By.CSS_SELECTOR if select_type == "select" else By.XPATH
                if need_wait:
                    self.waiter.until(lambda x: node.find_elements(by, query) and
                                            node.find_element(by, query) != self._last_el)
                result = node.find_element(by, query)
                self._last_el = result if need_wait else self._last_el
            else:
                raise ValueError("select_type not in ['select_list', 'select', 'xpath']")
            return result
        except (TimeoutException, NoSuchElementException):
            if captcha_occurs:
                return self.__common_select__(node, query, select_type, need_wait, captcha_occurs=False)
            else:
                return None
        except Exception as e:
            raise e

    def select_list(self, node, css_query, need_wait=False, captcha_occurs=True):
        return self.__common_select__(node, css_query, "select_list", need_wait, captcha_occurs)

    def select(self, node, css_query, need_wait=False, captcha_occurs=True):
        return self.__common_select__(node, css_query, "select_list", need_wait, captcha_occurs)

    def select_by_tag_text(self, node, tag, el_text, need_wait=False, captcha_occurs=True):
        xpath_query = "//{0}[contains(., '{1}')]".format(tag, el_text)
        return self.__common_select__(node, xpath_query, "xpath", need_wait, captcha_occurs)

    def text(self, node, safe=True):
        return node.text if node or not safe else ""

    def attr(self, node, attr_name, safe=True):
        return node.get_attribute(attr_name) if node or not safe else ""

