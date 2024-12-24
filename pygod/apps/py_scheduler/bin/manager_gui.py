import sys, json
from PyQt5 import QtGui, uic, QtCore
from PyQt5.QtWidgets import QMessageBox, QDialog
from pyqtgraph.Qt import QtGui
from pathlib import Path
from functools import partial
import click
import qpageview.viewactions
from PyQt5.QtWidgets import QMainWindow,QApplication, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
sys.path.append(str(Path(__file__).parent.parent.parent))
from ..core.db_opts import db_opts_entry as db_prj
from ..core.db_opts import db_opts_bulletin as db_bulletin
from ..core.db_opts import db_opts_book as db_book
from ..core.db_opts import db_opts_finance as db_fin
from ..core.db_opts import db_opts_personal as db_pe
from ..core.db_opts import db_opts_ppt as db_ppt
from ..core.db_opts import db_opts_task as db_task
from ..core.db_opts import init_db_opts as db_reg
from ..core.db_opts import db_opts_hymn as db_hymn
from ..core import graph_operations as graph
from ...py_scheduler.core.util import DownloadYoutube, PlaylistModel, player_api, process_lyrics_dynamic_optimized

db_api_map = {'图书': db_book,
              '人事': db_pe,
              '服事': db_task,
              '财务': db_fin,
              'PPT': db_ppt,
              '月报': db_bulletin,
              '诗歌': db_hymn }

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
        self.index_names = {}
        self.ui = ui
        uic.loadUi(ui, self)
        self.activated_task_input_widget = self.lineEdit_1st_week_note
        self.db_opts = db_prj
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
        self.statusbar = self.statusBar()
        self.statusLabel = QLabel(f"Welcome to ccg lib management system!")
        self.statusbar.addPermanentWidget(self.statusLabel)
        self.widget_terminal.update_name_space('main_gui',self)
        #reg
        db_reg.set_db_config(self)
        self.actionDatabaseCloud.triggered.connect(lambda:db_reg.start_mongo_client_cloud(self))
        self.actionLogout.triggered.connect(lambda:db_reg.logout(self))
        self.actionRegistration.triggered.connect(lambda:db_reg.register_new_user(self))
        #project
        self.pushButton_load.clicked.connect(lambda:db_prj.load_project(self))
        self.pushButton_new_project.clicked.connect(lambda:db_prj.new_project_dialog(self))
        self.pushButton_update_project_info.clicked.connect(lambda:db_prj.update_project_info(self))
        #book
        self.pushButton_lend.clicked.connect(lambda:db_book.lend_dialog(self))
        self.pushButton_return.clicked.connect(lambda:db_book.return_dialog(self))
        self.pushButton_new.clicked.connect(lambda:db_book.add_paper_info(self))
        self.pushButton_update.clicked.connect(lambda:db_book.update_paper_info(self))
        self.pushButton_reserve.clicked.connect(lambda:db_book.reserve(self))
        self.pushButton_remove.clicked.connect(lambda:db_book.delete_one_paper(self))
        self.pushButton_search.clicked.connect(lambda:db_book.query_paper_info_for_paper_id(self,self.comboBox_search_field.currentText(),self.lineEdit_search_item.text()))
        self.comboBox_books.activated.connect(lambda:db_book.extract_paper_info(self))
        # task
        self.comboBox_month.activated.connect(lambda:db_task.init_pandas_model_from_db(self))
        self.lineEdit_year_task.returnPressed.connect(lambda:db_task.init_pandas_model_from_db(self))
        self.comboBox_group.activated.connect(lambda:db_task.update_worker_names_info(self))
        self.pushButton_add_task_record.clicked.connect(lambda:db_task.add_task_info(self))
        self.lineEdit_1st_week_note.mousePressEvent = lambda x:self.set_activated_input_widget(self.lineEdit_1st_week_note)
        self.lineEdit_2nd_week_note.mousePressEvent = lambda x:self.set_activated_input_widget(self.lineEdit_2nd_week_note)
        self.lineEdit_3rd_week_note.mousePressEvent = lambda x:self.set_activated_input_widget(self.lineEdit_3rd_week_note)
        self.lineEdit_4th_week_note.mousePressEvent = lambda x:self.set_activated_input_widget(self.lineEdit_4th_week_note)
        self.lineEdit_5th_week_note.mousePressEvent = lambda x:self.set_activated_input_widget(self.lineEdit_5th_week_note)
        for which in ['1st', '2nd', '3rd', '4th', '5th']:
            getattr(self, f'pushButton_rm_{which}_week').clicked.connect(lambda state, which=which: getattr(self, f'lineEdit_{which}_week_note').setText(''))
            getattr(self, f'pushButton_format_{which}_week').clicked.connect(lambda state, which=which:self.format_input_text(f'lineEdit_{which}_week_note'))
        #image
        self.pushButton_load_img.clicked.connect(lambda:db_pe.load_img_from_file(self))
        self.pushButton_push_db_personal.clicked.connect(lambda: db_pe.add_personal_info(self))
        self.pushButton_delete_one_record_personal.clicked.connect(lambda: db_pe.delete_one_person(self))
        self.pushButton_clear.clicked.connect(lambda:db_pe.clear_all_input(self, 'formLayout'))
        #finance
        self.pushButton_add_finance_info.clicked.connect(lambda:db_fin.add_finance_info(self))
        self.pushButton_cal_sum.clicked.connect(lambda:db_fin.calculate_sum(self))
        self.pushButton_finance_info.clicked.connect(lambda:db_fin.delete_finance_info(self))
        #plot
        self.pushButton_plot.clicked.connect(lambda:graph.create_piechart(self))
        self.pushButton_plot.clicked.connect(lambda:graph.plot_finance_details(self))
        #ppt worker
        self.pushButton_make_ppt.clicked.connect(lambda:db_ppt.save_ppt_content_in_txt_format(self))
        self.pushButton_delete_ppt_record.clicked.connect(lambda:db_ppt.delete_ppt_record(self))
        self.pushButton_load_db_info.clicked.connect(lambda:db_ppt.extract_ppt_record(self))
        self.pushButton_save_ppt_info_to_db.clicked.connect(lambda:db_ppt.add_one_ppt_record(self))
        self.pushButton_extract_worker_info.clicked.connect(lambda:db_ppt.extract_workers(self))
        self.comboBox_song1.currentIndexChanged.connect(lambda:db_ppt.extract_one_song(self, self.comboBox_song1.currentText(),1))
        self.comboBox_song2.currentIndexChanged.connect(lambda:db_ppt.extract_one_song(self, self.comboBox_song2.currentText(),2))
        self.comboBox_song3.currentIndexChanged.connect(lambda:db_ppt.extract_one_song(self, self.comboBox_song3.currentText(),3))
        self.comboBox_song4.currentIndexChanged.connect(lambda:db_ppt.extract_one_song(self, self.comboBox_song4.currentText(),4))
        self.lineEdit_song1.returnPressed.connect(lambda:db_ppt.extract_targeted_songs_from_cache(self, self.lineEdit_song1.text(), self.comboBox_song1))
        self.lineEdit_song2.returnPressed.connect(lambda:db_ppt.extract_targeted_songs_from_cache(self, self.lineEdit_song2.text(), self.comboBox_song2))
        self.lineEdit_song3.returnPressed.connect(lambda:db_ppt.extract_targeted_songs_from_cache(self, self.lineEdit_song3.text(), self.comboBox_song3))
        self.lineEdit_song4.returnPressed.connect(lambda:db_ppt.extract_targeted_songs_from_cache(self, self.lineEdit_song4.text(), self.comboBox_song4))
        self.comboBox_rsp_scripture.currentIndexChanged.connect(lambda: self.textEdit_rsp_scripture.setPlainText(self.get_rsp_scripture_with_title()))
        self.pushButton_append_rsp_scripture.clicked.connect(self.update_or_append_scripture)
        #bulletin worker
        self.pushButton_load_db_info_bulletin.clicked.connect(lambda:db_bulletin.extract_bulletin_record(self))
        self.pushButton_save_bulletin_info.clicked.connect(lambda:db_bulletin.add_one_bulletin_record(self))
        self.pushButton_delete_bulletin_record.clicked.connect(lambda:db_bulletin.delete_bulletin_record(self))
        self.pushButton_make_bulletin.clicked.connect(lambda:db_bulletin.save_bulletin_content_in_txt_format_and_make_bulletin(self))
        #song manager
        self.pushButton_clear_field.clicked.connect(lambda:db_hymn.clear_all_text_field(self))
        self.pushButton_update_hymn.clicked.connect(lambda:db_hymn.add_one_record_in_db(self))
        self.pushButton_add_hymn.clicked.connect(lambda:db_hymn.add_one_record_in_db(self))
        self.pushButton_delete_hymn.clicked.connect(lambda:db_hymn.delete_one_record_in_db(self))
        self.pushButton_download_from_youtube.clicked.connect(lambda:db_hymn.download_file(self))
        self.pushButton_print.clicked.connect(self.print_lyrics)
        self.pushButton_make_script.clicked.connect(lambda: process_lyrics_dynamic_optimized(self.textEdit_script_ppt_note.toPlainText(), self.textEdit_script_text_note))
        #setup youtube downloader
        self.download = DownloadYoutube(self.statusbar, self)
        self.thread_download = QtCore.QThread()
        self.download.moveToThread(self.thread_download)
        self.thread_download.started.connect(self.download.download)
        #setup mp3 player
        ####qmediaplayer settings from this line on####
        self.player = QMediaPlayer()
        self.player.error.connect(partial(player_api.erroralert, self))
        self.player.play()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)
        # self.player.setVideoOutput(self.videowidget)
        self.playButton.pressed.connect(self.player.play)
        self.pauseButton.pressed.connect(self.player.pause)
        self.stopButton.pressed.connect(self.player.stop)
        self.volumeSlider.valueChanged.connect(self.player.setVolume)
        self.previousButton.pressed.connect(self.playlist.previous)
        self.nextButton.pressed.connect(self.playlist.next)

        self.model = PlaylistModel(self.playlist)
        self.playlistView.setModel(self.model)
        self.playlist.currentIndexChanged.connect(partial(player_api.playlist_position_changed,self))
        selection_model = self.playlistView.selectionModel()
        selection_model.selectionChanged.connect(partial(player_api.playlist_selection_changed,self))

        self.player.durationChanged.connect(partial(player_api.update_duration, self))
        self.player.positionChanged.connect(partial(player_api.update_position, self))
        self.timeSlider.valueChanged.connect(self.player.setPosition)

        self.pushButton_load_file.clicked.connect(partial(player_api.open_file, self))
        self.pushButton_empty.clicked.connect(partial(player_api.empty_files, self))
        self.dragEnterEvent = partial(player_api.dragEnterEvent, self)
        self.dropEvent = partial(player_api.dropEvent, self)
        self.setAcceptDrops(True)
        #search func
        self.pushButton_search_target.clicked.connect(self.search_field)

    def search_field(self):
        if hasattr(self, 'pandas_model'):
            db_api = db_api_map[self.database_type]
            if self.database_type == '服事':
                return
            if len(self.pandas_model._data)!=0:
                #reload db
                db_prj.load_project(self, resize = False)
                collection_name = list(self.db_config_info['db_types'][self.database_type]['table_viewer'].keys())[0]
                name_map = list(self.db_config_info['db_types'][self.database_type]['table_viewer'].values())[0]
                name_map = dict([(value, key) for key, value in name_map.items()])
                field_name = name_map[self.comboBox_search_item.currentText()]
                field_value = self.lineEdit_search_item_value.text()
                pandas_data = self.pandas_model._data[self.pandas_model._data[field_name].str.contains(field_value, case=False)]
                if hasattr(db_api,'rerender_tableview'):
                    db_api.rerender_tableview(self, pandas_data.reset_index(drop=True))

    def format_input_text(self, lineEditWidget_name):
        lineEditWidget = getattr(self, lineEditWidget_name)
        if lineEditWidget.text().startswith('+'):
            lineEditWidget.setText(lineEditWidget.text()[1:])

    def set_activated_input_widget(self, widget):
        self.activated_task_input_widget = widget

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
        self.set_data_for_widget_img_view = partial(db_pe.set_data_for_widget_img_view,self)
        self.get_data_for_widget_img_view = partial(db_pe.get_data_for_widget_img_view,self)
        self.set_data_for_x_song_script_note = partial(db_ppt.set_data_for_x_song_script_note, self)
        self.get_data_for_x_song_script_note = partial(db_ppt.get_data_for_x_song_script_note, self)
        self.set_data_for_x_song_items_note = partial(db_ppt.set_data_for_x_song_items_note, self)
        self.get_data_for_x_song_items_note = partial(db_ppt.get_data_for_x_song_items_note, self)
        self.set_data_for_x_role_note = partial(db_task.set_data_for_x_role_note, self)
        self.get_data_for_x_role_note = partial(db_task.get_data_for_x_role_note, self)
        self.set_data_for_x_worker_name_note = partial(db_task.set_data_for_x_worker_name_note, self)
        self.get_data_for_x_worker_name_note = partial(db_task.get_data_for_x_worker_name_note, self)
        self.get_data_for_x_check_status = partial(db_hymn.get_data_for_x_check_status, self)
        self.set_data_for_x_check_status = partial(db_hymn.set_data_for_x_check_status, self)
        self.get_data_for_x_correct_status = partial(db_hymn.get_data_for_x_correct_status, self)
        self.set_data_for_x_correct_status = partial(db_hymn.set_data_for_x_correct_status, self)

    def print_lyrics(self):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_()==QDialog.Accepted:
            self.textEdit_script_text_note.print(printer)

    def closeEvent(self, event) -> None:
        quit_msg = "Are you sure you want to exit the program? If yes, all text indexes will be deleted!"
        reply = QMessageBox.question(self, 'Message', 
                        quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if not hasattr(self,'mongo_client'):
                event.accept()
            print('remove all database index.....')
            for each in self.index_names:
                db_nm, coll, *k = each
                self.mongo_client[db_nm][coll].drop_index(self.index_names[each])
                print(self.index_names[each], 'deleted!')
            print('all done!')
            event.accept()
        else:
            event.ignore()

@click.command()
@click.option('--ui', default='library_manager.ui',help="main gui ui file generated from Qt Desinger, possible ui files are :")
@click.option('--ss', default ='Takezo.qss', help='style sheet file *.qss, possible qss files include: ')
@click.option('--tm', default = 'False', help='show terminal widget (--tm True) or not (--tm False)')
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
    