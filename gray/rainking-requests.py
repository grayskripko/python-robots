import re
import os

import time

from gray.common.bs4_utils import Node
from gray.common.data_utils import inline_print, first_match, write_entries

rainking_out_path = os.getenv("OUT") + "rainking\\"  # path to saved html pages


def process_page(saved_page):
    filter_name = first_match("(?<=_)\w+(?=_)", saved_page)
    i_page = first_match("(?<=_)\d*(?=\.)", saved_page)  # i_ prefix means "index"

    node = Node(rainking_out_path + saved_page)  # utils wrapper class
    table_el = node.select("#searchForm .grid-content.expanding-content > table")
    column_names = list(map(lambda x: x.text(), table_el.select_list("thead th")))
    row_els = table_el.select_list("tbody > tr")
    page_entries = []
    na_cells = 0  # we will set na for cells with exceptions. It is important for unstructured "Inside scoops" column

    for i_row, row_el in enumerate(row_els):
        entry = {"filter_name": filter_name, "page#": i_page}
        cell_els = row_el.select_list("td")
        for i_col, column in enumerate(column_names):
            if column in ["", "Status"]:
                continue
            elif column == "Company":
                entry[column] = "Accounts::::" + cell_els[i_col].text()
            elif column == "Inside Scoop":
                # example for regex:
                # Topic: Security, Staffing.
                # Company: Virgin Media Inc., New York, NY    Find the Best Contacts
                # Opportunity: Seeking a Security Data Engineer (England,Peterborough,PE3).    View Details
                cur_cell_text = cell_els[i_col].text()
                company_el = cell_els[i_col].select("a")
                if company_el is None:
                    company_name = first_match("(?<=Company:)[^,]*", cur_cell_text)
                    if not company_name:
                        company_name = cur_cell_text
                        na_cells += 1
                else:
                    company_name = company_el.text()
                entry["Company"] = "Accounts::::" + company_name
                location_regex = "(?<={0}).+?(?=\n|$|Find the Best Contacts)".format(company_name)
                location = first_match(location_regex, cur_cell_text)
                entry["Location"] = re.sub("^,\s*", "", location)
                opportunity_regex = "(?<=Opportunity:).+?(?=\n|$|View Details)".format(company_name)
                entry["Opportunity"] = first_match(opportunity_regex, cur_cell_text)
                opp_link_el = cell_els[i_col].select("a:contains('Details')")
                if opp_link_el:
                    entry["Opportunity_link"] = opp_link_el.attr("href")
                else:
                    entry["Opportunity_link"] = "NA"
                    na_cells += 1
            else:
                entry[column] = cell_els[i_col].text()
        page_entries.append(entry)
    if na_cells:
        print("--", str(na_cells))
    return page_entries


start_time = time.time()
saved_pages = [x for x in os.listdir(rainking_out_path) if x.endswith(".html")]
people_pages = [x for x in saved_pages if x.startswith("People")]  # split saved_pages for separate processing because their columns are different
companies_pages = [x for x in saved_pages if x.startswith("Companies")]
scoops_pages = [x for x in saved_pages if x.startswith("Scoops")]

for i_cat, category_pages in enumerate([people_pages, companies_pages, scoops_pages]):
    category_entries = []
    for i_page, saved_page in enumerate(category_pages):
        print(i_cat, i_page, "" if i_page % 10 else str(round(time.time() - start_time, 2)))
        category_entries += process_page(saved_page)
    write_entries(category_entries, i_cat)
