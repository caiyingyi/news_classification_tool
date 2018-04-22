# -*- coding:utf-8 -*-

from scrapy import cmdline

if __name__ == '__main__':
    name = "bbc"
    cmdline.execute(("scrapy crawl %s" % name).split())
