import os, datetime
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from pathlib import Path
from pymongo import MongoClient
import certifi, urllib
from ..core.util import error_pop_up, confirm_password, encrypt_password
from ..config.config import hidden_pushButtons_normal_user
from ..core.db_opts import common_db_opts as db

ui_path = str(Path(__file__).parent.parent/ "ui")

class NewProject(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Load the dialog's GUI
        uic.loadUi(os.path.join(ui_path,"new_project_dialog.ui"), self)
        self.pushButton_ok.clicked.connect(lambda:self._creat_a_new_project( parent = parent,
                                                                            name_db = self.lineEdit_name.text(), 
                                                                            db_info = self.textEdit_introduction.toPlainText(),
                                                                            type_db = self.comboBox_type.currentText()))
        self.pushButton_cancel.clicked.connect(lambda:self.close())

    def _creat_a_new_project(self,parent, name_db, db_info, type_db):
        parent.database = parent.mongo_client[name_db]
        parent.database.project_info.insert_many([{'project_info':db_info, 'db_type': type_db}])
        parent.comboBox_project_list.clear()
        parent.comboBox_project_list.addItems(parent.mongo_client.list_database_names())
        parent.comboBox_project_list.setCurrentText(name_db)
        #extract project info
        all = parent.database.project_info.find()
        parent.plainTextEdit_project_info.setPlainText('\n'.join([each['project_info'] for each in all]))

class LendDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Load the dialog's GUI
        uic.loadUi(os.path.join(ui_path,"lend_book_dialogue.ui"), self)
        self.lineEdit_book_name.setText(parent.lineEdit_book_name.text())
        self.lineEdit_borrower.setText(parent.name)
        self.pushButton_lend.clicked.connect(lambda:self.lend(parent))

    def lend(self, parent):
        if parent.lineEdit_status.text() not in ['预约','在馆']:
            error_pop_up('该书已经被借出！')
            return
        parent.lineEdit_borrower.setText(self.lineEdit_borrower.text())
        parent.lineEdit_status.setText('借出')
        parent.lineEdit_lend_date.setText(datetime.datetime.today().strftime('%Y-%m-%d'))
        parent.pushButton_update.click()
        parent.statusbar.clearMessage()
        parent.statusbar.showMessage('The book is lent to {} successfully:-)'.format(self.lineEdit_borrower.text()))
        self.close()

class LoginDialog(QDialog):
    def __init__(self, parent=None, url=''):
        super().__init__(parent)
        # Load the dialog's GUI
        uic.loadUi(os.path.join(ui_path,"login_dialogue.ui"), self)
        self.pushButton_login.clicked.connect(lambda:self.login(parent, url))

    def login(self, parent, url):
        url_complete = url.format(self.lineEdit_login_name.text(),urllib.parse.quote(self.lineEdit_password.text().encode('utf-8')))
        try:
            client = MongoClient(url_complete,tlsCAFile=certifi.where())
            parent.mongo_client = client
            parent.comboBox_project_list.clear()
            relevant_database_names = []
            for each in parent.mongo_client.list_database_names():
                if 'ccg' in each:
                    relevant_database_names.append(each)
            parent.comboBox_project_list.addItems(relevant_database_names)
            # client['ccg-book'].user_info[]
            names = db.text_query_by_field(self=parent, field='user_name', query_string=self.lineEdit_login_name.text(),target_field='name',collection_name='user_info', database=client['ccg-book'])
            roles = db.text_query_by_field(self=parent, field='user_name', query_string=self.lineEdit_login_name.text(),target_field='role',collection_name='user_info', database=client['ccg-book'])
            #salts = db.general_query_by_field(self=parent, field='user_name', query_string=self.lineEdit_login_name.text(),target_field='salt',collection_name='user_info', database=client['ccg-book'])
            if len(names)==0:
                name = self.lineEdit_login_name.text()
            else:
                name = names[0]
            parent.user_name = self.lineEdit_login_name.text()
            parent.name = name
            if len(roles)!=0:
                role = roles[0]
                parent.role = role
            else:
                role = 'undefined role'
            if role!='admin':
                for each in hidden_pushButtons_normal_user:
                    getattr(parent,'pushButton_'+each).hide()
            parent.statusLabel.setText('Welcome {}, you are logged in to ccg-lib system as a {}!'.format(name, parent.role))
            self.close()
        except Exception as e:
            error_pop_up('login info is incorrect. Try again!'+str(e))

class RegistrationDialog(QDialog):
    def __init__(self, parent=None, url=''):
        super().__init__(parent)
        # Load the dialog's GUI
        uic.loadUi(os.path.join(ui_path,"registration_dialogue.ui"), self)
        self.pushButton_submit.clicked.connect(lambda:self.submit(url))

    def submit(self, url):
        if self.lineEdit_password.text()!=self.lineEdit_password_confirm.text():
            error_pop_up('Two typed passwords are not matched. Try again please!')
            return
        url_complete = url.format('public_user','VgIDSIGw7UDcWIcL')
        user_info = {
                    'user_name':self.lineEdit_login_name.text(),
                    'name':self.lineEdit_name.text(),
                    'email':self.lineEdit_email.text(),
                    'password':self.lineEdit_password.text(),
                    'role':'new',
                    }
        try:
            client = MongoClient(url_complete,tlsCAFile=certifi.where())
            database = client['ccg-book']
            all_info = list(database.user_info.find({},{'_id':0}))
            user_name_list = [each['user_name'] for each in all_info]

            if self.lineEdit_login_name.text() in user_name_list:
                error_pop_up('User name exited, please use another user name!')
            else:
                database.user_info.insert_one(user_info)
                error_pop_up('You are all set. Wait for administrator to grant you access to the ccg-book database in patience!')
                self.close()
        except Exception as e:
            error_pop_up('Failure to append new user info!\n{}'.format(str(e)),'Error')

class ReturnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Load the dialog's GUI
        uic.loadUi(os.path.join(ui_path,"return_book_dialogue.ui"), self)
        self.lineEdit_book_name.setText(parent.lineEdit_book_name.text())
        self.lineEdit_borrower.setText(parent.lineEdit_borrower.text())
        self.pushButton_return.clicked.connect(lambda:self.return_(parent))

    def return_(self, parent):
        #parent.lineEdit_borrower.setText(self.lineEdit_borrower.text())
        if parent.lineEdit_status.text() != '借出':
            print('hello')
            error_pop_up('该书已经被预约.')
            return
        parent.lineEdit_status.setText('在馆')
        parent.lineEdit_return_date.setText(datetime.datetime.today().strftime('%Y-%m-%d'))
        parent.pushButton_update.click()
        parent.statusbar.clearMessage()
        parent.statusbar.showMessage('The book is returned by {} successfully:-)'.format(self.lineEdit_borrower.text()))
        self.close()

class QueryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Load the dialog's GUI
        uic.loadUi(os.path.join(ui,"query_dialog.ui"), self)
        self.pushButton_clear.clicked.connect(self.clear_fields)
        self.pushButton_search.clicked.connect(self.search)
        self.pushButton_exit.clicked.connect(lambda:self.close())
    
    def clear_fields(self):
        self.lineEdit_title.setText('')
        self.lineEdit_abstract.setText('')
        self.lineEdit_author.setText('')
        self.lineEdit_journal.setText('')
        self.lineEdit_year.setText('')

    def search(self):
        self.parent.query_string_title = self.lineEdit_title.text()
        self.parent.query_string_abstract = self.lineEdit_abstract.text()
        self.parent.query_string_author = self.lineEdit_author.text()
        self.parent.query_string_journal = self.lineEdit_journal.text()
        self.parent.query_string_year = self.lineEdit_year.text()

        self.parent.query_opt_title = self.comboBox_title.currentText()
        self.parent.query_opt_abstract = self.comboBox_abstract.currentText()
        self.parent.query_opt_author = self.comboBox_author.currentText()
        self.parent.query_opt_journal = self.comboBox_journal.currentText()
        self.parent.query_opt_year = self.comboBox_year.currentText()

        self.parent.database.paper_info.drop_indexes()

        paper_ids = self.parent.query_info()
        text_box = []

        #self.textEdit_query_info.setText('\n'.join(self.parent.query_info()))
        for each in paper_ids:
            text_box.append(each)
            #extract paper info
            text_box.append('##paper_info##')
            target = self.parent.database.paper_info.find_one({'paper_id':each})
            keys = ['full_authors','journal','year','title','url','doi','abstract']
            for each_key in keys:
                text_box.append('{}:  {}'.format('  '+each_key,target[each_key]))
            text_box.append('\n')
        self.textEdit_query_info.setText('\n'.join(text_box))