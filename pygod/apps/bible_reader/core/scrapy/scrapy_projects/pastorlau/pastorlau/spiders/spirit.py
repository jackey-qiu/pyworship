# -*- coding: utf-8 -*-
import scrapy
from .langconv import *
import json

convert = Converter('zh-hans').convert

class SpiritSpider(scrapy.Spider):
    name = 'spirit'
    #start_urls = ['http://www.pastorlau.org/pages/devotion.html']
    start_urls= ['http://www.pastorlau.org/pages/special.html']
    start_url_temp = ''
    spirit_book = {}
    file_name = '专题研究——刘锐光牧师释经序列.json'
    title = ''
    i=1

    def parse(self,response):
        # start_index = 25
        # urls = response.xpath('//*[@href]/@href').extract()[start_index:start_index+1]
        # books = response.xpath('//*[@href]/text()').extract()[start_index:start_index+1]
        urls = response.xpath('//*[@href]/@href').extract()
        books = response.xpath('//*[@href]/text()').extract()
        for i, each in enumerate(urls):
            current_url = response.urljoin(each)
            # self.file_name = '{}--刘锐光牧师解经序列.json'.format(convert(books[i].rstrip().lstrip()))
            title = (convert(books[i].rstrip().lstrip()))
            # self.spirit_book = {}
            self.i=self.i+1
            print(i,current_url,title)
            # yield scrapy.Request(current_url,self.parse_first)
            yield scrapy.Request(current_url,callback = self.parse_content_single_page, meta = {'title':title})

    def parse_content_single_page(self, response):
        content = response.xpath('//body').xpath('.//text()').extract()
        title = response.meta['title']
        content = ''.join(content)
        self.spirit_book[title] = convert(content)
        with open(self.file_name,'w') as outfile:
            json.dump(self.spirit_book,outfile)
        # print('crawling {}'.format(self.title))


class SpiritSpider2(scrapy.Spider):
    name = 'spirit2'
    allowed_domains = ['http://www.pastorlau.org/pages/devotion.html']
    top_url = 'http://www.pastorlau.org/pages/devotion'
    start_urls = ['http://http://www.pastorlau.org/pages/devotion.html/']
    spirit_book = {}


    def parse(self, response):
        urls = response.xpath('//*[@href]/@href').extract()
        titles = response.xpath('//*[@href]/text()').extract()
        for i,url in enumerate(urls):
            self.spirit_book[convert(titles[i])] = {}
            url_full = '/'.join([self.top_url,url.rsplit('/')[-1]])
            yield scrapy.Request(url_full,callback = self.parse_chapter_overview)

    def parse_chapter_overview(self,response):
        urls = response.xpath('//*[@href]/@href').extract()
        titles = response.xpath('//*[@href]/text()').extract()
        current_book = convert(response.xpath('/html/body/b/font/font/text()').extract()[0].rstrip().lstrip())
        for i,url in enumerate(urls):
            self.spirit_book[current_book][convert(titles[i])] = {}
            url_full = '/'.join([self.top_url,url])
            yield scrapy.Request(url_full,callback = self.parse_chapter_contents)

    def parse_chapter_contents(self,response):
        pass
    def parse_chapter_overview(self,response):
        urls = response.xpath('//*[@href]/@href').extract()
        titles = response.xpath('//*[@href]/text()').extract()

    def parse_first(self,response):
        urls = response.xpath('//*[@href]/@href').extract()
        if len(urls) == 0:
            self.start_url_temp = response.url
        else:
            self.start_url_temp = response.urljoin(urls[0])
        yield scrapy.Request(self.start_url_temp,self.parse_content)


    def parse_content(self, response):
        urls = response.xpath('//*[@href]/@href').extract()
        urls = [each for each in urls if each.endswith('.html')]
        next_link = None
        if len(urls)==0:
            pass
        elif len(urls)==2 or (response.url==self.start_url_temp):
            next_link = response.urljoin(urls[-1])
        else:
            pass
        print('next_link',next_link)
        # titles =[each.rstrip().lstrip() for each in response.xpath('//font/b/text()').extract()]
        title = '第{}讲'.format(self.i)
        # for each in titles:
            # if each !='':
                # title= convert(each.rstrip().lstrip())
                # break

        # content = response.xpath('//p').xpath('.//text()').extract()
        content = response.xpath('//body').xpath('.//text()').extract()
        """
        if self.i<=4:
            for each in content:
                if each.rstrip()!='':
                    title = convert(each)
                    break
                else:
                    pass
        else:
            title = convert(response.xpath('//b').xpath('.//text()').extract()[0])
        """
        content = ''.join(content)

        self.spirit_book[title] = convert(content)
        self.i = self.i+1
        if next_link!=None:
            print('crawling {}'.format(title))
            yield scrapy.Request(next_link,callback = self.parse_content)
        else:
            with open(self.file_name,'w') as outfile:
                json.dump(self.spirit_book,outfile)
