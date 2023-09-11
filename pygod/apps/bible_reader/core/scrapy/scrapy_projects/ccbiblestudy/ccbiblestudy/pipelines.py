# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os,json

class CcbiblestudyPipeline:
    def __init__(self):
        self.CS = {}
        self.GS = {}
        self.IS = {}
        self.MS = {}
        self.OS = {}

    def process_item(self, item, spider):
        source = item['source_name']
        book = item['book_name']
        chapter_number = item['chapter_name']
        chapter_content = item['chapter_content']
        if book not in getattr(self,source):
            # if self.CS!={}:
                # self.save_file()
                # self.CS, self.GS, self.IS, self.MS, self.OS = {}, {}, {}, {}, {}
            getattr(self,source)[book] = {}
        getattr(self,source)[book][chapter_number] = chapter_content

    def save_file(self):
        map_name = {'CS': '解经资料(注解)',
                    'GS': '解经资料(拾穗)',
                    'IS': '解经资料(例证)',
                    'MS': '解经资料(短篇信息)',
                    'OS': '解经资料(纲目)'
                    }
        for each_source in map_name:
            folder = map_name[each_source]
            if not os.path.exists(map_name[each_source]):
                os.mkdir(map_name[each_source])
            for each_book in getattr(self,each_source):
                with open(os.path.join(folder,each_book+'.json'),'w') as outfile:
                    json.dump(getattr(self,each_source)[each_book],outfile)

    def close_spider(self, spider):
        map_name = {'CS': '解经资料(注解)',
                    'GS': '解经资料拾穗)',
                    'IS': '解经资料(例证)',
                    'MS': '解经资料(短篇信息)',
                    'OS': '解经资料(纲目)'
                    }
        for each_source in map_name:
            folder = map_name[each_source]
            if not os.path.exists(map_name[each_source]):
                os.mkdir(map_name[each_source])
            for each_book in getattr(self,each_source):
                with open(os.path.join(folder,each_book+'.json'),'w') as outfile:
                    json.dump(getattr(self,each_source)[each_book],outfile)


