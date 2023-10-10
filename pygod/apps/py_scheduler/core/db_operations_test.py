from .util import error_pop_up, PandasModel, map_chinese_to_eng_key, get_date_from_nth_week, get_dates_for_one_month
from ..widgets.dialogues import NewProject, QueryDialog, LendDialog, ReturnDialog, LoginDialog, RegistrationDialog
from dotenv import load_dotenv
from pathlib import Path
import os, certifi, datetime, time
from pymongo import MongoClient
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QTextEdit, QLineEdit
from pathlib import Path
import PyQt5
import pandas as pd
from functools import partial
import yaml
from .common_db_opts import *
from .graph_operations import create_piechart
from datetime import timedelta
from pygod.apps.ppt_worker.scripts.ppt_worker import main as ppt
from pygod.apps.bulletin_worker.scripts.bulletin_worker import main as bulletin

db_config_file = Path(__file__).parent.parent / 'config' / 'db_matching.yaml'
db_config_info = None
with open(db_config_file, 'r', encoding='utf8') as f:
    db_config_info = yaml.safe_load(f.read())

def set_db_config(self):
    self.db_config_info = db_config_info

def start_mongo_client_cloud(self):
    try:
        if not os.path.exists(str(Path(__file__).parent.parent/ "resources" / "private" / "atlas_password.dot")):
            error_pop_up('You should create a file named atlas_password under Library_Manager/resources/private folder, \
                            where you save the atlas url link for your MongoDB atlas cloud account. \
                            please use the format ATLAS_URL="URL LINK"')
        else:
            env = load_dotenv(str(Path(__file__).parent.parent/ "resources" / "private" / "atlas_password.dot"))
            if env:
                url = os.getenv('ATLAS_URL') 
                login_dialog(self, url)
                #self.mongo_client = MongoClient(url,tlsCAFile=certifi.where())
            else:
                url = ''
                print('something is wrong')
    except Exception as e:
        error_pop_up('Fail to start mongo client.'+'\n{}'.format(str(e)),'Error')

def register_new_user(self):
    try:
        if not os.path.exists(str(Path(__file__).parent.parent/ "resources" / "private" / "atlas_password.dot")):
            error_pop_up('You should create a file named atlas_password under Library_Manager/resources/private folder, \
                            where you save the atlas url link for your MongoDB atlas cloud account. \
                            please use the format ATLAS_URL="URL LINK"')
        else:
            env = load_dotenv(str(Path(__file__).parent.parent/ "resources" / "private" / "atlas_password.dot"))
            if env:
                url = os.getenv('ATLAS_URL') 
                register_dialog(self, url)
                #self.mongo_client = MongoClient(url,tlsCAFile=certifi.where())
            else:
                url = ''
                print('something is wrong')
    except Exception as e:
        error_pop_up('Fail to start mongo client for new user registration.'+'\n{}'.format(str(e)),'Error')

def extract_project_info(self):
    all = self.database.project_info.find()
    self.plainTextEdit_project_info.setPlainText('\n'.join([each['project_info'] for each in all]))

def load_project(self):
    self.database = self.mongo_client[self.comboBox_project_list.currentText()]
    extract_project_info(self)
    # self.database_type = self.comboBox_project_list.currentText().rsplit('-')[1]
    if 'db_type' in self.database.project_info.find_one():
        self.database_type = self.database.project_info.find_one()['db_type']
    else:
        self.database_type = "图书"
    #self.update_paper_list_in_listwidget()
    init_pandas_model_from_db(self)
    if self.database_type == '图书':
        update_paper_list_in_combobox(self)
        extract_paper_info(self)
    elif self.database_type == 'PPT':
        extract_all_song_titles(self)

def disable_all_tabs_but_one(self, tab_name = 'tabWidget_2', enabled_tab_ix = 0):
    for i in range(len(getattr(self, tab_name))):
        getattr(self, tab_name).setTabEnabled(i, False)
    getattr(self, tab_name).setTabEnabled(enabled_tab_ix, True)

def init_pandas_model_from_db(self):
    if self.database_type == '图书':
        disable_all_tabs_but_one(self, 'tabWidget_2', 0)
        self.tabWidget_2.setCurrentIndex(0) 
        data = create_pandas_data_from_db(self, db_type = self.database_type, single_collection= True)
    elif self.database_type == '服事':
        disable_all_tabs_but_one(self, 'tabWidget_2', 2)
        self.tabWidget_2.setCurrentIndex(2) 
        data = create_pandas_data_from_db(self, db_type = self.database_type, single_collection= False, constrains = get_current_task_constrain(self))
    elif self.database_type == '人事':
        disable_all_tabs_but_one(self, 'tabWidget_2', 1)
        self.tabWidget_2.setCurrentIndex(1) 
        data = create_pandas_data_from_db(self, db_type = self.database_type, single_collection= True)
    elif self.database_type == '财务':
        disable_all_tabs_but_one(self, 'tabWidget_2', 3)
        self.tabWidget_2.setCurrentIndex(3) 
        data = create_pandas_data_from_db(self, db_type = self.database_type, single_collection= True)
    elif self.database_type == 'PPT':
        disable_all_tabs_but_one(self, 'tabWidget_2', 4)
        self.tabWidget_2.setCurrentIndex(4) 
        data = create_pandas_data_from_db(self, db_type = self.database_type, single_collection= True)
    elif self.database_type == '月报':
        disable_all_tabs_but_one(self, 'tabWidget_2', 5)
        self.tabWidget_2.setCurrentIndex(5) 
        data = create_pandas_data_from_db(self, db_type = self.database_type, single_collection= True)
    else:
        data = pd.DataFrame({})
    #if self.database_type in ['图书','服事','人事','财务']:
    #data['select'] = data['select'].astype(bool)
    header_name_map = {}
    if len(data)!=0:
        header_name_map = list(self.db_config_info['db_types'][self.database_type]['table_viewer'].values())[0]
    self.pandas_model_paper_info = PandasModel(data = data, tableviewer = self.tableView_book_info, main_gui = self, column_names=header_name_map)
    self.tableView_book_info.setModel(self.pandas_model_paper_info)
    self.tableView_book_info.resizeColumnsToContents()
    self.tableView_book_info.setSelectionBehavior(PyQt5.QtWidgets.QAbstractItemView.SelectRows)
    self.tableView_book_info.horizontalHeader().setStretchLastSection(True)
    if self.database_type == '图书':
        try:
            self.tableView_book_info.clicked.disconnect()
        except:
            pass
        self.tableView_book_info.clicked.connect(partial(update_selected_book_info,self))
    elif self.database_type == '服事':
        try:
            self.tableView_book_info.clicked.disconnect()
        except:
            pass
        self.tableView_book_info.clicked.connect(partial(update_selected_task_info,self))
    elif self.database_type == '人事':
        try:
            self.tableView_book_info.clicked.disconnect()
        except:
            pass
        self.tableView_book_info.clicked.connect(partial(update_selected_person_info,self))
    elif self.database_type == '财务':
        try:
            self.tableView_book_info.clicked.disconnect()
        except:
            pass
        self.tableView_book_info.clicked.connect(partial(update_selected_finance_info,self))
    elif self.database_type == 'PPT':
        try:
            self.tableView_book_info.clicked.disconnect()
        except:
            pass
        self.tableView_book_info.clicked.connect(partial(update_selected_PPT_info,self))
    elif self.database_type == '月报':
        try:
            self.tableView_book_info.clicked.disconnect()
        except:
            pass
        self.tableView_book_info.clicked.connect(partial(update_selected_bulletin_info,self))

def update_project_info(self):
    try:
        self.database.project_info.drop()
        self.database.project_info.insert_many([{'project_info':self.plainTextEdit_project_info.toPlainText()}])
        error_pop_up('Project information has been updated successfully!','Information')
    except Exception as e:
        error_pop_up('Failure to update Project information!','Error')

def new_project_dialog(self):
    dlg = NewProject(self)
    dlg.exec()

def lend_dialog(self):
    dlg = LendDialog(self)
    dlg.exec()

def login_dialog(self, url):
    dlg = LoginDialog(self, url)
    dlg.exec()

def logout(self):
    self.name = 'undefined'
    self.user_name = 'undefined'
    self.role = 'undefined'
    self.mongo_client = None
    self.database = None
    self.removeToolBar(self.toolBar)
    try:
        self.init_gui(self.ui)
        self.statusLabel.setText('Goodbye, you are logged out!')
    except:
        pass

def reserve(self):
    if self.lineEdit_status.text() in ['预约','借出']:
        error_pop_up('该书已经被预约或借出！')
        return
    if update_paper_info(self, '请确认是否预约该书？','预约成功！'):
        self.lineEdit_borrower.setText(self.name)
        self.lineEdit_status.setText('预约')
        self.pushButton_update.click()

def register_dialog(self, url):
    dlg = RegistrationDialog(self, url)
    dlg.exec()

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
    self.comboBox_books.setCurrentText(self.pandas_model_paper_info._data['paper_id'].tolist()[index.row()])
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

#apis for task database

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

def update_selected_task_info(self, index = None):
    self.comboBox_group.setCurrentText(self.pandas_model_paper_info._data['collections'].tolist()[index.row()])
    collection =  get_collection_name_lookup_map(self, self.database_type)[self.comboBox_group.currentText()]
    year = datetime.date.today().year
    group_id = f'{year}_{self.comboBox_month.currentText()}'
    constrain = {'group_id': group_id}
    extract_one_record(self, self.database_type, collection, constrain)

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
    if self.database[collection].count_documents({'name': self.lineEdit_name_ccg.text()})==1:
        update_one_record(self, '人事', collection, constrain= {'name': self.lineEdit_name_ccg.text()}, cbs=cbs)
    elif self.database[collection].count_documents({'name': self.lineEdit_name_ccg.text()})==0:
        add_one_record(self, '人事', collection, cbs=cbs)

def delete_one_person(self):
    delete_one_record(self, self.database_type, {'name':self.lineEdit_name_ccg.text()}, cbs = [init_pandas_model_from_db])

def update_selected_person_info(self, index = None):
    name = self.pandas_model_paper_info._data['name'].tolist()[index.row()]
    collection =  'personal_info'
    constrain = {'name': name}
    extract_one_record(self, self.database_type, collection, constrain)

def clear_all_input(self, layout_name):
    count = getattr(self, layout_name).count()
    for i in range(count):
        if type(getattr(self, layout_name).itemAt(i).widget()) == PyQt5.QtWidgets.QLineEdit:
            getattr(self, layout_name).itemAt(i).widget().clear()

# apis for finance info
def add_finance_info(self):
    calculate_sum(self)
    cbs = [init_pandas_model_from_db]
    collection = 'finance_info'
    month = self.comboBox_finance_month.currentText()
    year = datetime.date.today().year
    group_id = f'{year}_{month}'
    if self.database[collection].count_documents({'group_id': group_id})==1:
        update_one_record(self, '财务', collection, constrain= {'group_id': group_id}, cbs=cbs)
    elif self.database[collection].count_documents({'group_id': group_id})==0:
        add_one_record(self, '财务', collection, extra_info= {'group_id': group_id}, cbs=cbs)

def update_selected_finance_info(self, index = None):
    group_id = self.pandas_model_paper_info._data['group_id'].tolist()[index.row()]
    self.comboBox_finance_month.setCurrentText(group_id.rsplit('_')[-1])
    collection =  'finance_info'
    constrain = {'group_id': group_id}
    extract_one_record(self, self.database_type, collection, constrain)
    create_piechart(self)

def delete_finance_info(self):
    month = self.comboBox_finance_month.currentText()
    year = datetime.date.today().year
    group_id = f'{year}_{month}'
    delete_one_record(self, self.database_type, {'group_id':group_id}, cbs = [init_pandas_model_from_db])

def calculate_sum(self, total_income_widget = 'lineEdit_total_income', total_expense_widget = 'lineEdit_total_expense', net_income_widget = 'lineEdit_net_income'):
    income = 0
    expense = 0
    income_widgets = ['lineEdit_income_offering_onside','lineEdit_income_offering_online',
                      'lineEdit_income_offering_lubeck','lineEdit_income_offering_kiel',
                      'lineEdit_income_offering_korea','lineEdit_income_offering_others','lineEdit_income_offering_others2']
    expense_widgets = ['lineEdit_expense_pastor_wu','lineEdit_expense_pastor_guan','lineEdit_expense_pastor_chuandao',
                       'lineEdit_expense_kiel','lineEdit_expense_lubeck','lineEdit_expense_nebenkosten','lineEdit_expense_software_subscribe',
                       'lineEdit_expense_other_cost_1', 'lineEdit_expense_other_cost_2','lineEdit_expense_other_cost_3',
                       'lineEdit_expense_other_cost_4','lineEdit_expense_other_cost_5']
    for each in income_widgets:
        try:
            temp = float(eval(f'self.{each}.text()'))
        except:
            print('invalid number in the widget {}'.format(each))
            temp = 0
        income = income + temp

    for each in expense_widgets:
        try:
            temp = float(eval(f'self.{each}.text()'))
        except:
            print('invalid number in the widget {}'.format(each))
            temp = 0
        expense = expense + temp
    getattr(self, total_income_widget).setText(str(round(income,4)))
    getattr(self, total_expense_widget).setText(str(round(expense,4)))
    getattr(self, net_income_widget).setText(str(round(income - expense,4)))


#api funcs for ppt worker
def clear_all_text_field(self, tabWidget = 'tabWidget_note'):
    for each in getattr(self, tabWidget).findChildren(QLineEdit):
        each.setText('')
    for each in getattr(self, tabWidget).findChildren(QTextEdit):
        each.setPlainText('')
    
def extract_ppt_record(self):
    month = self.comboBox_ppt_month.currentText()
    year = datetime.date.today().year
    week_map = dict([('第一周','1st_week'),('第二周','2nd_week'),('第三周','3rd_week'),('第四周','4th_week'),('第五周','5th_week')])
    week = week_map[self.comboBox_ppt_week.currentText()]
    group_id = f'{year}_{month}+{week}'
    constrain = {'group_id':group_id}    
    self.pushButton_extract_worker_info.click()
    if not extract_one_record(self, self.database_type, 'ppt_info', constrain):
        clear_all_text_field(self)

def delete_ppt_record(self):
    cbs = [init_pandas_model_from_db,clear_all_text_field]
    month = self.comboBox_ppt_month.currentText()
    year = datetime.date.today().year
    week_map = dict([('第一周','1st_week'),('第二周','2nd_week'),('第三周','3rd_week'),('第四周','4th_week'),('第五周','5th_week')])
    week = week_map[self.comboBox_ppt_week.currentText()]
    group_id = f'{year}_{month}+{week}'
    delete_one_record(self, self.database_type, {'group_id':group_id}, cbs = cbs)

def add_one_ppt_record(self):
    month = self.comboBox_ppt_month.currentText()
    year = datetime.date.today().year
    week_map = dict([('第一周','1st_week'),('第二周','2nd_week'),('第三周','3rd_week'),('第四周','4th_week'),('第五周','5th_week')])
    week = week_map[self.comboBox_ppt_week.currentText()]
    group_id = f'{year}_{month}+{week}'
    extra_info = {'group_id':group_id}
    cbs = [init_pandas_model_from_db]
    if self.database['ppt_info'].count_documents({'group_id': group_id})==1:
        update_one_record(self, 'PPT', 'ppt_info', constrain= {'group_id': group_id}, cbs=cbs)
    elif self.database['ppt_info'].count_documents({'group_id': group_id})==0:    
        add_one_record(self, self.database_type,'ppt_info',extra_info, cbs)

def extract_workers(self):
    set_data_for_x_workers_note(self)

def extract_all_song_titles(self):
    songs = [each['song_id'] for each in self.database.song_info.find()]
    for i in range(1, 5):
        getattr(self,f'comboBox_song{i}').clear()
        getattr(self,f'comboBox_song{i}').addItems(songs)

def extract_one_song(self, song_title, which):
    self.which_song_widget = which
    extract_one_record(self, self.database_type, 'song_info', {'song_id': song_title})

def add_one_song(self, which):
    self.which_song_widget = which
    txt = getattr(self, f'textEdit_song{which}_note').toPlainText().rsplit('\n')[0]
    text, ok = QInputDialog.getText(self, 'input dialog', '请输入歌曲名称?', text = txt)
    if ok:
        song_title = text
    else:
        return
    set_song_title = lambda self:getattr(self,f'comboBox_song{self.which_song_widget}').setCurrentText(text)
    cbs = [extract_all_song_titles, set_song_title]
    collection = 'song_info'
    constrain = {'song_id': song_title}
    if self.database[collection].count_documents(constrain)==1:
        update_one_record(self, 'PPT', collection, constrain= constrain, cbs=cbs)
    elif self.database[collection].count_documents(constrain)==0:
        add_one_record(self, 'PPT', collection, extra_info= constrain, cbs=cbs)

def delete_one_song(self, song_title):
    delete_one_record(self, self.database_type, {'song_id': song_title})

def set_data_for_x_song_script_note(self, content):
    #collection = 'song_info'
    txtEditWidgetName = f'textEdit_song{self.which_song_widget}_note'
    # txtEditWidgetName = f'textEdit_song1_note'
    #comboWidgetName = f'comboBox_song{self.which_song_widget}'
    #constrain = {'song_id': getattr(self, comboWidgetName).currentText()}
    #data = self.database[collection].find_one(constrain)
    #format_html = '<p style="color:white;margin:0px;font-size:18px">{}</p>'.format
    getattr(self, txtEditWidgetName).setPlainText(content)

def get_data_for_x_song_script_note(self):
    txtEditWidgetName = f'textEdit_song{self.which_song_widget}_note'
    return getattr(self, txtEditWidgetName).toPlainText()

def set_data_for_x_song_items_note(self, content):
    '''
    month = self.comboBox_ppt_month.currentText()
    year = datetime.date.today().year
    week_map = [('第一周','1st_week'),('第二周','2nd_week'),('第三周','3rd_week'),('第四周','4th_week'),('第五周','5th_week')]
    week = week_map[self.comboBox_ppt_week.currentText()]
    group_id = f'{year}_{month}+{week}'    
    constrain = {'group_id': group_id}
    data = self.database[collection].find_one(constrain)['song_items'].rsplit(',')
    '''
    data = content.rsplit(',')
    for i in range(len(data)):
        getattr(self, f'comboBox_song{i+1}').setCurrentText(data[i])
    
def get_data_for_x_song_items_note(self):
    songs = []
    for i in range(4):
        songs.append(getattr(self, f'comboBox_song{i+1}').currentText())
    return ','.join(songs)

def set_data_for_x_workers_note(self, db_name = 'ccg-task'):
    def _next_week(this_week, month, year):
        nextweek = None
        if this_week.startswith('5'):
            nextweek = '1st_week'
            month = str(int(int(month)+1))
            if month=='13':
                month = '1'
                year = str(int(int(year) + 1))
            else:
                pass
            return year, month, nextweek
        else:
            nextweek = ['2nd_week', '3rd_week','4th_week','5th_week'][int(this_week[0])-1]
            return year, month, nextweek
        
    collection_widget_map = dict([
                                  ('topic_info','lineEdit_topic_info'),
                                  ('preacher_info','lineEdit_preacher_info'),
                                  ('hoster_info','lineEdit_hoster_info'),
                                  ('piano_info','lineEdit_piano_info'),
                                  ('song_leader_info','lineEdit_song_leader_info'),
                                  ('main_actioner_info','lineEdit_main_actioner_info'),
                                  ('teenage_info','lineEdit_teenage_info'),
                                  ('kid_info','lineEdit_kid_info'),
                                  ('baby_info','lineEdit_baby_info'),
                                  ('ppt_info','lineEdit_ppt_info')
                                ])
    
    month = self.comboBox_ppt_month.currentText()
    year = datetime.date.today().year
    week_map = dict([('第一周','1st_week'),('第二周','2nd_week'),('第三周','3rd_week'),('第四周','4th_week'),('第五周','5th_week')])
    week = week_map[self.comboBox_ppt_week.currentText()]
    year_, month_, nextweek = _next_week(week, month, year)
    group_id_next_week = f'{year_}_{month_}'
    group_id = f'{year}_{month}'
    constrain = {'group_id':group_id}
    constrain_next_week = {'group_id':group_id_next_week}
    database = self.mongo_client[db_name]
    collection_names = database.list_collection_names()
    for key, widget in collection_widget_map.items():
        if key in collection_names:
            value = database[key].find_one(constrain)
            value_next_week = database[key].find_one(constrain_next_week)
            if value!=None:
                getattr(self, widget).setText(value[week])
            if value_next_week!=None:
                getattr(self, widget+'2').setText(value_next_week[nextweek])

def get_data_for_x_workers_note(self):
    #do nothing
    pass

def update_selected_PPT_info(self, index = None):
    group_id = self.pandas_model_paper_info._data['group_id'].tolist()[index.row()]
    y_m, week = group_id.rsplit('+')
    y, m = y_m.rsplit('_')
    week_map = dict([('1st_week','第一周'),('2nd_week','第二周'),('3rd_week','第三周'),('4th_week','第四周'),('5th_week','第五周')])
    self.comboBox_ppt_month.setCurrentText(m)
    self.comboBox_ppt_week.setCurrentText(week_map[week])
    collection =  'ppt_info'
    constrain = {'group_id': group_id}
    extract_one_record(self, self.database_type, collection, constrain)

def save_ppt_content_in_txt_format(self):
    year, month = str(datetime.date.today().year), self.comboBox_ppt_month.currentText()
    day = get_date_from_nth_week(self.comboBox_ppt_week.currentText(),int(month))
    txt_file_name_end = f'_{year}-{month}-{day}.txt'
    #content_folder = Path(__file__).parent.parent.parent / 'ppt_worker' / 'src' / 'contents'
    content_folder = Path.home() / 'pygodAppData' / 'content_files'
    content_folder.mkdir(parents=True, exist_ok=True)
    date_next_sunday = datetime.datetime(int(year), int(month), int(day)) + timedelta(days=7)
    year_nw, month_nw, day_nw = date_next_sunday.year, date_next_sunday.month, date_next_sunday.day
    year, month, day = int(year), int(month), int(day)
    #save worker list
    widget_names = [('主题：','lineEdit_topic_info'),
                   ('证道：','lineEdit_preacher_info'),
                   ('司会：','lineEdit_hoster_info'),
                   ('司琴：','lineEdit_piano_info'),
                   ('领唱：','lineEdit_song_leader_info'),
                   ('主领执事：','lineEdit_main_actioner_info'),
                   ('少年主日学：','lineEdit_teenage_info'),
                   ('少儿主日学：','lineEdit_kid_info'),
                   ('幼儿主日学：','lineEdit_baby_info'),
                   ('PPT制作播放：','lineEdit_ppt_info')]
    with open(content_folder / ('worker_list'+txt_file_name_end), 'w', encoding='utf-8') as f:
        f.write("#1\n{} 年 {:02d} 月 {:02d} 日主日服事表\n".format(year, month, day))
        for label,each in widget_names:
            if label!='主题：':
                f.write(label+getattr(self, each).text().replace('+','、')+'\n')
            else:
                f.write(label+getattr(self, each).text()+'\n')
        f.write("#2\n{} 年 {:02d} 月 {:02d} 日主日服事表\n".format(year_nw, month_nw, day_nw))
        for label,each in widget_names:
            if label!='主题：':
                f.write(label+getattr(self, each+'2').text().replace('+','、')+'\n')
            else:
                f.write(label+getattr(self, each+'2').text()+'\n')            
    #save pray list
    with open(content_folder / ('pray_list'+txt_file_name_end), 'w', encoding='utf-8') as f:
        f.write(self.textEdit_pray_note.toPlainText())
    # save scripture list
    with open(content_folder / ('scripture_list'+txt_file_name_end), 'w', encoding='utf-8') as f:
        f.write(self.textEdit_scripture_note.toPlainText())    
    # save song list
    with open(content_folder / ('song_list'+txt_file_name_end), 'w', encoding='utf-8') as f:
        for i in range(1,5):
            f.write(f'#{i}\n')
            f.write(getattr(self, f'textEdit_song{i}_note').toPlainText())  
            f.write('\n')
    # save preach info
    with open(content_folder / ('preach_list'+txt_file_name_end), 'w', encoding='utf-8') as f:
        f.write(self.textEdit_preach_note.toPlainText())      
    # save report 
    with open(content_folder / ('report_list'+txt_file_name_end), 'w', encoding='utf-8') as f:
        f.write(self.textEdit_report_note.toPlainText())      
    #now create ppt file
    try:
        v = ['2','1'][int(self.comboBox_song_holy_dinner.currentText()=='靠近十架')]
        ppt(f'{year}-{month}-{day}',v, content_folder)
        error_pop_up(f"The ppt file is created and saved in {str(content_folder)}", 'Information')
    except Exception as e:
        error_pop_up(f'ERROR: {e}', 'Error')

def query_paper_info_for_paper_id(self, field, query_string):
    field =  map_chinese_to_eng_key(field)
    return_list = general_query_by_field(self, field, query_string, target_field='paper_id',collection_name = 'paper_info')
    if len(return_list)!=0:
        self.comboBox_books.setCurrentText(return_list[0])
        extract_paper_info(self)
    else:
        error_pop_up('Nothing return')

def general_query_by_field(self, field, query_string, target_field, collection_name, database = None):
    """
    Args:
        field ([string]): in ['author','book_name','book_id','status','class']
        query_string ([string]): [the query string you want to perform, e.g. 1999 for field = 'year']
        target_filed([string]): the targeted filed you would like to extract
        collection_name([string]): the collection name you would like to target

    Returns:
        [list]: [value list of target_field with specified collection_name]
    e.g.
    general_query_by_field(self, field='name', query_string='jackey', target_field='email', collection_name='user_info')
    means I would like to get a list of email for jackey in user_info collection in the current database
    """

    if database == None:
        database = self.database
    index_name = database[collection_name].create_index([(field,'text')])
    targets = database[collection_name].find({"$text": {"$search": "\"{}\"".format(query_string)}})
    #drop the index afterwards
    return_list = [each[target_field] for each in targets]
    # self.database.paper_info.drop_index(index_name)
    database[collection_name].drop_index(index_name)
    return return_list  

#api functions for bulletin creator
def extract_bulletin_record(self):
    month = self.comboBox_bulletin_month.currentText()
    year = datetime.date.today().year
    group_id = f'{year}_{month}'
    constrain = {'group_id':group_id}    
    extract_one_record(self, self.database_type, 'bulletin_info', constrain)
    extract_one_record(self, self.database_type, 'attendence_info_sunday', constrain)
    extract_one_record(self, self.database_type, 'attendence_info_bible_study', constrain)
    extract_one_record(self, self.database_type, 'year_scripture', {'group_id':str(year)})

def delete_bulletin_record(self):
    month = self.comboBox_bulletin_month.currentText()
    year = datetime.date.today().year
    group_id = f'{year}_{month}'
    delete_one_record(self, self.database_type, {'group_id':group_id}, cbs = [partial(clear_all_text_field, tabWidget='tabWidget_bulletin'), init_pandas_model_from_db])

def add_one_bulletin_record(self):
    month = self.comboBox_bulletin_month.currentText()
    year = datetime.date.today().year
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
    # return '\n'.join(contents_formated)

def get_finance_content(self, key):
    year, month = str(datetime.date.today().year), self.comboBox_bulletin_month.currentText()
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
    group_id = self.pandas_model_paper_info._data['group_id'].tolist()[index.row()]
    _, m = group_id.rsplit('_')
    self.comboBox_bulletin_month.setCurrentText(m)
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
    year, month = str(datetime.date.today().year), self.comboBox_bulletin_month.currentText()
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
    