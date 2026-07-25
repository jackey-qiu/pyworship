from ..util import error_pop_up, clear_all_text_field, get_dates_for_one_month
import datetime
from pathlib import Path
from functools import partial
from .common_db_opts import *
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import Qt
from pygod.apps.bulletin_worker.scripts.bulletin_worker import main as bulletin
import locale
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

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

#not per-item lines: these feed the year-to-date summary row and the footnote under the
#finance table, and are emitted as '@'-tagged rows instead of income/expense entries
FOOTNOTE_FIELDS = ['ytd_total_income', 'ytd_total_expense', 'ytd_net_income',
                   'accumulated_deficit', 'fund_building_income', 'fund_building_expense',
                   'fund_building_balance', 'fund_seminary_expense', 'fund_seminary_balance',
                   'fund_mission_balance']

def get_finance_content(self, key):
    def _format_num(value):
        tmp = locale.currency(float(value),grouping=True)
        comma_ix = tmp.index(',')
        tmp = list(tmp.replace('.',','))
        tmp[comma_ix] = '.'
        return ''.join(tmp)
    #the summary row is labelled with the month the numbers actually come from,
    #which is the month encoded in `key` (e.g. '2026_6月'), not the bulletin month
    year, month = key.split('_')
    month = month.rstrip('月')
    collection = 'finance_info'
    docs =  list(get_document_info_from_yaml(self, '财务', collection).keys())
    db_temp = self.mongo_client[self.lineEdit_db_finance.text()]
    income = []
    expense = []
    summary = [f'{year}年{month}月份']
    for doc in ['total_income','total_expense','net_income']:
        sign = '+' if doc=='total_income' else '-'
        
        value = float(text_query_by_field(self, 'group_id', key, doc, collection, db_temp)[0])
        if doc=='net_income':
            if value<=0:
                sign = ''
            else:
                sign = '+'
        # summary.append(sign+locale.currency(value,grouping=True))
        summary.append(sign+_format_num(value))
    for doc in docs:
        if not doc.endswith('note'):
            if doc not in ['total_income','total_expense','net_income'] + FOOTNOTE_FIELDS:
                value = text_query_by_field(self, 'group_id', key, doc, collection, db_temp)
                note = text_query_by_field(self, 'group_id', key, doc+'_note', collection, db_temp)
                if note == ['']:
                    note = [doc]
                if doc.startswith('income'):
                    if float(value[0])!=0:
                        income.append([note[0], '+'+_format_num(value[0])])
                else:
                    if float(value[0])!=0:
                        expense.append([note[0], '-'+_format_num(value[0])])
    income = '\n'.join(['&'.join(each) for each in income])
    expense = '\n'.join(['&'.join(each) for each in expense])
    summary = '&'.join(list(map(str,summary)))
    footnote = _get_footnote_rows(self, key, collection, db_temp, _format_num)
    return '\n'.join([income, expense, summary] + footnote)

def _get_footnote_rows(self, key, collection, db_temp, format_num):
    """The '@'-tagged tail of the FinanceTable block: the year-to-date summary row plus
    the fund and deficit figures quoted underneath the table.  Older finance records
    predate these fields - a missing one drops its whole row, and the bulletin worker
    then falls back to the '???' placeholder for that line."""
    year, month = key.split('_')
    month = month.rstrip('月')

    def _amount(doc, sign_mode):
        #the footnote quotes magnitudes ('总支为X欧', '赤字为X欧'), so those get 'abs';
        #the year-to-date row keeps the +/- columns of the monthly summary row above it
        value = float(text_query_by_field(self, 'group_id', key, doc, collection, db_temp)[0])
        if sign_mode == 'abs':
            return format_num(abs(value))
        if sign_mode == 'plus':
            return '+' + format_num(abs(value))
        if sign_mode == 'minus':
            return '-' + format_num(abs(value))
        return ('+' if value > 0 else '') + format_num(value)

    rows = []
    tagged = [('summary_ytd', [f'{year}年度（1-{month}月)'],
               [('ytd_total_income', 'plus'), ('ytd_total_expense', 'minus'),
                ('ytd_net_income', 'auto')]),
              ('deficit', [], [('accumulated_deficit', 'abs')]),
              ('fund_building', [], [('fund_building_income', 'abs'), ('fund_building_expense', 'abs'),
                                     ('fund_building_balance', 'abs')]),
              ('fund_seminary', [], [('fund_seminary_expense', 'abs'), ('fund_seminary_balance', 'abs')]),
              ('fund_mission', [], [('fund_mission_balance', 'abs')])]
    for tag, prefix, fields in tagged:
        try:
            values = [_amount(doc, sign_mode) for doc, sign_mode in fields]
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        rows.append('&'.join([f'@{tag}'] + prefix + values))
    return rows

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

def find_unassigned_services(service_content, preach_content):
    """collect the '日期 服事' slots that are still empty in the next month's schedule

    both arguments are the csv-like blocks produced by get_task_content and
    get_preach_content, whose first line always holds the sunday dates
    """
    missing = []
    def _scan(content, has_row_title, row_titles = None):
        lines = [each for each in content.rsplit('\n') if each.strip()!='']
        if len(lines)<2:
            return
        dates = lines[0].rsplit(',')
        if has_row_title:
            dates = dates[1:]
        for i, line in enumerate(lines[1:]):
            cells = line.rsplit(',')
            if has_row_title:
                title, values = cells[0], cells[1:]
            else:
                title = row_titles[i] if i<len(row_titles) else f'第{i+1}行'
                values = cells
            #a service with no db record at all comes back as a short row
            values = values + ['']*(len(dates)-len(values))
            for date, value in zip(dates, values):
                if value.strip()=='':
                    missing.append(f'{date}　{title}')
    _scan(service_content, True)
    _scan(preach_content, False, ['讲题','讲员','经文'])
    return missing

def confirm_unassigned_services(self, missing, max_shown = 20):
    shown = missing[0:max_shown]
    msg = '以下服事尚未安排：\n\n' + '\n'.join(shown)
    if len(missing)>max_shown:
        msg = msg + f'\n... 还有 {len(missing)-max_shown} 项'
    msg = msg + '\n\n仍然生成月报？（空缺处将留白）'
    reply = QMessageBox.question(self, 'Message', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    return reply == QMessageBox.Yes

def make_progress_dialog(self, title = '月报'):
    """a modal bar for the doc generation, which runs on the gui thread"""
    bar = QProgressDialog('正在生成月报…', None, 0, 100, self)
    bar.setWindowTitle(title)
    bar.setWindowModality(Qt.WindowModal)
    bar.setCancelButton(None)
    bar.setAutoClose(False)
    bar.setAutoReset(False)
    bar.setMinimumDuration(0)
    #wide enough that the step labels are not elided down to '正在调整行距...'
    bar.setMinimumWidth(360)
    bar.setValue(0)
    QApplication.processEvents()
    return bar

def update_progress_dialog(bar, step, total, message):
    bar.setMaximum(total)
    bar.setValue(step)
    bar.setLabelText(message)
    #the generation blocks the gui thread, so repaint by hand between the steps
    QApplication.processEvents()

def save_bulletin_content_in_txt_format_and_make_bulletin(self, create_file = True):
    year = int(self.lineEdit_year_bulletin.text())
    month = int(self.comboBox_bulletin_month.currentText())
    year_next_month = year if month!=12 else year + 1
    year_pre_month = year if month!=1 else year - 1
    next_month = month + 1 if month!=12 else 1
    pre_month = month - 1 if month!=1 else 12
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
                  'PreachTable':'preach_content',
                  'MonthlyServiceTable':'service_content',
                  'FinanceTable':f"get_finance_content(self, '{year_pre_month}_{pre_month}月')"
                  }
    try:
        #pull next month's schedule up front so the empty slots can be reported before anything is written
        service_content = get_task_content(self, f'{year_next_month}_{next_month}')
        preach_content = get_preach_content(self, f'{year_next_month}_{next_month}')
        missing = find_unassigned_services(service_content, preach_content)
        if len(missing)>0 and not confirm_unassigned_services(self, missing):
            return
        if create_file:
            with open(str(content_folder / txt_file_name), 'w', encoding='utf-8') as f:
                for content_type in content_types:
                    f.write(f"<{content_type}>\n{eval(api_map[content_type])}\n</{content_type}>\n")
                    # if content_type == 'MonthlyServiceTable':
                        # print(eval(api_map[content_type]))
                        # print('\n\n')
                        # print(get_task_content(self,f'{year_next_month}_{next_month}'))
        #making the doc takes half a minute or so - word is asked to lay it out several
        #times over - so show how far along it is instead of freezing on a dead window
        bar = make_progress_dialog(self)
        try:
            bulletin(year, month, str(content_folder / txt_file_name), str(content_folder / doc_file_name),
                     progress=partial(update_progress_dialog, bar))
        finally:
            bar.close()
        error_pop_up(f"{doc_file_name} created and saved in {str(content_folder)}", 'Information')
    except Exception as e:
        error_pop_up(f'ERROR: {e}', 'Error')