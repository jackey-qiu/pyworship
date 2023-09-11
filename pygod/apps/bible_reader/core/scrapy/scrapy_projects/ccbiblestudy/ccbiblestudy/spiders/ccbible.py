# -*- coding: utf-8 -*-
import scrapy
from ccbiblestudy.items import CcbiblestudyItem

class CcbibleSpider(scrapy.Spider):
    name = 'ccbible'
    #allowed_domains = ['www.ccbiblestudy.net/index-S.htm']
    start_urls = ['http://www.ccbiblestudy.net/index-S.htm']
    #66 books in total in Bible
    #which books do you want to crawl?
    bounds_books = [0,66]

    def parse(self, response):
        # all_urls = response.xpath('//*[@href]/@href').extract()
        # all_urls = [response.urljoin(each) for each in all_urls if 'Testament' in each]
        all = response.xpath('//*[contains(@href,"Testament")]')
        all_urls = all.xpath("@href").extract()
        all_books = [''.join(each.xpath('.//text()').extract()) for each in all]
        all_urls = [response.urljoin(each) for each in all_urls if 'Testament' in each]
        bounds = self.bounds_books
        all_books = all_books[bounds[0]:bounds[1]]
        all_urls = all_urls[bounds[0]:bounds[1]]
        for i,each_url in enumerate(all_urls):
            yield scrapy.Request(each_url,callback=self.parse_book_overview,meta = {'book':all_books[i]})

    def parse_book_overview(self,response):
        #book_name = response.xpath('//span/text()')[3].extract()
        book_name = response.meta['book']
        all_urls = response.xpath('//*[@href]/@href').extract()[4:]
        end = None
        if not all_urls[-1].endswith('htm'):
            end = -1
            all_urls = all_urls[0:-1]
        all_chapter_lables = []
        temp = response.xpath('//*[@href]') 
        if end == -1:
            temp = temp[0:-1]
        for each in temp[4:]:
            all_chapter_lables.append(''.join(each.xpath('.//text()').extract()))
        for i,each_url in enumerate(all_urls):
            current_url = response.urljoin(each_url)
            if 'CS' in current_url:
                source_name = 'CS'
            elif 'GS' in current_url:
                source_name = 'GS'
            elif 'IS' in current_url:
                source_name = 'IS'
            elif 'MS' in current_url:
                source_name = 'MS'
            elif 'OS' in current_url:
                source_name = 'OS'
            else:
                source_name = None
            #if all_chapter_lables[i].startswith('第'):
            #    tag = each_url.rsplit('.')[0]
                #'10CS091.htm'-->091
            #    chapter = '第{}章'.format(tag[(tag.index('S')+1):])

            #else:
            chapter = all_chapter_lables[i]

            yield scrapy.Request(current_url,callback = self.parse_chapter_content,meta = {'source_name':source_name,\
                                                                                           'chapter_name':chapter,\
                                                                                           'book_name':book_name})

    def parse_chapter_content(self,response):
        item = CcbiblestudyItem()
        item["source_name"] = response.meta["source_name"]
        item["chapter_name"] = response.meta["chapter_name"]
        item["book_name"] = response.meta["book_name"]
        all_index = range(1,len(response.xpath('//p'))+1)
        content_all = []
        for i in all_index[2:]:
            text_temp = ''.join(response.xpath('//p[{}]//span/text()'.format(i)).extract())
            if text_temp!='':
                content_all.append(text_temp)
        content = '\n'.join(content_all)
        item["chapter_content"] = content
        print('crawling {} of {} now'.format(item['chapter_name'],item['book_name']))
        return item
