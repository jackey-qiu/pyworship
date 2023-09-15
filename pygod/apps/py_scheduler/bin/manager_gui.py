import sys, json
from PyQt5 import uic, QtCore
from pyqtgraph.Qt import QtGui
from pathlib import Path
from functools import partial
import click
import qpageview.viewactions
from PyQt5.QtWidgets import QMainWindow,QApplication, QLabel
sys.path.append(str(Path(__file__).parent.parent.parent))
from ..core import db_operations_test as db
from ..core import graph_operations as graph

class MyMainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MyMainWindow, self).__init__(parent)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(str(Path(__file__).parent.parent / 'resources'/'icons'/'ccglogo.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.setIconSize(QtCore.QSize(24, 24))
        self.img_in_base64_format = b''
        self.img_format = 'png'
        self.setget_funcs_setup()

    def init_gui(self, ui):
        self.ui = ui
        uic.loadUi(ui, self)
        #setup image viewer actions
        self.comboBox_rsp_scripture.clear()
        self.comboBox_rsp_scripture.addItems(self.get_rsp_scripture_titles())
        self.action = qpageview.viewactions.ViewActions(self)
        self.action.setView(self.widget_img_view)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&View')
        fileMenu.addAction(self.action.fit_both)
        fileMenu.addAction(self.action.fit_height)
        fileMenu.addAction(self.action.fit_width)
        fileMenu.addAction(self.action.zoom_in)
        fileMenu.addAction(self.action.zoom_out)
        fileMenu.addAction(self.action.next_page)
        fileMenu.addAction(self.action.previous_page)
        db.set_db_config(self)
        self.statusbar = self.statusBar()
        self.statusLabel = QLabel(f"Welcome to ccg lib management system!")
        self.statusbar.addPermanentWidget(self.statusLabel)
        self.widget_terminal.update_name_space('main_gui',self)
        self.actionDatabaseCloud.triggered.connect(lambda:db.start_mongo_client_cloud(self))
        self.actionLogout.triggered.connect(lambda:db.logout(self))
        self.actionRegistration.triggered.connect(lambda:db.register_new_user(self))
        self.pushButton_load.clicked.connect(lambda:db.load_project(self))
        self.pushButton_new_project.clicked.connect(lambda:db.new_project_dialog(self))
        self.pushButton_update_project_info.clicked.connect(lambda:db.update_project_info(self))
        self.pushButton_lend.clicked.connect(lambda:db.lend_dialog(self))
        self.pushButton_return.clicked.connect(lambda:db.return_dialog(self))
        self.pushButton_new.clicked.connect(lambda:db.add_paper_info(self))
        self.pushButton_update.clicked.connect(lambda:db.update_paper_info(self))
        self.pushButton_reserve.clicked.connect(lambda:db.reserve(self))
        self.pushButton_remove.clicked.connect(lambda:db.delete_one_paper(self))
        self.pushButton_search.clicked.connect(lambda:db.query_paper_info_for_paper_id(self,self.comboBox_search_field.currentText(),self.lineEdit_search_item.text()))
        self.comboBox_books.activated.connect(lambda:db.extract_paper_info(self))
        self.comboBox_month.activated.connect(lambda:db.init_pandas_model_from_db(self))
        self.pushButton_add_task_record.clicked.connect(lambda:db.add_task_info(self))
        #image
        self.pushButton_load_img.clicked.connect(lambda:db.load_img_from_file(self))
        self.pushButton_push_db_personal.clicked.connect(lambda: db.add_personal_info(self))
        self.pushButton_delete_one_record_personal.clicked.connect(lambda: db.delete_one_person(self))
        self.pushButton_clear.clicked.connect(lambda:db.clear_all_input(self, 'formLayout'))
        #finance
        self.pushButton_add_finance_info.clicked.connect(lambda:db.add_finance_info(self))
        self.pushButton_cal_sum.clicked.connect(lambda:db.calculate_sum(self))
        self.pushButton_finance_info.clicked.connect(lambda:db.delete_finance_info(self))
        #plot
        self.pushButton_plot.clicked.connect(lambda:graph.create_piechart(self))
        self.pushButton_plot.clicked.connect(lambda:graph.plot_finance_details(self))
        #ppt worker
        self.pushButton_make_ppt.clicked.connect(lambda:db.save_ppt_content_in_txt_format(self))
        self.pushButton_delete_ppt_record.clicked.connect(lambda:db.delete_ppt_record(self))
        self.pushButton_load_db_info.clicked.connect(lambda:db.extract_ppt_record(self))
        self.pushButton_save_ppt_info_to_db.clicked.connect(lambda:db.add_one_ppt_record(self))
        self.pushButton_update_song1.clicked.connect(lambda:db.add_one_song(self, which = '1'))
        self.pushButton_update_song2.clicked.connect(lambda:db.add_one_song(self, which = '2'))
        self.pushButton_update_song3.clicked.connect(lambda:db.add_one_song(self, which = '3'))
        self.pushButton_update_song4.clicked.connect(lambda:db.add_one_song(self, which = '4'))
        self.pushButton_extract_worker_info.clicked.connect(lambda:db.extract_workers(self))
        self.pushButton_insert_song1.clicked.connect(lambda:db.extract_one_song(self, self.comboBox_song1.currentText(),1))
        self.pushButton_insert_song2.clicked.connect(lambda:db.extract_one_song(self, self.comboBox_song2.currentText(),2))
        self.pushButton_insert_song3.clicked.connect(lambda:db.extract_one_song(self, self.comboBox_song3.currentText(),3))
        self.pushButton_insert_song4.clicked.connect(lambda:db.extract_one_song(self, self.comboBox_song4.currentText(),4))
        self.comboBox_rsp_scripture.currentIndexChanged.connect(lambda: self.textEdit_rsp_scripture.setPlainText(self.get_rsp_scripture_with_title()))
        self.pushButton_append_rsp_scripture.clicked.connect(self.update_or_append_scripture)

    def get_rsp_scripture_titles(self):
        json_file = Path(__file__).parent.parent.parent / 'ppt_worker' / 'src' / 'bible' / 'scriptures.json'
        with open(json_file, 'r', encoding='utf-8') as f:
            def _key(x):
                if x.startswith('0'):
                    return int(x[1])
                elif x[0] in map(str, range(1,10)):
                    return int(x[:2])
                else:
                    return 0
            return sorted(list(json.load(f).keys()), key=_key)

    def get_rsp_scripture_with_title(self):
        json_file = Path(__file__).parent.parent.parent / 'ppt_worker' / 'src' / 'bible' / 'scriptures.json'
        title = self.comboBox_rsp_scripture.currentText()
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)[title]

    def update_or_append_scripture(self):
        json_file = Path(__file__).parent.parent.parent / 'ppt_worker' / 'src' / 'bible' / 'scriptures.json'
        title = self.comboBox_rsp_scripture.currentText()
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data[self.lineEdit_rsp_scripture.text()] = self.textEdit_rsp_scripture.toPlainText()
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        self.comboBox_rsp_scripture.clear()
        self.comboBox_rsp_scripture.addItems(self.get_rsp_scripture_titles())

    def setget_funcs_setup(self):
        self.set_data_for_widget_img_view = partial(db.set_data_for_widget_img_view,self)
        self.get_data_for_widget_img_view = partial(db.get_data_for_widget_img_view,self)
        self.set_data_for_x_song_script_note = partial(db.set_data_for_x_song_script_note, self)
        self.get_data_for_x_song_script_note = partial(db.get_data_for_x_song_script_note, self)
        self.set_data_for_x_song_items_note = partial(db.set_data_for_x_song_items_note, self)
        self.get_data_for_x_song_items_note = partial(db.get_data_for_x_song_items_note, self)

@click.command()
@click.option('--ui', default='library_manager.ui',help="main gui ui file generated from Qt Desinger, possible ui files are :")
@click.option('--ss', default ='Takezo.qss', help='style sheet file *.qss, possible qss files include: ')
@click.option('--tm', default = 'True', help='show terminal widget (--tm True) or not (--tm False)')
def scheduler(ui, ss, tm):
    ui_file = str(Path(__file__).parent.parent/ "ui" / ui)
    QApplication.setStyle("fusion")
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.init_gui(ui_file)
    if tm=='False':
        myWin.widget_terminal.hide()
        myWin.label_3.hide()
    elif tm=='True':
        pass
    myWin.setWindowTitle('汉堡华人基督教会数据库管理系统')
    style_sheet_path = str(Path(__file__).parent.parent/ "resources" / "stylesheets" / ss)
    File = open(style_sheet_path,'r')
    with File:
        qss = File.read()
        app.setStyleSheet(qss)    
    myWin.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    scheduler()
    