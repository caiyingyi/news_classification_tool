# -*- coding:utf-8 -*-

import scrapy
import time
from ..service.html_filter import XssHtml
from ..bloom_filter_redis import bloomfilter


class UPI(scrapy.Spider):
    name = "upi"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 124,
            'test_newsspider.middlewares.UAPOOLS': 122
        }
    }
    start_urls = ['https://www.upi.com/Sports_News/2018/',
                  'https://www.upi.com/Entertainment_News/2018/',
                  'https://www.upi.com/Health_News/2018/',
                  'https://www.upi.com/Science_News/2018/',
                  'https://www.upi.com/Energy-News/2018/',
                  'https://www.upi.com/Defense-News/2018/',
                  'https://www.upi.com/Sports_News/2017/',
                  'https://www.upi.com/Entertainment_News/2017/',
                  'https://www.upi.com/Health_News/2017/',
                  'https://www.upi.com/Science_News/2017/',
                  'https://www.upi.com/Energy-News/2017/',
                  'https://www.upi.com/Defense-News/2017/',
                  'https://www.upi.com/Sports_News/2016/',
                  'https://www.upi.com/Entertainment_News/2016/',
                  'https://www.upi.com/Health_News/2016/',
                  'https://www.upi.com/Science_News/2016/',
                  'https://www.upi.com/Energy-News/2016/',
                  'https://www.upi.com/Defense-News/2016/',
                  'https://www.upi.com/Sports_News/2015/',
                  'https://www.upi.com/Entertainment_News/2015/',
                  'https://www.upi.com/Health_News/2015/',
                  'https://www.upi.com/Science_News/2015/',
                  'https://www.upi.com/Energy-News/2015/',
                  'https://www.upi.com/Defense-News/2015/']

    bloom_filter = bloomfilter.BloomFilter(key="upi")

    def parse(self, response):
        origin_topic = response.url.split("/")[3]
        topic_dictionary = {"Sports_News": "Sport",
                            "Entertainment_News": "Lifestyle",
                            "Health_News": "Health",
                            "Science_News": "Technology",
                            "Energy-News": "Business",
                            "Defense-News": "World"}
        topic = topic_dictionary[origin_topic]

        articles = response.xpath('//div[@class="upi_item"]')
        for article in articles:
            url = article.xpath('./a/@href').extract_first()
            id = url.split('/')[-2]

            # 判断新闻是否已存在
            item_new = self.bloom_filter.do_filter(id)
            # item_new = True
            if item_new:
                yield scrapy.Request(url,
                                     callback=self.parse_article,
                                     meta={"id": id, "topic": topic})
            else:
                continue

        # next page
        next_page = response.xpath('//div[@id="pn_arw"]//a[text()="Next"]/@href').extract_first()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse)

    def parse_article(self, response):
        try:
            item = dict()
            item["url"] = response.url
            item["id"] = response.meta["id"]
            item['created_time'] = int(time.time())
            item['categories'] = ""
            item["media"] = "UPI"
            item["topic"] = response.meta["topic"]

            keywords = response.xpath('//div[@class="breadcrumb grey"]/a[3]/text()').extract_first()
            if keywords:
                item['keywords'] = keywords
            else:
                item['keywords'] = response.xpath('//div[@class="breadcrumb grey"]/a[2]/text()').extract_first()

            item["title"] = response.xpath('//h1[@class="st_headline title"]/text()').extract_first()

            published_at = response.xpath('//meta[@itemprop="datePublished"]/@content').extract_first()
            if published_at:
                published_at = published_at.split("T")[0]
                try:
                    item['published_at'] = int(time.mktime(time.strptime(str(published_at), "%Y-%m-%d")))
                except:
                    item['published_at'] = int(time.time())
            else:
                item['published_at'] = int(time.time())

            item['origin_content'] = response.xpath('//article[@itemprop="articleBody"]').extract_first()
            try:
                parser = XssHtml()
                parser.feed(item['origin_content'])
                parser.close()
                item['content'] = parser.getHtml()
            except BaseException:
                item['content'] = item['origin_content']

            image_urls = response.xpath('//div[@class="ph_c"]/div[@class="img"]/img/@src').extract()
            if image_urls:
                item['image_urls'] = image_urls
            else:
                item['image_urls'] = []

            yield item


        except:
            return
