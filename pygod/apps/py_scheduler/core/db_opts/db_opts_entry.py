from ..util import error_pop_up
from ...widgets.dialogues import NewProject
from .db_opts_book import load_db_book
from .db_opts_task import load_db_task
from .db_opts_finance import load_db_fin
from .db_opts_ppt import load_db_ppt
from .db_opts_personal import load_db_pe
from .db_opts_ppt import load_db_ppt
from .db_opts_bulletin import load_db_bulletin

def extract_project_info(self):
    all = self.database.project_info.find()
    self.plainTextEdit_project_info.setPlainText('\n'.join([each['project_info'] for each in all]))

def load_project(self):
    self.database = self.mongo_client[self.comboBox_project_list.currentText()]
    extract_project_info(self)
    if 'db_type' in self.database.project_info.find_one():
        self.database_type = self.database.project_info.find_one()['db_type']
    else:
        self.database_type = "图书"
    maps_load_db = {'图书': load_db_book,
                    '人事': load_db_pe,
                    '服事': load_db_task,
                    '财务': load_db_fin,
                    'PPT': load_db_ppt,
                    '月报': load_db_bulletin,
                    }
    assert self.database_type in maps_load_db, self.database_type+' is not in the maps!'
    maps_load_db[self.database_type](self)

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