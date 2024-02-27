import scrapy
from scrapy import Selector
import json
from lxml import etree

class BibleSpider(scrapy.Spider):
    name = "Bible"
    start_urls = [
        "https://www.biblica.com/bible/niv/genesis/1/",
                  ]
    file='english_bible_niv.json'
    bible_content = {}
    i = 1
    def parse(self, response):
        selector = Selector(response)
        current_url = response.request.url
        book = current_url.rsplit('/')[-3]
        if book not in self.bible_content:
            self.bible_content[book] = {}
        chapter_num = current_url.rsplit('/')[-2]
        if chapter_num not in self.bible_content[book]:
            self.bible_content[book][chapter_num] = {}
        # content = selector.xpath('//*[contains(@id,"verse-")]/text()')
        # content = selector.xpath('//*[contains(@class,"verse")][sup]')
        content = selector.xpath('//*[contains(@class,"verse")][sup]').extract()
        index_verse_num = []
        for iii,each_ in enumerate(content):
            if len(etree.HTML(each_).xpath('//sup[@class="versenum"]'))!=0:
                index_verse_num.append(iii)
        content_set = []
        last_included = False
        for iii,each_ in enumerate(index_verse_num):
            if each_ != index_verse_num[-1]:
                els = content[each_:index_verse_num[iii+1]]
                if index_verse_num[iii]==index_verse_num[-1]:
                    last_included = True
                text = []
                for el in els:
                    text = text + etree.HTML(el).xpath('//*[@class="verse"]/text()')
                content_set.append(''.join(text).rstrip().lstrip())
            else:
                if not last_included:
                    content_set.append(''.join(etree.HTML(content[-1]).xpath('//*[@class="verse"]/text()')).rstrip().lstrip())
        self.bible_content[book][chapter_num]=dict(zip(range(1,len(content_set)+1),content_set))
        print('Crawling chapter {} of {}'.format(chapter_num,book))
        # self.bible_content[book][chapter_num]=dict(zip(range(1,len(content)+1),[each.get().rstrip().lstrip() for each in content]))
        # self.bible_content[book][chapter_num]=dict(zip(range(1,len(content)+1),[''.join(etree.HTML(each.get()).xpath('//*[@class="verse"]/text()')).rstrip().lstrip() for each in content]))
        next_page = response.xpath('//*[@id="online-bible"]/div[2]/div/div/div/div[4]/a[2]/@href').get()
        self.i=self.i+1
        if self.i==100:
            with open(self.file,'w') as outfile:
                json.dump(self.bible_content,outfile)
                self.i=1
        if next_page!=self.start_urls[0]:
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            with open(self.file,'w') as outfile:
                json.dump(self.bible_content,outfile)


