import pandas as pd
import os
import re
import sys


def first_match(pattern, string, safe=True, strip=True):
    try:
        result = re.search(pattern, string, flags=re.MULTILINE | re.DOTALL).group(0)
        return result.strip() if strip else result
    except Exception as ex:
        if safe:
            return ""
        else:
            raise ex


def parse_float(string, round_precision=None, safe=True):
    try:
        parsed_float = float(string)
        if round_precision:
            return round(float(parsed_float), round_precision)
    except Exception as ex:
        if safe:
            return ""
        else:
            raise ex


def inline_print(string, sep=" "):
    if isinstance(string, int):
        string = str(string)
    print(string, end=sep)
    sys.stdout.flush()


# def __write_entries__(dict_list, file_name, col_names, new_line_alt="|| "):
#     with open(os.environ['OUT'] + file_name, 'w', newline='', encoding='utf-8') as stream:
#         dict_writer = csv.DictWriter(stream, col_names)
#         dict_writer.writeheader()
#         # dict_writer.writerow({k: v.encode('utf8') for k, v in dict_list.items()})
#         dict_writer.writerows(dict_list)


def write_entries(dict_list, file_name):
    dict_list = [{k: re.sub("(\r?\n)+", "|| ", str(v)) for k, v in dict.items()} for dict in dict_list]
    df = pd.DataFrame(dict_list, )
    df.index = df["id"]
    df.to_csv(os.getenv("OUT") + file_name)
    # predicted_df = pd.DataFrame(Y_pred, index=np.arange(1, X_pred.shape[0] + 1), columns=["too_much"])
    # predicted_df.to_csv(_data_path + file_name, index_label="id")

    # if col_names is None:
    #     col_names = dict_list[0].keys()
    # dict_list = [{k: re.sub("\r?\n", "|| ", str(v)) for k, v in dict.items()} for dict in dict_list]
    # file_name = str(file_name) if not isinstance(file_name, str) else file_name
    # if not file_name.endswith(".csv"):
    #     if "." in file_name:
    #         file_name = input("Bad file_name for saving as csv file. Type new: ")
    #     else:
    #         file_name += ".csv"
    #
    # __write_entries__(dict_list, file_name, col_names)
    #
    # if len(dict_list) > 50000:
    #     answer = input("len(dict_list) = [{}]. Press [1] for skipping searching of duplicates:".format(len(dict_list)))
    #     if answer == "1":
    #         return
    #     answer = input("Are you sure? [Press 1 for skipping]:")
    #     if answer == "1":
    #         return
    #
    # dict_list_wo_duplicates = []
    # for dict_el in dict_list:
    #     if dict_el not in dict_list_wo_duplicates:
    #         dict_list_wo_duplicates.append(dict_el)
    #
    # if len(dict_list) != len(dict_list_wo_duplicates):
    #     print("\ncount of duplicates: " + str(len(dict_list) - len(dict_list_wo_duplicates)))
    #     __write_entries__(dict_list_wo_duplicates, "no_duplicates_" + file_name, col_names)
