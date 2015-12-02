import os

import upwork

from gray.common.data_utils import first_match
from gray.common.node_utils import Node


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

