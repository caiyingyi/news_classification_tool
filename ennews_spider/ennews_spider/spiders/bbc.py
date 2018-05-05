# -*- coding:utf-8 -*-
import scrapy
import time
import datetime
from ..service.html_filter import XssHtml
from ..service.helper import Helper
from ..bloom_filter_redis import bloomfilter


class BBCSpider(scrapy.Spider):
    name = "bbc"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 124,
            'ennews_spider.middlewares.UAPOOLS': 122
        }
    }
    start_urls = ['http://www.bbc.com/news/world',
                  'http://www.bbc.com/news/business',
                  'http://www.bbc.com/news/technology',
                  'http://www.bbc.com/news/science_and_environment',
                  'http://www.bbc.com/news/entertainment_and_arts',
                  'http://www.bbc.com/news/health',
                  ]
    bloom_filter = bloomfilter.BloomFilter(key="bbc")

    def parse(self, response):
        topics = {"technology": "Technology",
                  "science_and_environment": "Technology",
                  "world": "World",
                  "business": "Business",
                  "entertainment_and_arts": "Lifestyle",
                  "health": "Health"}
        topic = topics.get(response.url.split('/')[-1], "")

        articles = response.xpath('//li[@class="links-list__item"]/a/@href').extract() + response.xpath(
            '//a[@class="title-link"]/@href').extract()
        repeat = 0
        for url in articles:
            if repeat > 5:
                print("repeation--OVER")
                return

            if "http" in url or "av" in url:
                continue
            id = "".join(url.split('/')[2:])
            # 判断新闻是否已存在
            item_new = self.bloom_filter.do_filter(id)
            # item_new = True
            if item_new:
                url = "http://www.bbc.com" + url
                yield scrapy.Request(url,
                                     callback=self.parse_article,
                                     meta={"id": id, "topic": topic})
            else:
                repeat += 1
                continue

    def parse_article(self, response):
        try:
            # 普通新闻
            published_at = response.xpath('//li[@class="mini-info-list__item"]/div/@data-seconds').extract_first()
            # 判断是否七天内新闻
            seven_days_ago = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=7)).timetuple()))
            if published_at < seven_days_ago:
                return

            item = dict()
            item["media"] = "bbc"
            item["topic"] = response.meta['topic']
            item['url'] = response.url
            item['id'] = response.meta['id']
            item['created_time'] = int(time.time())
            item['categories'] = ""

            title = response.xpath('//h1[@class="story-body__h1"]/text()').extract_first()
            origin_content = response.xpath('//div[@class="story-body__inner"]').extract_first()

            if published_at and title and origin_content:
                item['keywords'] = response.xpath('//li[@class="tags-list__tags"]/a/text()').extract()

            item['pubilshed_at'] = int(published_at)
            item['title'] = title
            item['origin_content'] = origin_content
            try:
                parser = XssHtml()
                parser.feed(item['origin_content'])
                parser.close()
                item['content'] = parser.getHtml()
            except BaseException:
                item['content'] = item['origin_content']

            item['image_urls'] = Helper.parse_images(item['content'])
            yield item

        except:
            return
