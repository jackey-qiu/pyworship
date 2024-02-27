import scrapy
from scrapy import Selector
import json
from lxml import etree

class BibleSpider(scrapy.Spider):
    name = "Bible2"
    start_urls = [
        "https://www.biblestudytools.com/nkjv/genesis/1.html",
                  ]
    file='english_bible_NKJV.json'
    bible_content = {}
    i = 1
    def parse(self, response):
        current_url = response.request.url
        next_page = response.xpath('//*[@id="content-column"]/div[3]/div/div[3]/div[1]/div/a[4]/@href').extract()
        book = current_url.rsplit('/')[-2]
        if book not in self.bible_content:
            self.bible_content[book] = {}
        chapter_num = current_url.rsplit('/')[-1].replace('.html','')
        if chapter_num not in self.bible_content[book]:
            self.bible_content[book][chapter_num] = {}
        content_raw = response.xpath('//*[contains(@id,"v-")]').extract()
        content = []
        for each in content_raw:
            text = etree.HTML(each).xpath('//span/text()')
            content.append(' '.join([each_.rstrip().lstrip() for each_ in text]))
        self.bible_content[book][chapter_num]=dict(zip(range(1,len(content)+1),content))
        print('Crawling chapter {} of {}'.format(chapter_num,book))
        self.i=self.i+1
        if self.i==100:
            with open(self.file,'w') as outfile:
                json.dump(self.bible_content,outfile)
                self.i=1
        if len(next_page) == 1:
            yield scrapy.Request(next_page[0], callback=self.parse)
        else:
            with open(self.file,'w') as outfile:
                json.dump(self.bible_content,outfile)


