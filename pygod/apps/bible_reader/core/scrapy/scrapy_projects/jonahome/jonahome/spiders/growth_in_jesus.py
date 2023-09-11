import scrapy
from jonahome.items import JonahomeItem


class GrowthInJesusSpider(scrapy.Spider):
    name = 'growth_in_jesus'
    # allowed_domains = ['http://www.jonahome.net']
    start_urls = ['http://www.jonahome.net/files/zjdlzj/right.htm']

    def parse(self, response):
        all_urls = response.xpath('//*[@href]/@href').extract()
        all_chapters = response.xpath('//*[@href]/text()').extract()
        self.all_chapters = all_chapters
        print(all_chapters)
        all_urls.pop()
        all_chapters.pop()
        for i,each_url in enumerate(all_urls):
            print('sensor',response.urljoin(each_url))
            yield scrapy.Request(response.urljoin(each_url),callback=self.parse_chapter_content,meta = {'book':all_chapters[i]})

    def parse_chapter_content(self, response):
        print('sensor',response.url)
        text = ''.join(response.xpath('//text()').extract())
        # print(text)
        item = JonahomeItem()
        item['chapter_name'] = response.meta['book']
        item['chapter_content'] = text
        print('crawling {} now'.format(item['chapter_name']))
        return item
