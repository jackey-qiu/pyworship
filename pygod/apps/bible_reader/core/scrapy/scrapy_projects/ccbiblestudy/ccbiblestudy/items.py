# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class CcbiblestudyItem(scrapy.Item):
    chapter_content = scrapy.Field()
    chapter_name = scrapy.Field()
    book_name = scrapy.Field()
    source_name = scrapy.Field()