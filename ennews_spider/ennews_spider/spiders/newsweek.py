# -*- coding:utf-8 -*-
import scrapy
import time
from ..service.html_filter import XssHtml
from ..bloom_filter_redis import bloomfilter


class NewsWeekSpider(scrapy.Spider):
    name = "newsweek"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 124,
            'ennews_spider.middlewares.UAPOOLS': 122
        }
    }
    start_urls = ['http://www.newsweek.com/newsfeed']
    bloom_filter = bloomfilter.BloomFilter(key="newsweek")

    def parse(self, response):
        topics = {"Tech & Science": "Technology",
                  "World": "World",
                  "Sports": "Sport",
                  "Culture": "Lifestyle",
                  "Health": "Health",
                  "Business": "Business"}
        articles = response.xpath('//div[@class="archive-list"]/article[@class="flex-sm"]')
        for item in articles:
            topic = item.xpath('.//div[@class="category"]/a/text()').extract_first()
            if topic not in topics:
                continue
            else:
                url = item.xpath('.//h3/a/@href').extract_first()
                id = url.split("-")[-1]

                # 判断新闻是否已存在
                item_new = self.bloom_filter.do_filter(id)
                # item_new = True
                if item_new:
                    url = "http://www.newsweek.com" + url
                    yield scrapy.Request(url,
                                         callback=self.parse_article,
                                         meta={"id": id, "topic": topics[topic]})
                else:
                    continue

        # 翻页
        next_page = response.xpath('//li[@class="pager-next last"]/a/@href').extract_first()
        print("翻页")
        if next_page:
            next_url = "http://www.newsweek.com" + next_page
            yield scrapy.Request(next_url, callback=self.parse)

    def parse_article(self, response):
        try:
            item = dict()
            item["url"] = response.url
            item["id"] = response.meta["id"]
            item['created_time'] = int(time.time())
            item['categories'] = ""
            item["media"] = "NewsWeek"
            item["topic"] = response.meta["topic"]

            item["keywords"] = response.xpath('//div[@class="filed-under flex-xs flex-wrap ai-c"]/a/text()').extract()
            item["title"] = response.xpath('//header[@class="article-header"]/h1/text()').extract_first()

            published_at = response.xpath('//time[@itemprop="datePublished"]/@datetime').extract_first()
            if published_at:
                published_at = published_at.split("T")[0]
                try:
                    item['published_at'] = int(time.mktime(time.strptime(str(published_at), "%Y-%m-%d")))
                except:
                    item['published_at'] = int(time.time())
            else:
                item['published_at'] = int(time.time())

            item['origin_content'] = response.xpath('//div[@itemprop="articleBody"]').extract_first()
            try:
                parser = XssHtml()
                parser.feed(item['origin_content'])
                parser.close()
                item['content'] = parser.getHtml()
            except BaseException:
                item['content'] = item['origin_content']

            item['image_urls'] = []
            yield item

        except:
            return
