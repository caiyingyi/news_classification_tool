# -*- coding:utf-8 -*-

from scrapy import cmdline

if __name__ == '__main__':
    name = ["bbc", "foxnews", "news_asia", "newsweek", "upi"]
    for one in name:
        cmdline.execute(("scrapy crawl %s" % one).split())
