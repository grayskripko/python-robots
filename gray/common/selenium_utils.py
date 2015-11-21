import win32api
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import *
from gray.rear.keaboard_emulation import *


class Document:
    def __init__(self, headless=False, page_load_timeout=30, ajax_timeout=5):
        if headless:
            webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.Accept-Language'] = 'en-US'
            self.driver = webdriver.PhantomJS(
                executable_path="D:\\dev\\projects\\Python\\robots\\resources\\phantomjs.exe")
        else:  # start-maximized
            options = webdriver.ChromeOptions()
            options.add_argument('--lang=en')
            self.driver = webdriver.Chrome(
                executable_path="D:\\dev\\projects\\Python\\robots\\resources\\chromedriver.exe",
                chrome_options=options)
            # self.driver = webdriver.Firefox()

        self.driver.set_page_load_timeout(page_load_timeout)
        self.waiter = WebDriverWait(self.driver, ajax_timeout)
        self._last_el = None
        self._list_last_el = None

    def get_driver(self):
        return self.driver

    def navigate(self, url):
        self.driver.get(url)

    def shutdown(self):
        self.driver.quit()

    def select_list(self, css_query, root_el="", attr=None, need_wait=False, captcha_occur=True):
        root_el = self.driver if root_el == "" else root_el
        if root_el is None:
            print("Root_el for css_query [{0}] is None".format(css_query))
            return None
        try:
            if need_wait:
                self.waiter.until(lambda x: root_el.find_elements_by_css_selector(css_query) and
                                            root_el.find_elements_by_css_selector(css_query)[-1] != self._list_last_el)
            target_els = root_el.find_elements_by_css_selector(css_query)
            self._list_last_el = target_els[-1] if need_wait else self._list_last_el
        except (TimeoutException, NoSuchElementException):
            if captcha_occur:
                return self.select_list(css_query, root_el, attr, need_wait, captcha_occur=False)
            else:
                return []
        except StaleElementReferenceException as stale_exc:
            raise stale_exc
        return target_els if attr is None else list(map(lambda x: x.get_attribute(attr), target_els))

    def select(self, css_query, root_el="", attr=None, need_wait=False, captcha_occurs=True):
        root_el = self.driver if root_el == "" else root_el
        if root_el is None:
            print("Root_el for css_query [{0}] is None".format(css_query))
            return None
        try:
            if need_wait:
                self.waiter.until(lambda x: root_el.find_elements_by_css_selector(css_query) and
                                            root_el.find_element_by_css_selector(css_query) != self._last_el)
            target_el = root_el.find_element_by_css_selector(css_query)
            self._last_el = target_el if need_wait else self._last_el
        except (TimeoutException, NoSuchElementException):
            if captcha_occurs:
                return self.select(css_query, root_el, attr, need_wait, captcha_occurs=False)
            else:
                return None
        except StaleElementReferenceException as stale_exc:
            raise stale_exc
        except Exception as ex:
            raise ex
        return target_el if attr is None else target_el.get_attribute(attr)

    def select_by_tag_text(self, tag, el_text, root_el="", attr=None, need_wait=False, captcha_occurs=True):
        xpath_query = "//{0}[contains(., '{1}')]".format(tag, el_text)
        root_el = self.driver if root_el == "" else root_el
        if root_el is None:
            print("Root_el for css_query [{0}] is None".format(xpath_query))
            return None
        try:
            if need_wait:
                self.waiter.until(lambda x: root_el.find_elements_by_xpath(xpath_query) and
                                            root_el.find_element_by_xpath(xpath_query) != self._last_el)
            target_el = root_el.find_element_by_xpath(xpath_query)
            self._last_el = target_el if need_wait else self._last_el
        except (TimeoutException, NoSuchElementException):
            if captcha_occurs:
                return self.select(xpath_query, root_el, attr, need_wait, captcha_occurs=False)
            else:
                return None
        except StaleElementReferenceException as stale_exc:
            raise stale_exc
        except Exception as ex:
            raise ex
        return target_el if attr is None else target_el.get_attribute(attr)

    def get_text(self, css_query, root_el=None, safe=True, map_text=False):
        try:
            if map_text:
                return list(map(lambda x: x.text, self.select_list(css_query, root_el=None)))
            else:
                return self.select(css_query, root_el).text
        except Exception as ex:
            if safe:
                return None if map_text else ""
            else:
                raise ex

    def page_save_as(self, file_name=None, delay_before_win_enter=2):
        save_as_dialog = ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL)
        save_as_dialog.perform()
        time.sleep(delay_before_win_enter)

        if file_name is not None:
            do_button_stream(file_name)
        press_enter()
        time.sleep(1)
        # import win32con
        # win32api.keybd_event(win32con.SHIFT_PRESSED, 0, win32con.KEYEVENTF_EXTENDEDKEY, 0)
