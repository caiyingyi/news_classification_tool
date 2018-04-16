# -*- coding:utf-8 -*-

from scrapy import cmdline

if __name__ == '__main__':
    name = "upi"
    cmdline.execute(("scrapy crawl %s" % name).split())
