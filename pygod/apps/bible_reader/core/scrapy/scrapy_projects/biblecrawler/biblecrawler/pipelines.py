# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json

class BiblecrawlerPipeline:
    bible_content = {}
    json_file_name = 'english_bible_niv.json'

    def save_to_json(self):
        with open(self.json_file_name,'w') as file:
            json.dump(self.bible_content,self.json_file_name)

    def process_item(self, item, spider):
        if isinstance(item,BiblecrawlerItem):
            if item['book_name'] not in self.bible_content:
                self.bible_content[item['book_name']]={}
            if item['book_chapter'] not in self.bible_content[item['book_name']]:
                self.bible_content[item['book_name']][item['book_chapter']]={}
            for i,each in enumerate(item['chapter_content']):
                self.bible_content[item['book_name']][item['book_chapter']][str(i+1)] = each
            self.save_to_json()
            print('crawling chapter {} of {} now!'.format(item['book_chapter'],item['book_name']))

        return item
