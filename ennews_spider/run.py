# -*- coding:utf-8 -*-

from scrapy import cmdline

if __name__ == '__main__':
    # spiders_names = ["bbc", "foxnews", "news_asia", "newsweek", "upi"]
    name = "upi"
    cmdline.execute(("scrapy crawl %s" % name).split())
