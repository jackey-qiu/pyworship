import datetime
from ...widgets.dialogues import ReturnDialog
from ..util import error_pop_up, map_chinese_to_eng_key
from .common_db_opts import init_pandas_model_from_db_base, extract_one_record, delete_one_record, update_one_record, add_one_record, text_query_by_field
# from .db_opts_entry import init_pandas_model_from_db
def init_pandas_model_from_db(self):
    args = {'self': self, 
            'tab_indx': 0, 
            'single_collection': True, 
            'contrains': [], 
            'onclicked_func': update_selected_book_info}
    init_pandas_model_from_db_base(**args)

def load_db_book(self):
    init_pandas_model_from_db(self)
    update_paper_list_in_combobox(self)
    extract_paper_info(self)

def reserve(self):
    if self.lineEdit_status.text() in ['预约','借出']:
        error_pop_up('该书已经被预约或借出！')
        return
    if update_paper_info(self, '请确认是否预约该书？','预约成功！'):
        self.lineEdit_borrower.setText(self.name)
        self.lineEdit_status.setText('预约')
        self.pushButton_update.click()

def return_dialog(self):
    dlg = ReturnDialog(self)
    dlg.exec()

def update_paper_list_in_combobox(self):
    papers = get_papers_in_a_list(self)
    self.comboBox_books.clear()
    self.comboBox_books.addItems(papers)

def get_papers_in_a_list(self):
    all_info = list(self.database.paper_info.find({},{'_id':0}))
    paper_id_list = [each['paper_id'] for each in all_info]
    return sorted(paper_id_list)

def update_selected_book_info(self, index = None):
    self.comboBox_books.setCurrentText(self.pandas_model._data['paper_id'].tolist()[index.row()])
    extract_paper_info(self)

def update_project_info(self):
    try:
        self.database.project_info.drop()
        self.database.project_info.insert_many([{'project_info':self.plainTextEdit_project_info.toPlainText()}])
        error_pop_up('Project information has been updated successfully!','Information')
    except Exception as e:
        error_pop_up('Failure to update Project information!','Error')

def extract_paper_info(self):
    paper_id = self.comboBox_books.currentText()
    extract_one_record(self, self.database_type, collection='paper_info', constrain= {'paper_id': paper_id})

def delete_one_paper(self):
    paper_id = self.comboBox_books.currentText()
    delete_one_record(self, self.database_type, {'paper_id':paper_id}, cbs = [update_paper_list_in_combobox, init_pandas_model_from_db, extract_paper_info])

def update_paper_info(self):
    paper_id = self.comboBox_books.currentText()
    update_one_record(self, self.database_type, 'paper_info', {'paper_id':paper_id}, cbs = [init_pandas_model_from_db])

#create a new paper record in database
def add_paper_info(self):
    cbs = [init_pandas_model_from_db, update_paper_list_in_combobox]
    record = add_one_record(self, self.database_type, 'paper_info', {'select':False, 'archive_date': datetime.datetime.today().strftime('%Y-%m-%d')}, cbs= cbs)
    self.comboBox_books.setCurrentText(record['paper_id'])              

def query_paper_info_for_paper_id(self, field, query_string):
    field =  map_chinese_to_eng_key(field)
    return_list = text_query_by_field(self, field, query_string, target_field='paper_id',collection_name = 'paper_info')
    if len(return_list)!=0:
        self.comboBox_books.setCurrentText(return_list[0])
        extract_paper_info(self)
    else:
        error_pop_up('Nothing return')