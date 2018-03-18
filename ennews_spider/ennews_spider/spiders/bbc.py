# -*- coding:utf-8 -*-
import scrapy
import time
from ..service.html_filter import XssHtml
from ..service.helper import Helper
from ..bloom_filter_redis import bloomfilter


class BBCSpider(scrapy.Spider):
    name = "bbc"
    custom_settings = {}
    start_urls = ['http://www.bbc.com/news']
    bloom_filter = bloomfilter.BloomFilter(key="bbc")

    def parse(self, response):

        articles = response.xpath(
            '//a[@class="gs-c-promo-heading nw-o-link-split__anchor gs-o-faux-block-link__overlay-link gel-pica-bold"]/@href').extract()
        for url in articles:
            if "http" in url:
                continue
            id = "".join(url.split('/')[2:])
            # 判断新闻是否已存在
            item_new = self.bloom_filter.do_filter(id)
            print "新闻是新的" + str(item_new)
            if not item_new:
                continue
            else:
                url = "http://www.bbc.com" + url
                yield scrapy.Request(url,
                                     callback=self.parse_article,
                                     meta={"id": id})

    def parse_article(self, response):
        try:
            item = dict()
            item['url'] = response.url
            item['id'] = response.meta['id']
            item['created_time'] = int(time.time())
            item['categories'] = ""

            # 普通新闻
            published_at = response.xpath('//li[@class="mini-info-list__item"]/div/@data-seconds').extract_first()
            title = response.xpath('//h1[@class="story-body__h1"]/text()').extract_first()
            origin_content = response.xpath('//div[@class="story-body__inner"]').extract_first()

            if published_at and title and origin_content:
                item['keywords'] = response.xpath('//li[@class="tags-list__tags"]/a/text()').extract()
            else:
                # 体育新闻
                published_at = response.xpath(
                    '//li[@class="story-info__item story-info__item--time"]/span/time/@data-timestamp').extract_first()
                title = response.xpath('//h1[@class="story-headline gel-trafalgar-bold "]/text()').extract_first()
                origin_content = response.xpath('//div[@id="story-body"]').extract_first()

                if published_at and title and origin_content:
                    item['keywords'] = response.xpath(
                        '//div[@class="story-info__list"]/ul//span[@class="section-tag--nested-link gel-brevier  section-tag"]/a/text()').extract()
                else:
                    return

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
