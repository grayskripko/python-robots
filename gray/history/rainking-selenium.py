import os
import re
import time
from selenium.common.exceptions import TimeoutException
from gray.common.node_utils import Document


# script for collection html pages only
def login():
    url = "https://www.rainkingforstaffing.com/login/auth"
    doc = Document(headless=False, page_load_timeout=120)
    print("Getting login page...")
    doc.navigate(url)
    doc.select("#username").send_keys("dev.nisar@welcometech.com")
    doc.select("#password").send_keys("Oneone!23")
    doc.select("#rkFormLogin").submit()
    print("Logging...")
    return doc


# for one discrete filter
def process_filter_section(doc, url):
    url = url if "max=1000" in url \
        else re.sub("\?", "?max=1000&", url, count=1) if "?" in url \
        else url + "?max=1000"  # change url for getting 1000 results per page
    doc.navigate(url)

    category_name = re.sub("\W", "", doc.select("#searchForm h1 > .search_title").text)
    filter_name = re.sub("\W", "", doc.select("#saved_search_container").text)
    print("Filter section [{0}]".format(filter_name))

    while True:
        pagination_root = doc.select(".pagination > ul")
        cur_page_idx = doc.select("li.active", pagination_root)
        cur_page_idx = cur_page_idx.text if cur_page_idx else ""
        print("Page [{0}]".format(cur_page_idx))
        doc.page_save_as(category_name + "_" + filter_name + "_" + str(cur_page_idx))

        #  rest of this function is attempt to navigate to next page if it exists
        if not pagination_root or doc.select_list("li.next.disabled", pagination_root):
            break

        next_url = doc.select("li.next a", pagination_root)
        next_url = next_url.get_attribute("href") if next_url else ""
        print(next_url)
        while True:
            try:
                doc.navigate(next_url)
                break
            except TimeoutException:
                print("timeout exception")
                time.sleep(15)
            except Exception as ex:
                print("Common exception: ", ex)


doc = login()
category_els = doc.select_list("#rkSubNav > .navOffset > .navItem > a", need_wait=True)
narrow_category_urls = [cat.get_attribute("href") for cat in category_els if cat.text in ["People", "Companies", "Scoops"]]

for cat_idx, category_url in enumerate(narrow_category_urls):
    print("Category [{0}]".format(cat_idx))
    doc.navigate(category_url)

    filter_section_els = doc.select_list("#saved_search_drop_down > ul > li > a", need_wait=True)
    filter_section_urls = [x.get_attribute("href") for x in filter_section_els]
    filter_section_urls.append(doc.driver.current_url)  # appending current filter

    for filter_section_url in filter_section_urls:
        process_filter_section(doc, filter_section_url)

print("end")
