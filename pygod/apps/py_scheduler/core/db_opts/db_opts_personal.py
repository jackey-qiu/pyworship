import PyQt5
from ..db_opts.common_db_opts import *

def init_pandas_model_from_db(self, pandas_data = None):
    args = {'self': self, 
            'tab_indx': 1, 
            'single_collection': True, 
            'contrains': [], 
            'onclicked_func': update_selected_person_info,
            'pandas_data': pandas_data}
    init_pandas_model_from_db_base(**args)

def load_db_pe(self, pandas_data = None, resize = True):
    init_pandas_model_from_db(self, pandas_data)
    # update_selected_person_info(self)
    if resize:
        self.tableView_book_info.resizeColumnsToContents()

def rerender_tableview(self, pandas_data):
    load_db_pe(self, pandas_data)
    self.tableView_book_info.selectRow(0)

#apis for personal database
def load_img_from_file(self):
    img_format = open_image_file(self, widget_view = self.widget_img_view)
    self.lineEdit_img_format.setText(img_format)

def get_data_for_widget_img_view(self):
    return self.img_in_base64_format

def set_data_for_widget_img_view(self, data):
    self.img_in_base64_format = data
    self.widget_img_view.clear()
    self.widget_img_view.loadImages([image_string_to_qimage(data, img_format = self.lineEdit_img_format.text())])
    self.widget_img_view.show() 

def add_personal_info(self):
    cbs = [init_pandas_model_from_db]
    collection = 'personal_info'
    if self.database[collection].count_documents({'name': self.lineEdit_name_ccg_note.text()})==1:
        update_one_record(self, '人事', collection, constrain= {'name': self.lineEdit_name_ccg_note.text()}, cbs=cbs)
    elif self.database[collection].count_documents({'name': self.lineEdit_name_ccg_note.text()})==0:
        add_one_record(self, '人事', collection, cbs=cbs)

def delete_one_person(self):
    delete_one_record(self, self.database_type, {'name':self.lineEdit_name_ccg_note.text()}, cbs = [init_pandas_model_from_db])

def update_selected_person_info(self, index = None):
    name = self.pandas_model._data['name'].tolist()[index.row()]
    collection =  'personal_info'
    constrain = {'name': name}
    extract_one_record(self, self.database_type, collection, constrain)

def clear_all_input(self, layout_name):
    count = getattr(self, layout_name).count()
    for i in range(count):
        if type(getattr(self, layout_name).itemAt(i).widget()) == PyQt5.QtWidgets.QLineEdit:
            getattr(self, layout_name).itemAt(i).widget().clear()
