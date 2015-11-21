import re

import bs4


class Node:
    def __init__(self, dom, is_document=True):
        if is_document:
            self.node = bs4.BeautifulSoup(open(dom, encoding="utf-8"))
        else:
            self.node = dom

    def select(self, css_path):
        results = self.node.select(css_path)
        return Node(results[0], is_document=False) if results else None

    def select_list(self, css_path):
        return list(map(lambda el: Node(el, is_document=False), self.node.select(css_path)))

    def text(self):
        result = re.sub("\t", "", self.node.get_text())
        result = re.sub("\n{2,}", "\n", result).strip()
        result = re.sub("\n", " | ", result)
        result = re.sub(" {2,}", " ", result)
        return result

    def attr(self, attr_name):
        return self.node.attrs.get(attr_name)
