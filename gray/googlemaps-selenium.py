import re

from selenium.webdriver.common.keys import Keys

from com.common.data_utils import parse_float, first_match, inline_print, write_entries
from com.common.selenium_utils import Document

doc = Document()
entries = []
# queries_str = "Andronico\'s\nBianchini\'s\nCostco\nErewhon\nFalletti Foods\nFresh & Easy\nGelsons\n" \
#               "Mollie Stones\nPetco\nRainbow Grocer\nRalphs\nSafeway\nSmart & Final\nSuper King Markets\n" \
#               "Target\nTrader Joes\nVons\nWalgreens\nWalmart\nWhole Food Markets"
queries_str = "Gelson's"
queries = queries_str.split("\n")

url = "https://www.google.com/#q=california+supermarket+Petco"
doc.navigate(url)  # print(driver.title)
doc.select("#_L8b > div > a:nth-child(3)", need_wait=True).click()  # english
doc.select("#rso div._m3g > a", need_wait=True).click()  # more
items_css = '.rl_full-list .rlfl__tls.rl_tls > div'
doc.select(items_css, need_wait=True)

for query in queries:
    inline_print("\n" + query)
    search_box = doc.select("#lst-ib")
    search_box.clear()
    search_box.send_keys("california supermarket \"{0}\"".format(query))
    search_box.send_keys(Keys.RETURN)

    checker = doc.select("#rso > div[jsl] + div", need_wait=True)  # map and search results
    if not checker:
        inline_print("empty")
        continue
    doc.select("#lu_map", need_wait=True).click()  # click map

    while True:
        page_items = doc.select_list(items_css, need_wait=True)
        inline_print(len(page_items))
        for page_item in page_items:
            lat_str = doc.select("div[data-lat]", page_item, attr="data-lat")  # div.rllt__mi
            lng_str = doc.select("div[data-lng]", page_item, attr="data-lng")
            address_el = doc.select("._gt > a[data-akp-oq]", page_item)
            if address_el is not None:
                city_mess_el = address_el.get_attribute('data-akp-oq')
                city = first_match("(?<={0}\W)[^,]+".format(query), city_mess_el)
                if city == "":
                    n_words = len(query.split(" "))
                    city = re.sub(",.+", "", city_mess_el)
                    city = re.sub("^(\S+ ){" + str(n_words) + "}", "", city)
                    city = re.sub("(?i)markets? ", "", city)
            else:
                city = ""
            entry = {"name": query,
                     "city": city,
                     "street": doc.get_text(".rllt__details ._lfe", address_el),
                     "lat": parse_float(lat_str, 6),
                     "lng": parse_float(lng_str, 6)}
            entries.append(entry)

        next_page = doc.select("#pnnext", captcha_occurs=False)  # table#nav tr > td.cur + td > a
        if next_page is None:
            break
        next_page.click()

doc.shutdown()
write_entries(entries, ["name", "city", "street", "lat", "lng"], '/googlemaps-gels.csv')
