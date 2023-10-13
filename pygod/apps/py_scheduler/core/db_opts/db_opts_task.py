import datetime
from PyQt5.QtWidgets import QPushButton
import pandas as pd
from ..db_opts.common_db_opts import *
# from .db_opts_entry import init_pandas_model_from_db
#apis for task database
def init_pandas_model_from_db(self):
    args = {'self': self, 
            'tab_indx': 2, 
            'single_collection': False, 
            'contrains': get_current_task_constrain(self), 
            'onclicked_func': update_selected_task_info}
    init_pandas_model_from_db_base(**args)

def load_db_task(self):
    init_pandas_model_from_db(self)

def get_collection_name_lookup_map(self, db_type):
    collections = get_collection_list_from_yaml(self, db_type)
    name_lookup_map = {}
    for collection in collections:
        info_temp = get_document_info_from_yaml(self, db_type, collection)
        if 'map_name' in info_temp:
            name_lookup_map[info_temp['map_name']] = collection
    return name_lookup_map
    
def get_current_task_constrain(self):
    collection_name_map = get_collection_name_lookup_map(self, db_type = '服事')
    month = self.comboBox_month.currentText()
    year = datetime.date.today().year
    return ['group_id', f'{year}_{month}']

def add_task_info(self):
    cbs = [init_pandas_model_from_db]
    collection_name_map = get_collection_name_lookup_map(self, db_type = '服事')
    collection = collection_name_map[self.comboBox_group.currentText()]
    month = self.comboBox_month.currentText()
    year = datetime.date.today().year
    group_id = f'{year}_{month}'
    if self.database[collection].count_documents({'group_id': group_id})==1:
        update_one_record(self, '服事', collection, constrain= {'group_id': group_id}, cbs=cbs)
    elif self.database[collection].count_documents({'group_id': group_id})==0:
        add_one_record(self, '服事', collection, extra_info= {'group_id': group_id}, cbs=cbs)
    if get_data_for_x_role_note(self)!='主题':
        add_worker_names_info(self)
        update_worker_names_info(self)

def update_selected_task_info(self, index = None):
    self.comboBox_group.setCurrentText(self.pandas_model._data['collections'].tolist()[index.row()])
    collection =  get_collection_name_lookup_map(self, self.database_type)[self.comboBox_group.currentText()]
    year = datetime.date.today().year
    group_id = f'{year}_{self.comboBox_month.currentText()}'
    constrain = {'group_id': group_id}
    extract_one_record(self, self.database_type, collection, constrain)
    if get_data_for_x_role_note(self)!='主题':
        update_worker_names_info(self)

def add_worker_names_info(self):
    role = get_data_for_x_role_note(self)
    if role=='主题':
        return
    collection = 'name_info'
    cbs = []
    if self.database[collection].count_documents({'role': role})==1:
        update_one_record(self, '服事', collection, constrain= {'role': role}, cbs=cbs)
    elif self.database[collection].count_documents({'role': role})==0:
        add_one_record(self, '服事', collection, cbs=cbs)

def update_worker_names_info(self):
    constrain = {'role': get_data_for_x_role_note(self)}
    extract_one_record(self, self.database_type, 'name_info', constrain)

def set_data_for_x_role_note(self, content):
    pass

def get_data_for_x_role_note(self):
    return self.comboBox_group.currentText()

def set_data_for_x_worker_name_note(self, content):
    #remove all widgets first
    for i in reversed(range(self.gridLayout_names.count())): 
        self.gridLayout_names.itemAt(i).widget().setParent(None)
    names = content.rsplit('+')
    for i, name in enumerate(names):
        button = QPushButton(name)
        button.setStyleSheet("font-size: 14px;")
        self.gridLayout_names.addWidget(button, int(i/8), i%8)
        button.clicked.connect(lambda state, name=name:self.activated_task_input_widget.setText(f'{self.activated_task_input_widget.text()}+{name}'))

def get_data_for_x_worker_name_note(self):
    names_db = text_query_by_field(self, field = 'role', query_string = get_data_for_x_role_note(self), target_field='name', collection_name = 'name_info')
    if len(names_db)!=0:
        names_db = names_db[0].rsplit('+')
    else:
        names_db = []
    names = self.lineEdit_1st_week_note.text().rsplit('+') + \
            self.lineEdit_2nd_week_note.text().rsplit('+') + \
            self.lineEdit_3rd_week_note.text().rsplit('+') + \
            self.lineEdit_4th_week_note.text().rsplit('+') + \
            self.lineEdit_5th_week_note.text().rsplit('+')
    names = list(set([each for each in names if each!='' and each not in names_db]))
    return '+'.join(sorted(names+names_db))

