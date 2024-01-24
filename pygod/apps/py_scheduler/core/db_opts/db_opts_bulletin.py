from ..util import error_pop_up, clear_all_text_field, get_dates_for_one_month
import datetime
from pathlib import Path
from functools import partial
from .common_db_opts import * 
from pygod.apps.bulletin_worker.scripts.bulletin_worker import main as bulletin

def init_pandas_model_from_db(self):
    args = {'self': self, 
            'tab_indx': 5, 
            'single_collection': True, 
            'contrains': [], 
            'onclicked_func': update_selected_bulletin_info}
    init_pandas_model_from_db_base(**args)

def load_db_bulletin(self, **kwargs):
    init_pandas_model_from_db(self)

#api functions for bulletin creator
def extract_bulletin_record(self):
    month = self.comboBox_bulletin_month.currentText()
    year = self.lineEdit_year_bulletin.text()
    #year = datetime.date.today().year
    group_id = f'{year}_{month}'
    constrain = {'group_id':group_id}    
    extract_one_record(self, self.database_type, 'bulletin_info', constrain)
    extract_one_record(self, self.database_type, 'attendence_info_sunday', constrain)
    extract_one_record(self, self.database_type, 'attendence_info_bible_study', constrain)
    extract_one_record(self, self.database_type, 'year_scripture', {'group_id':str(year)})

def delete_bulletin_record(self):
    month = self.comboBox_bulletin_month.currentText()
    year = self.lineEdit_year_bulletin.text()
    # year = datetime.date.today().year
    group_id = f'{year}_{month}'
    delete_one_record(self, self.database_type, {'group_id':group_id}, cbs = [partial(clear_all_text_field, tabWidget='tabWidget_bulletin'), init_pandas_model_from_db])

def add_one_bulletin_record(self):
    month = self.comboBox_bulletin_month.currentText()
    year = self.lineEdit_year_bulletin.text()
    # year = datetime.date.today().year
    group_id = f'{year}_{month}'
    extra_info = {'group_id':group_id}
    cbs = [init_pandas_model_from_db]
    def _add_or_update(collection, constraint, cbs):
        if self.database[collection].count_documents(constraint)==1:
            update_one_record(self, self.database_type, collection, constrain=constraint, cbs=cbs)
        elif self.database[collection].count_documents(constraint)==0:
            add_one_record(self, self.database_type, collection, extra_info=constraint, cbs=cbs)
    collections = ['bulletin_info','attendence_info_sunday','attendence_info_bible_study', 'year_scripture']
    constraints = [extra_info]*3 + [{'group_id':str(year)}]
    for collection, constraint in zip(collections, constraints):
        _add_or_update(collection, constraint, cbs)

def get_task_content(self, key):
    #last one is shared collection which is the project info
    collections = get_collection_list_from_yaml(self, '服事')[2:-1]
    #also exclude name_info content
    excluded_collections = []
    if 'excluded_collections' in self.db_config_info['db_types']['服事']['table_viewer']:
        excluded_collections = self.db_config_info['db_types']['服事']['table_viewer']['excluded_collections']
    collections = [each for each in collections if each not in excluded_collections]
    db_temp = self.mongo_client[self.lineEdit_db_task.text()]
    contents = []
    for collection in collections:
        docs = get_document_info_from_yaml(self, '服事', collection)
        title = docs['map_name']
        row = [[title]] + text_query_by_field(self, 'group_id', key, list(docs.keys())[1:], collection, db_temp)
        formated_row = [l for r in row for l in r]
        contents.append(formated_row)
    contents_formated = []
    for each in contents:
        contents_formated.append(','.join(each))
    dates = ','.join(['日期']+get_dates_for_one_month(int(key.rsplit('_')[1]), int(key.rsplit('_')[0])))
    return '\n'.join([dates]+contents_formated)

def get_finance_content(self, key):
    month = self.comboBox_bulletin_month.currentText()
    year = self.lineEdit_year_bulletin.text()
    collection = 'finance_info'
    docs =  list(get_document_info_from_yaml(self, '财务', collection).keys())
    db_temp = self.mongo_client[self.lineEdit_db_finance.text()]
    income = []
    expense = []
    summary = [f'{year}年{month}月份']
    for doc in ['total_income','total_expense','net_income']:
        summary.append(text_query_by_field(self, 'group_id', key, doc, collection, db_temp)[0])
    for doc in docs:
        if not doc.endswith('note'):
            if doc not in ['total_income','total_expense','net_income']:
                value = text_query_by_field(self, 'group_id', key, doc, collection, db_temp)
                note = text_query_by_field(self, 'group_id', key, doc+'_note', collection, db_temp)
                if note == ['']:
                    note = [doc]
                if doc.startswith('income'):
                    if value!=['0.0']:
                        income.append([note[0], '+'+str(value[0])])
                else:
                    if value!=['0.0']:
                        expense.append([note[0], '-'+str(value[0])])
    income = '\n'.join(['&'.join(each) for each in income])
    expense = '\n'.join(['&'.join(each) for each in expense])
    summary = '&'.join(list(map(str,summary)))
    return income+'\n'+expense+'\n'+summary

def get_last_month_record(self):
    widgets = ['lineEdit_dates_1_note','lineEdit_attendence_note','lineEdit_offerings_note',\
               'lineEdit_dates_2_note','lineEdit_attendence_onsite_note','lineEdit_attendence_online_note']
    contents = []
    for each in widgets:
        contents.append(getattr(self, each).text())
    return '\n'.join(contents)

def update_selected_bulletin_info(self, index = None):
    group_id = self.pandas_model._data['group_id'].tolist()[index.row()]
    y, m = group_id.rsplit('_')
    self.comboBox_bulletin_month.setCurrentText(m)
    self.lineEdit_year_bulletin.setText(y)
    collection =  'bulletin_info'
    constrain = {'group_id': group_id}
    extract_one_record(self, self.database_type, collection, constrain)

def get_preach_content(self, key):
    collections = get_collection_list_from_yaml(self, '服事')[0:2]
    db_temp = self.mongo_client[self.lineEdit_db_task.text()]
    contents = []
    for collection in collections:
        docs = get_document_info_from_yaml(self, '服事', collection)
        title = docs['map_name']
        row = text_query_by_field(self, 'group_id', key, list(docs.keys())[1:], collection, db_temp)
        formated_row = [l for r in row for l in r]#each item is like topic+chapter
        if title=='主题':
            topic = []
            chapter = []
            for each in formated_row:
                if each=='':
                    topic.append('')
                    chapter.append('')
                else:
                    items = each.rsplit('+')
                    if len(items)>=2:
                        topic.append(items[0])
                        chapter.append(items[1])
                    elif len(items)==1:
                        topic.append(items[0])
                        chapter.append('')
            contents.append(topic)
            contents.append(chapter)
        else:
            contents.append(formated_row)
    contents_formated = []
    for each in contents:
        contents_formated.append(','.join(each))
    dates = get_dates_for_one_month(int(key.rsplit('_')[-1]), int(key.rsplit('_')[0]))
    contents_formated = [','.join(dates)]+[contents_formated[0],contents_formated[2],contents_formated[1]]
    return '\n'.join(contents_formated)

def save_bulletin_content_in_txt_format_and_make_bulletin(self):
    year = self.lineEdit_year_bulletin.text()
    month = self.comboBox_bulletin_month.currentText()
    txt_file_name = f'bulletin_{year}-{month}.txt'
    doc_file_name = f'bulletin_{year}-{month}.docx'
    #content_folder = Path(__file__).parent.parent.parent / 'ppt_worker' / 'src' / 'contents'
    content_folder = Path.home() / 'pygodAppData' / 'content_files'
    content_folder.mkdir(parents=True, exist_ok=True)
    year, month= int(year), int(month)
    content_types = ['YearScripture','MonthlyScripture','MonthlyServiceTable','Report','Pray','LastMonthRecord','FinanceTable','PreachTable']
    api_map = {'YearScripture':'self.textEdit_year_scripture_note.toPlainText()',
                  'MonthlyScripture':'self.textEdit_month_scripture_note.toPlainText()',
                  'Report':'self.textEdit_reports_note.toPlainText()',
                  'Pray': 'self.textEdit_prays_note.toPlainText()',
                  'LastMonthRecord':'get_last_month_record(self)',
                  'PreachTable':f"get_preach_content(self,'{year}_{month}')",
                  'MonthlyServiceTable':f"get_task_content(self,'{year}_{month}')",
                  'FinanceTable':f"get_finance_content(self, '{year}_{month}月')"
                  }
    try:    
        with open(str(content_folder / txt_file_name), 'w', encoding='utf8') as f:
            for content_type in content_types:
                f.write(f"<{content_type}>\n{eval(api_map[content_type])}\n</{content_type}>\n")
        bulletin(year, month, str(content_folder / txt_file_name), str(content_folder / doc_file_name))
        error_pop_up(f"The bulletin doc file is created and saved in {str(content_folder)}", 'Information')
    except Exception as e:
        error_pop_up(f'ERROR: {e}', 'Error')