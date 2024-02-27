# -*- coding: utf-8 -*-
import scrapy
from desertscripture.items import DesertscriptureItem

class DesertscriptureSpider(scrapy.Spider):
    name = 'desertscripture'
    #allowed_domains = ['www.ccbiblestudy.net/index-S.htm']
    start_urls = ['https://www.24en.com/novel/religion/streams-in-the-desert.html']

    def parse(self, response):
        # all_urls = response.xpath('//*[@href]/@href').extract()
        # all_urls = [response.urljoin(each) for each in all_urls if 'Testament' in each]
        all_urls = response.xpath('/html/body/div[2]/div[4]/div[1]/div[2]/div/ul/li/a/@href').extract()
        for i,each_url in enumerate(all_urls):
            yield scrapy.Request(each_url,callback=self.parse_book_content,meta = {'book_index':i+1})

    def parse_book_content(self,response):
        item = DesertscriptureItem()
        eng = response.xpath('/html/body/div[2]/div[4]/div/div[4]/div[1]/p/text()').extract()
        cn = response.xpath('/html/body/div[2]/div[4]/div/div[4]/div[2]/p/text()').extract()
        eng =['    '+each for each in eng]
        cn =['    '+each for each in cn]
        id = response.meta["book_index"]
        item['eng'] = '\n'.join(eng)
        item['cn'] = '\n'.join(cn)
        item['id'] = id
        print('crawling {} now'.format(id))
        return item
