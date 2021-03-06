# -*- coding:utf-8 -*-
import scrapy
import time
import datetime
from ..service.html_filter import XssHtml
from ..bloom_filter_redis import bloomfilter


class NewsAsiaSpider(scrapy.Spider):
    name = "news_asia"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 124,
            'ennews_spider.middlewares.UAPOOLS': 122
        }
    }
    start_urls = ['https://www.channelnewsasia.com/archives/8395986/news?channelId=7469166']
    bloom_filter = bloomfilter.BloomFilter(key="news_asia")
    early = 0

    def parse(self, response):
        topics = ["World", "Sport", "Business", "Technology", "Lifestyle", "Health"]
        articles = response.xpath('//ol[@class="result-section__list"]/li[@class="result-section__list-item"]')

        repeat = 0
        for item in articles:
            if repeat > 5:
                print("repeation--OVER")
                return
            if self.early > 5:
                print("early--OVER")
                return

            topic = item.xpath('.//a[@class="teaser__category"]/text()').extract_first()
            if topic not in topics:
                continue
            else:
                url = item.xpath('.//a[@class="teaser__title"]/@href').extract_first()
                id = url.split("-")[-1]

                # 判断新闻是否已存在
                item_new = self.bloom_filter.do_filter(id)
                # item_new = True
                if item_new:
                    url = "https://www.channelnewsasia.com" + url
                    yield scrapy.Request(url,
                                         callback=self.parse_article,
                                         meta={"id": id, "topic": topic})
                else:
                    repeat += 1
                    continue
        # 翻页
        next_page = response.xpath('//a[@class="pagination__link is-next"]/@href').extract_first()
        print("next page")
        if next_page:
            next_url = "https://www.channelnewsasia.com" + next_page
            yield scrapy.Request(next_url, callback=self.parse)

    def parse_article(self, response):
        try:
            # 判断是否七天内新闻
            published_at = response.xpath('//meta[@name="cXenseParse:recs:publishtime"]/@content').extract_first()
            if published_at:
                published_at = published_at.split("T")[0]
                try:
                    published_at = time.strptime(str(published_at), "%Y-%m-%d")
                    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).timetuple()
                    if published_at <= seven_days_ago:
                        self.early += 1
                        return
                    else:
                        published_at = int(time.mktime(published_at))
                except:
                    published_at = int(time.time())
            else:
                published_at = int(time.time())

            item = dict()
            item['published_at'] = published_at
            item['url'] = response.url
            item["id"] = response.meta["id"]
            item['created_time'] = int(time.time())
            item['categories'] = ""
            item['topic'] = response.meta["topic"]
            item['image_urls'] = []
            item['media'] = "NewsAsia"

            item['title'] = response.xpath('//h1[@class="article__title"]/text()').extract_first()
            item['keywords'] = response.xpath(
                '//div[@class="c-link-list--tag-list"]//a[@class="link-list__link"]/text()').extract()

            item['origin_content'] = response.xpath('//div[@class="c-rte--article"]').extract_first()
            try:
                parser = XssHtml()
                parser.feed(item['origin_content'])
                parser.close()
                item['content'] = parser.getHtml()
            except BaseException:
                item['content'] = item['origin_content']

            yield item

        except:
            return
