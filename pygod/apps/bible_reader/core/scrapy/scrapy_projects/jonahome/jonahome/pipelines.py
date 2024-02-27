# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json

class JonahomePipeline:

    def __init__(self):
        self.books = {}
        self.path = '/Users/canrong/apps/Bible_Reader/scrapy_projects/jonahome/jonahome/在基督里长进_2.json'

    def process_item(self, item, spider):
        self.books[item['chapter_name']] = item['chapter_content']

    def close_spider(self,spider):
        all_chapters_in_order = spider.all_chapters
        books = {}
        for each in all_chapters_in_order:
            books[each] = self.books[each]
        with open(self.path,'w') as outfile:
             json.dump(self.books,outfile)
