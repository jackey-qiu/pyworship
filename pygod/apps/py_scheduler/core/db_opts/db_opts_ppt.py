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
            'tab_indx': 4, 
            'single_collection': True, 
            'contrains': [], 
            'onclicked_func': update_selected_PPT_info}
    init_pandas_model_from_db_base(**args)

def load_db_ppt(self, **kwargs):
    init_pandas_model_from_db(self)
    extract_all_song_titles(self)

#api funcs for ppt worker
def clear_all_text_field(self, tabWidget = 'tabWidget_note'):
    for each in getattr(self, tabWidget).findChildren(QLineEdit):
        each.setText('')
    for each in getattr(self, tabWidget).findChildren(QTextEdit):
        each.setPlainText('')
    
def extract_ppt_record(self):
    month = self.comboBox_ppt_month.currentText()
    year = self.lineEdit_year_bulletin.text()
    #year = datetime.date.today().year
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
    year = self.lineEdit_year_bulletin.text()
    # year = datetime.date.today().year
    week_map = dict([('第一周','1st_week'),('第二周','2nd_week'),('第三周','3rd_week'),('第四周','4th_week'),('第五周','5th_week')])
    week = week_map[self.comboBox_ppt_week.currentText()]
    group_id = f'{year}_{month}+{week}'
    delete_one_record(self, self.database_type, {'group_id':group_id}, cbs = cbs)

def add_one_ppt_record(self):
    month = self.comboBox_ppt_month.currentText()
    year = self.lineEdit_year_bulletin.text()
    # year = datetime.date.today().year
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
    # songs = [each['song_id'] for each in self.database.song_info.find()]
    songs = [each['name'] for each in self.mongo_client['ccg-hymn'].hymn_info.find()]
    self.songs = songs
    for i in range(1, 5):
        getattr(self,f'comboBox_song{i}').clear()
        getattr(self,f'comboBox_song{i}').addItems(songs)

def add_one_song_title_to_cache(self, song_title):
    self.songs.append(song_title)
    for i in range(1, 5):
        getattr(self,f'comboBox_song{i}').addItem(song_title)

def extract_targeted_songs_from_cache(self, signature, comboBox_widget):
    if not hasattr(self, 'songs'):
        return
    targeted_songs = [each for each in self.songs if each.startswith(signature)]
    comboBox_widget.clear()
    comboBox_widget.addItems(targeted_songs)

def extract_one_song(self, song_title, which):
    self.which_song_widget = which
    #extract record from ccg-hymn database
    extract_one_record(self, '诗歌', 'hymn_info', {'name': song_title}, db='ccg-hymn')
    #transfer the text from hymn tab to ppt tab
    getattr(self, f'textEdit_song{which}_note').setPlainText(self.textEdit_script_ppt_note.toPlainText())

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
    year = self.lineEdit_year_ppt.text()
    # year = datetime.date.today().year
    week_map = dict([('第一周','1st_week'),('第二周','2nd_week'),('第三周','3rd_week'),('第四周','4th_week'),('第五周','5th_week')])
    week = week_map[self.comboBox_ppt_week.currentText()]
    year_, month_, nextweek = _next_week(week, month, int(year))
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
    group_id = self.pandas_model._data['group_id'].tolist()[index.row()]
    y_m, week = group_id.rsplit('+')
    y, m = y_m.rsplit('_')
    week_map = dict([('1st_week','第一周'),('2nd_week','第二周'),('3rd_week','第三周'),('4th_week','第四周'),('5th_week','第五周')])
    self.comboBox_ppt_month.setCurrentText(m)
    self.lineEdit_year_ppt.setText(y)
    self.comboBox_ppt_week.setCurrentText(week_map[week])
    collection =  'ppt_info'
    constrain = {'group_id': group_id}
    extract_one_record(self, self.database_type, collection, constrain)

def save_ppt_content_in_txt_format(self):
    year = self.lineEdit_year_bulletin.text()
    month = self.comboBox_ppt_month.currentText()
    day = get_date_from_nth_week(self.comboBox_ppt_week.currentText(),int(month), year = int(year))
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