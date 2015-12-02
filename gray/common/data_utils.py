import pandas as pd
import os
import re
import sys
import smtplib
from dateutil.parser import parse

import time


def first_match(pattern, string, safe=True, strip=True):
    try:
        results = re.search(pattern, string, flags=re.MULTILINE | re.DOTALL)
        result = results.group(0) if results else ""
        return result.strip() if strip else result
    except Exception as ex:
        if safe:
            return ""
        else:
            raise ex


def clear_text(string):
    result = re.sub("\t", "", string)
    result = re.sub("\n{2,}", "\n", result).strip()
    result = re.sub("\n", "|| ", result)
    result = re.sub(" {2,}", " ", result)
    return result


def parse_number(string, round_precision=0, default=None, safe=True):
    try:
        if "." not in string:
            return int(string)
        parsed_float = float(string)
        if round_precision is None:
            return parsed_float
        rounded_float = round(float(parsed_float), round_precision)
        return int(rounded_float) if int(rounded_float) == rounded_float else rounded_float
    except Exception as ex:
        if safe:
            return default
        else:
            raise ex


def parse_date(string):
    return parse(string)


def contains_url(string):
    return first_match("(?i)\Wcom\W|http|www", string) != ""


def inline_print(string, sep=" "):
    if isinstance(string, int):
        string = str(string)
    print(string, end=sep)
    sys.stdout.flush()


def generate_full_file_name(file_name):
    return os.getenv("OUT") + file_name + ("" if "." in file_name else ".csv")


def write_entries(dict_list, file_name, id_column=None):
    if not dict_list:
        print("Empty dict_list")
        return
    dict_list = [{k: re.sub("(\r?\n)+", "|| ", str(v)) for k, v in dict.items()} for dict in dict_list]
    df = pd.DataFrame(dict_list)
    if id_column:
        df.index = df[id_column]

    full_file_name = generate_full_file_name(file_name)
    df.to_csv(full_file_name)
    df.to_excel(re.sub("\.csv", ".xlsx", full_file_name))


def write_list(lst, file_name, append=False):
    full_file_name = generate_full_file_name(file_name)
    if append:
        with open(full_file_name, 'a') as stream:
            pd.DataFrame(lst).to_csv(stream, index=False, header=False)
    else:
        pd.DataFrame(lst).to_csv(full_file_name, index=False, header=False)


def read_list(file_name):
    full_file_name = generate_full_file_name(file_name)
    if not os.path.exists(full_file_name) or os.stat(full_file_name).st_size == 0:
        return []
    return pd.read_csv(full_file_name, header=None)[0].tolist()


def send_email(body, subject="Upwork monitor", recipient=os.getenv("email")):
    gmail_user = os.getenv("email")
    gmail_pwd = os.getenv("up") + "#g"
    TO = recipient if type(recipient) is list else [recipient]
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s""" % (os.getenv("email"), ", ".join(TO), subject, body)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(os.getenv("email"), TO, message)
        server.close()
    except:
        print("failed to send mail")


def time_measure(msg, start_time, precision=0):
    duration = str(round(time.time() - start_time, precision)) if precision else str(round(time.time() - start_time))
    print("{0}: [{1}] sec".format(msg, duration))


def get_domain(url):
    return first_match(".+?\.[^/]*", url, safe=False, strip=False)  # or .+?\..*(?=/)
