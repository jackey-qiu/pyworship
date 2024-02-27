# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os,json


class DesertscripturePipeline:
    def __init__(self):
        self.book = {}
        self.path = '/Users/canrong/apps/Bible_Reader/scrapy_projects/desertscripture/desertscripture.json'

    def process_item(self, item, spider):
        id = item['id']
        eng = item['eng']
        cn = item['cn']
        self.book[str(id)+'_eng'] = eng
        self.book[str(id)+'_cn'] = cn
        return item

    def close_spider(self,spider):
        with open(self.path,'w') as outfile:
            json.dump(self.book,outfile)
