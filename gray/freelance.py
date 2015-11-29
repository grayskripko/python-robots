import os
import time
import upwork
from gray.common.data_utils import first_match, send_email, parse_number, contains_url, read_list
from gray.common.node_utils import Node, Provider

upwork_job_feed_url = "https://www.upwork.com/find-work-home/"
delay_between_job_feed_refresh_sec = 30
delay_between_requests_sec = 2
stop_skills = ["Internet research", "WordPress", "Telephone Handling"]


def is_attractive_job(job):
    for stop_skill in stop_skills:
        if stop_skill in job["skills"]:
            return False
    if job["stars"] and job["stars"] < 4.6:
        return False

    very_attractive = (job["budget"] and job["budget"] > 200) \
                      or (job["is_hourly"] and "Entry" not in job["budget_level"])
    if very_attractive:
        return True

    attractive_payment = "Entry" not in job["budget_level"] and \
        job["is_hourly"] or (job["budget"] and job["budget"] > 50)
    if not attractive_payment:
        return False
    attractive_competitiveness = job["proposals"] < 10 and job["interviewing"] < 3
    if not attractive_competitiveness:
        return False
    # attractive_job_desc = contains_url(job["desc"])
    return True


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


def get_upwork_job_feed_doc():
    doc = Node(upwork_job_feed_url, Provider.PHANTOMJS)
    doc.select("#login_username").send_keys("grayskripko@gmail.com")
    doc.select("#login_password").send_keys(os.getenv("up") + "#u")
    doc.select("#layout > div.container.ng-scope > div > form").el.submit()
    return doc


def process_job(doc, job_link):
    job = {}
    job["url"] = job_link
    if doc.select("h1:contains('job is private')"):
        job["is_public"] = False
        return job
    else:
        job["is_public"] = True

    job_title_el = doc.select("#layout > .container.ng-scope > .row")
    job_left_col_el = doc.select("#layout > .container.ng-scope > .row:last-child > .col-md-9")
    about_company = doc.select("#layout > .container.ng-scope > .row:last-child > .col-md-3")

    job["title"] = job_title_el.select("h1").text()
    stars_review_popover_el = about_company.select("p:contains('review')").select("*[popover]")
    job["stars"] = stars_review_popover_el.number(pattern="[\d\.]+(?= stars?)", prec=2, attr_name="popover") \
        if stars_review_popover_el else None
    job["stars_reviewers"] = stars_review_popover_el.number(pattern="(?<=based on )\d+", attr_name="popover") \
        if stars_review_popover_el else None
    job["company_since"] = about_company.select(".o-support-info:contains('Since')").text()  ##################################################

    posted_ago_str = job_left_col_el.select("*:nth-child(2)").text()
    if "day" in posted_ago_str:
        sec_time_shift = 24 * 60 * 60
    elif "hour" in posted_ago_str:
        sec_time_shift = parse_number(first_match("\d+", posted_ago_str), default=1) * 60 * 60
    elif "minute" in posted_ago_str:
        sec_time_shift = parse_number(first_match("\d+", posted_ago_str), default=1) * 60
    else:
        print("Rear posted_ago_str value:", posted_ago_str)
        sec_time_shift = 0
    job["posted_time"] = time.time() - sec_time_shift

    price_cell_els = job_left_col_el.select(":nth-child(3)").children()
    job["is_hourly"] = price_cell_els[0].select("strong").text() == "Hourly Job"

    job["budget"] = price_cell_els[1].select("strong").number(pattern="(?=\$)\d+") \
        if len(price_cell_els) == 3 else None
    job["budget_level"] = price_cell_els[-1].select("strong").text(pattern="\w+(?= Level)")

    job_details_el = job_left_col_el.select(":nth-child(4)").children()
    job["desc"] = job_details_el[0].select("p.break").text()
    job["skills"] = job_details_el[0].select("#form span").text()

    job_activity_el = job_details_el[-1]
    job["last_viewed"] = job_activity_el.select("p:contains('Last Viewed')").children(1).text()
    job["proposals"] = job_activity_el.select("p:contains('Proposals')").children(1).number()
    job["interviewing"] = job_activity_el.select("p:contains('Interviewing')").number("(?<=Interviewing: )\d+")
    print(job)
    return job


def actualize_viewed_jobs(viewed_jobs):
    hours_for_marking_expired = 6
    actualization_time_barrier = time.time() - hours_for_marking_expired * 60 * 60
    return list(filter(lambda job: job["posted_time"] > actualization_time_barrier, viewed_jobs))


def send_email_with_attractive_jobs(attractive_jobs):
    msg = "\n".join(list(map(lambda job: str(job["budget"]) + " " + job["url"], attractive_jobs)))
    send_email(msg)


def process_job_feed_list(viewed_jobs):
    viewed_job_links = list(map(lambda job: job["url"], viewed_jobs))
    attractive_jobs = []
    job_links = list(map(lambda node: node.abs_url(upwork_job_feed_url),
                         doc.select_list("#jsJobResults .oVisitedLink")))
    for job_link in job_links:
        if job_link in viewed_job_links:
            continue
        doc.navigate(job_link)
        new_job = process_job(doc, job_link)
        viewed_jobs.append(new_job)
        if is_attractive_job(new_job):
            attractive_jobs.append(new_job)
        time.sleep(delay_between_requests_sec)

    if attractive_jobs:
        send_email_with_attractive_jobs(attractive_jobs)
    return viewed_jobs


doc = get_upwork_job_feed_doc()
prev_attractive_jobs = read_list("")
viewed_jobs = []
i = 0
while True:
    viewed_jobs = actualize_viewed_jobs(viewed_jobs)
    len_viewed_jobs = len(viewed_jobs)
    viewed_jobs = process_job_feed_list(viewed_jobs)
    if len(viewed_jobs) != len_viewed_jobs:
        print(i, len_viewed_jobs, len(viewed_jobs))
    time.sleep(delay_between_job_feed_refresh_sec)
    doc.navigate(upwork_job_feed_url)

# write_entries(jobs_list_dict, "jobs.csv")
print("end")
