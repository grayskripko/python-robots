import os

import time
import upwork

from gray.common.data_utils import first_match, send_email
from gray.common.node_utils import Node, Provider


def get_api_token():
    client = upwork.Client(os.environ["upkey"], os.environ["upsecret"])
    authorize_url = client.auth.get_authorize_url()
    doc = Node(authorize_url, "url", "chrome")
    print("Navigating authorize url...")
    doc.select("#login_username").send_keys("grayskripko@gmail.com")
    doc.select("#login_password").send_keys(os.getenv("up") + "#u")
    doc.select("#layout form").submit()

    print("Navigating token url...")
    verifier_el = doc.select("#main > div")
    verifier = first_match("(?<=oauth_verifier=).+", verifier_el.text)

    oauth_token, oauth_token_secret = client.auth.get_token(verifier)
    oauth_token = oauth_token.decode("utf-8")
    oauth_token_secret = oauth_token_secret.decode("utf-8")
    print(oauth_token, oauth_token_secret)
    return oauth_token, oauth_token_secret
    # client = upwork.Client(os.environ["upkey"], os.environ["upsecret"], os.getenv("uptoken"), os.getenv("uptokensecret"))
    # jobs_list_dict = client.provider_v2.search_jobs(data={'skills': ["mining", "scraping", " crawler", " scrapy"],


def start_monitoring():
    doc = Node("https://www.upwork.com/find-work-home/", Provider.PHANTOMJS)
    doc.select("#login_username").el.send_keys("grayskripko@gmail.com")
    doc.select("#login_password").el.send_keys(os.getenv("up") + "#u")
    doc.select("#layout > div.container.ng-scope > div > form").el.submit()

    jobs = []
    job_links = list(map(lambda node: node.attr("href"), doc.select_list("#jsJobResults .oVisitedLink")))
    for job_link in job_links:
        job = {}
        doc.provider_navigate(job_link)

        job_title_el = doc.select("#layout > .container.ng-scope > :nth-child(2)")
        job_left_col_el = doc.select("#layout > .container.ng-scope > :nth-child(3) > .col-md-9")
        about_company = doc.select("#layout > .container.ng-scope > :nth-child(3) > .col-md-3")

        job["title"] = job_title_el.select("h1").text()
        stars_review_el = about_company.select_by_tag_text("p", "review")
        job["company_reviews"] = stars_review_el.select("*[popover]").attr("popover") if stars_review_el else "0"
        job["company_since"] = about_company.select(".o-support-info").text()
        job["posted_ago"] = job_left_col_el.select("*:nth-child(2)").text()

        price_cell_els = job_left_col_el.select(":nth-child(3)").children()
        job["is_hourly"] = price_cell_els[0].select("strong").text() == "Hourly Job"
        job["budget"] = price_cell_els[1].select("strong").text() if len(price_cell_els) == 3 else ""

        job_details_el = job_left_col_el.select(":nth-child(4)").children()
        job["desc"] = job_details_el[0].select("p.break").text()
        job["skills"] = job_details_el[0].select("#form span").text()

        job_activity_el = job_details_el[-1]
        job["interviewing"] = job_activity_el.select_by_tag_text("p", "Last Viewed").children(1).text()
        job["proposals"] = job_activity_el.select_by_tag_text("p", "Proposals").children(1).text()
        job["interviewing"] = job_activity_el.select_by_tag_text("p", "Interviewing").children(1).text()

        jobs.append(job)
        time.sleep(1)

send_email("msg body")

# write_entries(jobs_list_dict, "jobs.csv")
print("end")
