import os

import time
import upwork

from gray.common.data_utils import first_match, send_email, parse_number
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
    url = "https://www.upwork.com/find-work-home/"
    doc = Node(url, Provider.PHANTOMJS)
    doc.select("#login_username").send_keys("grayskripko@gmail.com")
    doc.select("#login_password").send_keys(os.getenv("up") + "#u")
    doc.select("#layout > div.container.ng-scope > div > form").el.submit()

    jobs = []
    job_links = list(map(lambda node: node.abs_url(url),
                         doc.select_list("#jsJobResults .oVisitedLink")))
    for job_link in job_links:
        doc.navigate(job_link)
        if doc.select("h1:contains('job is private')"):
            continue

        job = {}
        job_title_el = doc.select("#layout > .container.ng-scope > :nth-child(2)")
        job_left_col_el = doc.select("#layout > .container.ng-scope > :nth-child(3) > .col-md-9")
        about_company = doc.select("#layout > .container.ng-scope > :nth-child(3) > .col-md-3")

        job["url"] = job_link
        job["title"] = job_title_el.select("h1").text()
        stars_review_popover_el = about_company.select("p:contains('review')").select("*[popover]")

        job["reliability_stars"] = stars_review_popover_el.number(pattern="[\d\.]+(?= stars?)", prec=2, attr_name="popover") \
            if stars_review_popover_el else None
        job["reliability_stars_reviewers"] = stars_review_popover_el.number(pattern="(?<=based on )\d+", attr_name="popover") \
            if stars_review_popover_el else None
        job["company_since"] = about_company.select(".o-support-info").text()
        job["posted_ago"] = job_left_col_el.select("*:nth-child(2)").text()

        price_cell_els = job_left_col_el.select(":nth-child(3)").children()
        job["is_hourly"] = price_cell_els[0].select("strong").text() == "Hourly Job"
        job["budget"] = price_cell_els[1].select("strong").number(pattern="(?=\$)\d+") \
            if len(price_cell_els) == 3 else None

        job_details_el = job_left_col_el.select(":nth-child(4)").children()
        job["desc"] = job_details_el[0].select("p.break").text()
        job["skills"] = job_details_el[0].select("#form span").text()

        job_activity_el = job_details_el[-1]
        job["last_viewed"] = job_activity_el.select("p:contains('Last Viewed')").children(1).text()
        job["proposals"] = job_activity_el.select("p:contains('Proposals')").children(1).number()
        job["interviewing"] = job_activity_el.select("p:contains('Interviewing')").number("(?<=Interviewing: )\d+")

        jobs.append(job)
        time.sleep(1)

        # send_email(url)

start_monitoring()
# write_entries(jobs_list_dict, "jobs.csv")
print("end")
