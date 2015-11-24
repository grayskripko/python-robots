from abc import ABCMeta, abstractmethod
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
    def __init__(self, el_source, provider_type=None, page_load_timeout=30, ajax_timeout=5):
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
                self.provider = Requests(page_load_timeout)
            else:
                self.provider = Browser(provider_type, page_load_timeout, ajax_timeout)
            self.provider_navigate(el_source)
        elif node_source_type == "file":
            self.el = bs4.BeautifulSoup(open(el_source, encoding="utf-8"))
        else:
            raise ValueError("node_source_type not in ['node', 'url', 'file']")

    def provider_navigate(self, url):
        self.el = self.provider.navigate(url)
        return self.__create_node__(self.el)

    def provider_save_as(self, file_name=None, delay_before_win_enter=2):
        self.provider.save_as(file_name, delay_before_win_enter)

    def provider_shutdown(self):
        self.provider.shutdown()
        self.el = None

    def select_list(self, css_query, need_wait=False, captcha_occurs=True):
        if not self.el:
            return NodeList(self.__create_node__(None))
        return NodeList(map(lambda el: self.__create_node__(el),
                        self.provider.select_list(self.el, css_query, need_wait, captcha_occurs)))

    def select(self, css_path, need_wait=False, captcha_occurs=True):
        return self.__create_node__(self.provider.select(self.el, css_path, need_wait, captcha_occurs)) \
            if self.el else self.__create_node__(None)

    def select_by_tag_text(self, tag, el_text, need_wait=False, captcha_occurs=True):
        return self.__create_node__(self.provider.select_by_tag_text(self.el, tag, el_text, need_wait, captcha_occurs)) \
            if self.el else self.__create_node__(None)

    def children(self, idx=None):
        if not self.el:
            return self.__create_node__(None) if idx else NodeList(self.__create_node__(None))
        children_els = self.provider.children(self.el)
        if idx:
            return self.__create_node__(children_els[idx]) if idx < len(children_els) else self.__create_node__(None)
        return NodeList(map(lambda el: self.__create_node__(el), children_els))

    def text(self, safe=True):
        return self.provider.text(self.el, safe)

    def attr(self, attr_name, safe=True):
        return self.provider.attr(self.el, attr_name, safe)

    def __create_node__(self, el):
        result_node = Node(el)
        result_node.provider = self.provider
        return result_node

    def __nonzero__(self):
        return self.el is not None


class NodeList(list):
    def texts(self, one_line=True):
        result = list(map(lambda node: node.text(), self))  # list.__getitem__(self, key-1)
        return " | ".join(result) if one_line else result

    def attrs(self, attr_name, one_line=True):
        result = list(map(lambda node: node.attr(attr_name), self))
        return " | ".join(result) if one_line else result


class AbstractDocumentProvider(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def navigate(self, url): pass

    @abstractmethod
    def save_as(self, file_name=None, delay_before_win_enter=2): pass

    @abstractmethod
    def shutdown(self): pass

    @abstractmethod
    def select_list(self, el, css_query, need_wait=False, captcha_occurs=True): pass

    @abstractmethod
    def select(self, el, css_query, need_wait=False, captcha_occurs=True): pass

    @abstractmethod
    def select_by_tag_text(self, el, tag, el_text, need_wait=False, captcha_occurs=True): pass

    @abstractmethod
    def children(self, el): pass

    @abstractmethod
    def text(self, el, safe=True): pass

    @abstractmethod
    def attr(self, el, attr_name, safe=True): pass


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

    def select_list(self, el, css_query, need_wait=False, captcha_occurs=True):
        return el.select(css_query)

    def select(self, el, css_query, need_wait=False, captcha_occurs=True):
        results = self.select_list(el, css_query)
        return results[0] if results else None

    def select_by_tag_text(self, el, tag, el_text, need_wait=False, captcha_occurs=True):
        return self.select(el, "{0}:contains('{1}')".format(tag, el_text))

    def children(self, el):
        return el.findChildren()

    def text(self, el, safe=True):
        if safe and not el:
            return ""
        el_text = el.get_text()
        return clear_text(el_text)

    def attr(self, el, attr_name, safe=True):
        return el.attrs.get(attr_name) if el or not safe else None


class Browser(AbstractDocumentProvider):
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
        self._last_el = None
        self._list_last_el = None

    def navigate(self, url):
        for attempts in range(5, 0, -1):
            try:
                self.driver.get(url)
                print(url)
                return self.driver
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

    def __common_select__(self, el, query, select_type, need_wait=False, captcha_occurs=True):
        """
        :param select_type: ['select_list', 'select', 'select_xpath']
        """
        try:
            if select_type == "select_list":
                if need_wait:
                    self.waiter.until(lambda x: el.find_elements_by_css_selector(query) and
                                            el.find_elements_by_css_selector(query)[-1] != self._list_last_el)
                result = el.find_elements_by_css_selector(query)
                self._list_last_el = result[-1] if need_wait else self._list_last_el
            elif select_type in ["select", "xpath"]:
                by = By.CSS_SELECTOR if select_type == "select" else By.XPATH
                if need_wait:
                    self.waiter.until(lambda x: el.find_elements(by, query) and
                                            el.find_element(by, query) != self._last_el)
                result = el.find_element(by, query)
                self._last_el = result if need_wait else self._last_el
            else:
                raise ValueError("select_type not in ['select_list', 'select', 'xpath']")
            return result
        except (TimeoutException, NoSuchElementException):
            if captcha_occurs:
                return self.__common_select__(el, query, select_type, need_wait, captcha_occurs=False)
            else:
                return None
        except Exception as e:
            raise e

    def select_list(self, el, css_query, need_wait=False, captcha_occurs=True):
        return self.__common_select__(el, css_query, "select_list", need_wait, captcha_occurs)

    def select(self, el, css_query, need_wait=False, captcha_occurs=True):
        return self.__common_select__(el, css_query, "select", need_wait, captcha_occurs)

    def select_by_tag_text(self, el, tag, el_text, need_wait=False, captcha_occurs=True):
        xpath_query = "//{0}[contains(., '{1}')]".format(tag, el_text)
        return self.__common_select__(el, xpath_query, "xpath", need_wait, captcha_occurs)

    def children(self, el):
        return el.find_elements_by_xpath("*")

    def text(self, el, safe=True):
        return el.text if el or not safe else ""

    def attr(self, el, attr_name, safe=True):
        return el.get_attribute(attr_name) if el or not safe else ""


class Provider:
    REQUESTS = "requests"
    CHROME = "chrome"
    PHANTOMJS = "phantomjs"
