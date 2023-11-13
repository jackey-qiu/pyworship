from ..util import error_pop_up, get_date_from_nth_week
from pathlib import Path
import datetime
from PyQt5.QtWidgets import QInputDialog, QTextEdit, QLineEdit
from pathlib import Path
from ..db_opts.common_db_opts import *
from datetime import timedelta
from pygod.apps.ppt_worker.scripts.ppt_worker import main as ppt

def init_pandas_model_from_db(self):
    args = {'self': self, 
            'tab_indx': 6, 
            'single_collection': True, 
            'contrains': [], 
            'onclicked_func': update_selected_hymn_info}
    init_pandas_model_from_db_base(**args)

def load_db_hymn(self):
    init_pandas_model_from_db(self)
    #extract_all_song_titles(self)

def clear_all_text_field(self, widgets = ['frame_song_info','tabWidget_song']):
    for widget in widgets:
        for each in getattr(self, widget).findChildren(QLineEdit):
            each.setText('')
        for each in getattr(self, widget).findChildren(QTextEdit):
            each.setPlainText('')
    today = datetime.datetime.today()
    date_str = f'{today.year}-{today.month}-{today.day}'
    self.lineEdit_archived_date_note.setText(date_str)

def extract_hymn_record(self):
    constrain = {'group_id':f'{self.lineEdit_hymn_name_note.text()}_{self.lineEdit_album_note.text()}_{self.lineEdit_band_note.text()}'} 
    if not extract_one_record(self, self.database_type, 'hymn_info', constrain):
        pass

def delete_hymn_record(self):
    cbs = [init_pandas_model_from_db]
    extra_info = {'group_id':f'{self.lineEdit_hymn_name_note.text()}_{self.lineEdit_album_note.text()}_{self.lineEdit_band_note.text()}'} 
    delete_one_record(self, self.database_type, extra_info, cbs = cbs)

def add_one_hymn_record(self):
    extra_info = {'group_id':f'{self.lineEdit_hymn_name_note.text()}_{self.lineEdit_album_note.text()}_{self.lineEdit_band_note.text()}'} 
    cbs = [init_pandas_model_from_db]
    if self.database['hymn_info'].count_documents(extra_info)==1:
        update_one_record(self, '诗歌', 'hymn_info', constrain= extra_info, cbs=cbs)
    elif self.database['hymn_info'].count_documents(extra_info)==0:    
        add_one_record(self, self.database_type,'hymn_info',extra_info, cbs)

def update_selected_hymn_info(self, index = None):
    name = self.pandas_model._data['name'].tolist()[index.row()]
    album = self.pandas_model._data['album'].tolist()[index.row()]
    band = self.pandas_model._data['band'].tolist()[index.row()]
    collection =  'hymn_info'
    extra_info = {'group_id':f'{name}_{album}_{band}'} 
    extract_one_record(self, self.database_type, collection, extra_info)