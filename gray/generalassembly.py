import time

from gray.common.data_utils import write_entries
from gray.common.node_utils import Node, Provider

doc = Node("https://generalassemb.ly/education", Provider.PHANTOMJS)
entries = []
row_els = doc.select_list("#catalog-results > div > *:not(.date-divider)")
for row_idx, row_el in enumerate(row_els):
    start_time = time.time()
    entry = {}
    entry["link"] = row_el.select("a").attr("href")

    details_el = row_el.select(".item-details")
    entry["title"] = details_el.select(".medium.item-title").text()
    entry["desc"] = details_el.children(1).text()
    entry["instructor"] = details_el.select(".instructor").text()

    entry["series"] = row_el.select(".series-info").text()
    entry["date"] = row_el.select(".date-details:first-child").text()
    entry["time"] = row_el.select(".date-details:last-child").text()
    entry["topics"] = row_el.select_list("li.topic-icon-item").attrs("title")
    entry["promo"] = row_el.select_list(".cyber-monday-promo").texts()
    print(row_idx, time.time() - start_time)
    entries.append(entry)

write_entries(entries, "generalassembly")
