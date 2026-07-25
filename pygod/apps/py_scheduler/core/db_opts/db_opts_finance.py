import datetime
import re
from ..db_opts.common_db_opts import *
from ..graph_operations import create_piechart
from openpyxl import Workbook, load_workbook

def load_content_from_excel_file(self):
    file = self.lineEdit_excel_file_path.text()
    income_dict = {}
    expense_dict = {}
    # data_only=True reads cached computed values so formula cells return numbers/strings
    # rather than the formula text itself.  A second workbook (raw formulas) serves as
    # fallback for the rare case where a cell's cached value is absent (file never
    # re-saved after formula entry) — we then manually resolve simple & -concat formulas.
    ws_data = load_workbook(file, data_only=True).active
    ws_raw  = load_workbook(file).active

    def _resolve(coord):
        val = ws_data[coord].value
        if val is not None:
            return val
        raw = ws_raw[coord].value
        if not isinstance(raw, str) or not raw.startswith('='):
            return raw
        parts = raw[1:].split(' & ')
        result = []
        for part in parts:
            part = part.strip()
            if part.startswith('"') and part.endswith('"'):
                result.append(part[1:-1])
            else:
                try:
                    result.append(str(ws_raw[part].value))
                except Exception:
                    result.append(part)
        return ''.join(result)

    pointer = 2
    while True:
        label = _resolve(f'B{pointer}')
        if label is None:
            break
        income_dict[label] = _resolve(f'C{pointer}')
        pointer += 1
    pointer += 2
    while True:
        label = _resolve(f'B{pointer}')
        if label is None:
            break
        expense_dict[label] = _resolve(f'D{pointer}')
        pointer += 1

    for i, key in enumerate(income_dict):
        if i > 6:
            error_pop_up('There are more than 7 items in the income. Cut off items>7. You should manually add them')
            break
        getattr(self, f'lineEdit_income_{i+1}_note').setText(str(key))
        getattr(self, f'lineEdit_income_{i+1}').setText(str(income_dict[key]))
    for i, key in enumerate(expense_dict):
        if i > 16:
            error_pop_up('There are more than 17 items in the expense. Cut off items>17. You should manually add them')
            break
        getattr(self, f'lineEdit_expense_{i+1}_note').setText(str(key))
        getattr(self, f'lineEdit_expense_{i+1}').setText(str(expense_dict[key]))

    load_bulletin_footnote_figures(self, ws_data)

def load_bulletin_footnote_figures(self, ws):
    """Pull the year-to-date row and the fund/deficit figures that the bulletin footnote
    quotes.  They sit under the monthly item block in loosely fixed positions — the
    treasurer moves them around between months — so anchor on the label text in column
    A/B and read the numbers from the columns to its right."""
    def _num(row, col):
        try:
            return float(ws.cell(row=row, column=col).value)
        except (TypeError, ValueError):
            return None

    def _set(widget, value):
        if value is not None:
            getattr(self, widget).setText(str(round(value, 2)))

    labels = {}
    for row in ws.iter_rows(min_col=1, max_col=2):
        for cell in row:
            if isinstance(cell.value, str) and cell.value.strip():
                labels.setdefault(cell.row, cell.value.strip())
    rows = sorted(labels)

    def find(pred, after=0):
        for r in rows:
            if r > after and pred(labels[r]):
                return r
        return None

    #'2026年 (1-6月份)' — the row right under the monthly one
    row_ytd = find(lambda t: re.match(r'^\d{4}\s*年\s*\(?\s*1-\d+\s*月', t))
    if row_ytd:
        _set('lineEdit_ytd_total_income', _num(row_ytd, 3))
        _set('lineEdit_ytd_total_expense', _num(row_ytd, 4))
        _set('lineEdit_ytd_net_income', _num(row_ytd, 5))

    #'堂址维护基金截至到6月31日总进为' / '总支为' … '结余为' on the same row, else the
    #standalone '建堂基金结余：' row further down
    row_building = find(lambda t: '堂址维护基金' in t and '总进' in t)
    if row_building:
        _set('lineEdit_fund_building_income', _num(row_building, 3))
        row_expense = find(lambda t: '总支' in t, row_building)
        balance = None
        if row_expense:
            _set('lineEdit_fund_building_expense', _num(row_expense, 3))
            balance = _num(row_expense, 5)
        if balance is None:
            row_balance = find(lambda t: '结余' in t, row_expense or row_building)
            balance = _num(row_balance, 3) if row_balance else None
        _set('lineEdit_fund_building_balance', balance)

    row_seminary = find(lambda t: '神学教育基金' in t)
    if row_seminary:
        row_support = find(lambda t: 'Bremen' in t or '神学生' in t, row_seminary)
        if row_support:
            _set('lineEdit_fund_seminary_expense', _num(row_support, 3))
        row_balance = find(lambda t: '结余' in t, row_support or row_seminary)
        if row_balance:
            _set('lineEdit_fund_seminary_balance', _num(row_balance, 3))

    row_mission = find(lambda t: '广传事工基金' in t or '宣教广传' in t)
    if row_mission:
        row_balance = find(lambda t: '结余' in t, row_mission)
        if row_balance:
            _set('lineEdit_fund_mission_balance', _num(row_balance, 3))

    #the cumulative deficit is the last '<year>年结余' row — '2025年年结余' above it is
    #only the carried-over part, so take the bottom-most match
    candidates = [r for r in rows if re.match(r'^\d{4}\s*年结余', labels[r])]
    if candidates:
        _set('lineEdit_accumulated_deficit', _num(candidates[-1], 3))

def init_pandas_model_from_db(self):
    args = {'self': self, 
            'tab_indx': 3, 
            'single_collection': True, 
            'contrains': [], 
            'onclicked_func': update_selected_finance_info}
    init_pandas_model_from_db_base(**args)

def load_db_fin(self, **kwargs):
    init_pandas_model_from_db(self)

# apis for finance info
def add_finance_info(self):
    calculate_sum(self)
    cbs = [init_pandas_model_from_db]
    collection = 'finance_info'
    month = self.comboBox_finance_month.currentText()
    #year = datetime.date.today().year
    year = self.lineEdit_year_finance.text()
    group_id = f'{year}_{month}'
    if self.database[collection].count_documents({'group_id': group_id})==1:
        update_one_record(self, '财务', collection, constrain= {'group_id': group_id}, cbs=cbs)
    elif self.database[collection].count_documents({'group_id': group_id})==0:
        add_one_record(self, '财务', collection, extra_info= {'group_id': group_id}, cbs=cbs)

def update_selected_finance_info(self, index = None):
    group_id = self.pandas_model._data['group_id'].tolist()[index.row()]
    self.comboBox_finance_month.setCurrentText(group_id.rsplit('_')[-1])
    self.lineEdit_year_finance.setText(group_id.rsplit('_')[0])
    collection =  'finance_info'
    constrain = {'group_id': group_id}
    extract_one_record(self, self.database_type, collection, constrain)
    create_piechart(self)

def delete_finance_info(self):
    month = self.comboBox_finance_month.currentText()
    year = self.lineEdit_year_finance.text()
    # year = datetime.date.today().year
    group_id = f'{year}_{month}'
    delete_one_record(self, self.database_type, {'group_id':group_id}, cbs = [init_pandas_model_from_db])

def calculate_sum(self, total_income_widget = 'lineEdit_total_income', total_expense_widget = 'lineEdit_total_expense', net_income_widget = 'lineEdit_net_income'):
    income = 0
    expense = 0
    income_widgets = [f'lineEdit_income_{i}' for i in range(1,8)]
    expense_widgets = [f'lineEdit_expense_{i}' for i in range(1,18)]

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
