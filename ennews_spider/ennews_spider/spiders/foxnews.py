# -*- coding:utf-8 -*-
import scrapy
import time
import datetime
from ..service.html_filter import XssHtml
from ..bloom_filter_redis import bloomfilter
from ..service.helper import Helper


class FoxNewsSpider(scrapy.Spider):
    name = "foxnews"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 124,
            'ennews_spider.middlewares.UAPOOLS': 122
        }
    }
    start_urls = ['http://www.foxnews.com/world.html',
                  'http://www.foxnews.com/politics.html',
                  'http://www.foxnews.com/entertainment.html',
                  'http://www.foxnews.com/lifestyle.html',
                  'http://www.foxnews.com/health.html',
                  'http://www.foxnews.com/science.html',
                  'http://www.foxnews.com/tech.html']
    bloom_filter = bloomfilter.BloomFilter(key="foxnews")

    def parse(self, response):
        topics = {"science": "Technology",
                  "tech": "Technology",
                  "world": "World",
                  "politics": "World",
                  "entertainment": "Lifestyle",
                  "lifestyle": "Lifestyle",
                  "health": "Health"}
        topic = topics.get(response.url.split('/')[-1].split('.')[0], "")

        articles = response.xpath('//h2[@class="title"]/a/@href').extract() + response.xpath(
            '//h4[@class="title"]/a/@href').extract() + response.xpath(
            '//h5[@class="title"]/a/@href').extract()

        repeat = 0
        for article in articles:
            if repeat > 5:
                print("repetion--OVER")
                return
            if "http" not in article:
                id = article.split('/')[-1].split('.')[0]

                # 判断新闻是否已存在
                item_new = self.bloom_filter.do_filter(id)
                # item_new = True
                if item_new:
                    url = "http://www.foxnews.com" + article
                    yield scrapy.Request(url,
                                         callback=self.parse_article,
                                         meta={"id": id, "topic": topic})
                else:
                    repeat += 1
                    continue

    def parse_article(self, response):
        try:
            # 判断是否七天内的新闻
            published_at = response.xpath('//div[@class="article-date"]/time/@data-time-published').extract_first()
            if published_at:
                published_at = published_at.split("T")[0]
                try:
                    published_at = time.strptime(str(published_at), "%Y-%m-%d")
                    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).timetuple()
                    if published_at < seven_days_ago:
                        return
                    else:
                        published_at = int(time.mktime(published_at))
                except:
                    published_at = int(time.time())
            else:
                published_at = int(time.time())

            keywords = response.xpath('//div[@class="eyebrow"]/a/text()').extract()
            if not keywords:
                return
            else:
                item = dict()
                item['keywords'] = keywords
                item['published_at'] = published_at

                item["url"] = response.url
                item["id"] = response.meta["id"]
                item['created_time'] = int(time.time())
                item['categories'] = ""
                item["media"] = "FoxNews"
                item["topic"] = response.meta["topic"]

                item['title'] = response.xpath('//h1[contains(@class,"headline")]/text()').extract_first()

                item['origin_content'] = response.xpath('//div[@class="article-content"]').extract_first()
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
