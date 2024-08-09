import datetime
from ..db_opts.common_db_opts import *
from ..graph_operations import create_piechart

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
    income_widgets = ['lineEdit_income_offering_onside','lineEdit_income_offering_online',
                      'lineEdit_income_offering_lubeck','lineEdit_income_offering_kiel',
                      'lineEdit_income_offering_korea','lineEdit_income_offering_others','lineEdit_income_offering_others2']
    expense_widgets = ['lineEdit_expense_pastor_wu','lineEdit_expense_pastor_guan','lineEdit_expense_pastor_chuandao',
                       'lineEdit_expense_kiel','lineEdit_expense_lubeck','lineEdit_expense_nebenkosten','lineEdit_expense_software_subscribe',
                       'lineEdit_expense_other_cost_1', 'lineEdit_expense_other_cost_2','lineEdit_expense_other_cost_3',
                       'lineEdit_expense_other_cost_4','lineEdit_expense_other_cost_5',
                       'lineEdit_expense_other_cost_6','lineEdit_expense_other_cost_7',
                       'lineEdit_expense_other_cost_8','lineEdit_expense_other_cost_9','lineEdit_expense_other_cost_10']
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
