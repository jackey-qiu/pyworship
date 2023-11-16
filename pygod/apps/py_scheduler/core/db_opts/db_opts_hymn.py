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
            'onclicked_func': update_selected_record,
            'update_func': update_recored_upon_change_in_pd_model}
    init_pandas_model_from_db_base(**args)

def load_db_hymn(self):
    # update_cache(self)
    init_pandas_model_from_db(self)
    update_selected_record(self)
    self.tableView_book_info.resizeColumnsToContents()
    #extract_all_song_titles(self)

def resume_pos_after_change_table(self, row = 0, tableview_widget_name = 'tableView_book_info'):
    tableView = getattr(self, tableview_widget_name)
    if tableView.selectionModel().hasSelection():
        row = tableView.selectionModel().selectedIndexes()[1].row()
    if row>=len(tableView.model()._data):
        row = len(tableView.model()._data)
    tableView.selectRow(row)
    update_selected_record(self, index=row)

def update_cache(self):
    # self.cache = list(self.database.hymn_info.find({}).limit(50))
    self.cache = list(self.database.hymn_info.find({}))

def clear_all_text_field(self, widgets = ['frame_song_info','tabWidget_song']):
    for widget in widgets:
        for each in getattr(self, widget).findChildren(QLineEdit):
            each.setText('')
        for each in getattr(self, widget).findChildren(QTextEdit):
            each.setPlainText('')
    today = datetime.datetime.today()
    date_str = f'{today.year}-{today.month}-{today.day}'
    self.lineEdit_archived_date_note.setText(date_str)

def extract_one_record_in_db(self):
    constrain = {'group_id':f'{self.lineEdit_hymn_name_note.text()}_{self.lineEdit_album_note.text()}_{self.lineEdit_band_note.text()}'} 
    if not extract_one_record(self, self.database_type, 'hymn_info', constrain):
        pass

def delete_one_record_in_db(self):
    current_row = self.tableView_book_info.selectionModel().selectedIndexes()[1].row()
    cbs = [init_pandas_model_from_db, partial(resume_pos_after_change_table, row=current_row)]
    extra_info = {'group_id':f'{self.lineEdit_hymn_name_note.text()}_{self.lineEdit_album_note.text()}_{self.lineEdit_band_note.text()}'} 
    delete_one_record(self, self.database_type, extra_info, cbs = cbs)

def add_one_record_in_db(self):
    current_row = self.tableView_book_info.selectionModel().selectedIndexes()[1].row()
    if (self.lineEdit_hymn_name_note.text()==''):
        error_pop_up('歌名不能为空，请填充', 'Error')
    extra_info = {'group_id':f'{self.lineEdit_hymn_name_note.text()}_{self.lineEdit_album_note.text()}_{self.lineEdit_band_note.text()}'} 
    cbs = [init_pandas_model_from_db, partial(resume_pos_after_change_table, row=current_row)]
    if self.database['hymn_info'].count_documents(extra_info)==1:
        update_one_record(self, '诗歌', 'hymn_info', constrain= extra_info, cbs=cbs)
    elif self.database['hymn_info'].count_documents(extra_info)==0:    
        add_one_record(self, self.database_type,'hymn_info',extra_info, cbs)

def update_recored_upon_change_in_pd_model(self):
    extra_info = {'group_id':f'{self.lineEdit_hymn_name_note.text()}_{self.lineEdit_album_note.text()}_{self.lineEdit_band_note.text()}'} 
    update_one_record(self, '诗歌', 'hymn_info', constrain= extra_info, cbs=[], silent=True)
    # self.tableView_book_info.resizeColumnsToContents() 

def update_selected_record(self, index = 0):
    if type(index)!=int:
        name = self.pandas_model._data['name'].tolist()[index.row()]
        album = self.pandas_model._data['album'].tolist()[index.row()]
        band = self.pandas_model._data['band'].tolist()[index.row()]
        collection =  'hymn_info'
        extra_info = {'group_id':f'{name}_{album}_{band}'} 
        # extract_one_record(self, self.database_type, collection, extra_info, cache=self.cache[index.row()])
        extract_one_record(self, self.database_type, collection, extra_info)
        
    else:
        if len(self.pandas_model._data)>index:
            name = self.pandas_model._data['name'].tolist()[index]
            album = self.pandas_model._data['album'].tolist()[index]
            band = self.pandas_model._data['band'].tolist()[index]
            collection =  'hymn_info'
            extra_info = {'group_id':f'{name}_{album}_{band}'} 
            # extract_one_record(self, self.database_type, collection, extra_info, cache=self.cache[0]) 
            extract_one_record(self, self.database_type, collection, extra_info) 

#get data for this attr to be saved in db
def get_data_for_x_check_status(self):
    try:
        data_ = self.pandas_model._data
        contraint = (data_['name']==self.lineEdit_hymn_name_note.text()) & (data_['album']==self.lineEdit_album_note.text()) & (data_['band']==self.lineEdit_band_note.text())
        return bool(list(data_[contraint]['checked'])[0])
    except:
        return False

#extract from db, and set content to the widget
def set_data_for_x_check_status(self, content):
    pass

#get data for this attr to be saved in db
def get_data_for_x_correct_status(self):
    try:
        data_ = self.pandas_model._data
        contraint = (data_['name']==self.lineEdit_hymn_name_note.text()) & (data_['album']==self.lineEdit_album_note.text()) & (data_['band']==self.lineEdit_band_note.text())
        return bool(list(data_[contraint]['corrected'])[0])
    except:
        return False

#extract from db, and set content to the widget
def set_data_for_x_correct_status(self, content):
    pass