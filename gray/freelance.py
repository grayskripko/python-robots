import os
import time
import upwork
from gray.common.data_utils import first_match, send_email, parse_number, contains_url, read_list, write_list, \
    parse_date
from gray.common.node_utils import Node, Provider

upwork_job_feed_url = "https://www.upwork.com/find-work-home/"
prev_attractive_file_name = "upwork/prev_attractive.csv"
delay_between_job_feed_refresh_sec = 30
delay_between_requests_sec = 2
stop_skills = ["Internet research", "WordPress", "Telephone Handling"]


def get_upwork_job_feed_doc():
    doc = Node(upwork_job_feed_url, Provider.PHANTOMJS)
    doc.select("#login_username").send_keys("grayskripko@gmail.com")
    doc.select("#login_password").send_keys(os.getenv("up") + "#u")
    doc.select("#layout > div.container.ng-scope > div > form").el.submit()
    return doc


def remove_old_viewed_jobs(viewed_jobs):
    hours_for_marking_expired = 6
    actualization_time_barrier = time.time() - hours_for_marking_expired * 60 * 60
    return list(filter(lambda job: job["posted_time"] > actualization_time_barrier, viewed_jobs))


def send_email_with_attractive_jobs(attractive_jobs):
    msg = "\n".join(list(map(lambda job: str(job["budget"]) + " " + job["url"], attractive_jobs)))
    send_email(msg)


def fill_shallow_job(doc, job):
    if doc.select("h1:contains('job is private')"):
        job["is_public"] = False
        return job
    else:
        job["is_public"] = True
        job["is_shallow"] = False

    job_left_col_el = doc.select("#layout > .container.ng-scope > .row:last-child > .col-md-9")
    job_activity_el = job_left_col_el.select(":nth-child(4)").children()[-1]
    job["last_viewed"] = job_activity_el.select("p:contains('Last Viewed')").children(1).text()
    job["proposals"] = job_activity_el.select("p:contains('Proposals')").children(1).number()
    job["interviewing"] = job_activity_el.select("p:contains('Interviewing')").number("(?<=Interviewing: )\d+")
    print("\n", job)
    return job


def get_shallow_jobs(doc, viewed_job_urls):
    shallow_job_els = doc.select_list("#jsJobResults > article.oMed")
    shallow_jobs = []
    for shallow_job_el in shallow_job_els:
        job = {}
        title_el = shallow_job_el.select("h1 > a")
        job["url"] = title_el.abs_url(upwork_job_feed_url)
        if job["url"] in viewed_job_urls:
            continue
        job["title"] = title_el.text()

        price_el = shallow_job_el.select(".oSupportInfo")
        job["is_hourly"] = price_el.select("strong").text() == "Hourly"
        job["budget_level"] = price_el.select("#jsTier").text("\S+")
        job["budget"] = price_el.select(".jsBudget").number("(?<=\$)\d+")
        job["time_posted"] = price_el.select(".jsAutoRelativeTime").date(False, "\d+", "data-timestamp")

        hidden_desc_el = shallow_job_el.select(".oDescription > .jsFull")
        job["desc"] = hidden_desc_el.text() if hidden_desc_el.text() else shallow_job_el.select(".oDescription").text()

        job["company_since"] = shallow_job_el.select(".oSpendIcon").date(True, "(?<=Member Since )\S+", "title")
        job["stars"] = shallow_job_el.select(".oStarsContainer").number(pattern="\S+(?= star)", attr_name="data-content")
        job["skills"] = shallow_job_el.select_list(".oSkills > a").texts()
        shallow_jobs.append(job)
    return shallow_jobs


def process_job_feed_list(doc, viewed_job_urls):
    attractive_jobs = []
    shallow_jobs = get_shallow_jobs(doc, viewed_job_urls)
    new_shallow_jobs = []

    for shallow_job in shallow_jobs:
        if shallow_job["url"] in viewed_job_urls:
            continue
        new_shallow_jobs.append(shallow_job)
        if not is_attractive_job(shallow_job, is_shallow=True):
            continue
        doc.navigate(shallow_job["url"])
        new_filled_job = fill_shallow_job(doc, shallow_job)
        if is_attractive_job(new_filled_job, is_shallow=False):
            attractive_jobs.append(new_filled_job)
        time.sleep(delay_between_requests_sec)

    if attractive_jobs:
        send_email_with_attractive_jobs(attractive_jobs)
        write_list(list(map(lambda job: job["url"], attractive_jobs)), prev_attractive_file_name, append=True)
    return new_shallow_jobs


def is_attractive_job(job, is_shallow):
    if is_shallow:
        for stop_skill in stop_skills:
            if stop_skill in job["skills"]:
                print(job["url"], "is_shallow for stop_skill:", stop_skill)
                return False
        if job["stars"] and job["stars"] < 4.5:
            print(job["url"], "is_shallow for low stars:", job["stars"])
            return False
        is_attractive_payment = "Entry" not in job["budget_level"] and \
            job["is_hourly"] or (job["budget"] and job["budget"] > 50)
        if not is_attractive_payment:
            print(job["url"], "is_shallow for low payment")
        return is_attractive_payment

    is_very_attractive_payment = (job["budget"] and job["budget"] >= 200) \
                      or (job["is_hourly"] and "Entry" not in job["budget_level"])
    is_attractive_competitiveness = job["proposals"] < 10 and job["interviewing"] < 3
    if is_very_attractive_payment or is_attractive_competitiveness:
        if is_very_attractive_payment:
            print(job["url"], "selected for very_attractive_payment")
        else:
            print(job["url"], "selected for attractive_competitiveness")
    return is_very_attractive_payment or is_attractive_competitiveness


def main():
    doc = get_upwork_job_feed_doc()
    prev_attractive_job_urls = read_list(prev_attractive_file_name)
    viewed_jobs = list(map(lambda job_url: {"url": job_url, "is_prev_attractive": True}, prev_attractive_job_urls))
    i = 0

    while True:
        view_job_urls = list(map(lambda job: job["url"], viewed_jobs))
        viewed_jobs += process_job_feed_list(doc, view_job_urls)
        print("Monitoring iteration: [{0}], len(viewed_jobs): [{1}]".format(i, len(viewed_jobs)))
        time.sleep(delay_between_job_feed_refresh_sec)
        doc.navigate(upwork_job_feed_url)
        i += 1
    # write_entries(jobs_list_dict, "jobs.csv")
    print("end")


if __name__ == '__main__':
    main()
