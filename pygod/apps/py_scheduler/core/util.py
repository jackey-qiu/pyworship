import os
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QMenu, QLineEdit, QTextEdit, QFileDialog
from PyQt5.QtCore import Qt, QAbstractListModel
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtCore import Qt, QAbstractListModel,QUrl
import base64
import bcrypt
import calendar, datetime
import numpy as np
from pypinyin import pinyin, Style
import yt_dlp as youtube_dl
from pathlib import Path

def clear_all_text_field(self, tabWidget = 'tabWidget_note'):
    for each in getattr(self, tabWidget).findChildren(QLineEdit):
        each.setText('')
    for each in getattr(self, tabWidget).findChildren(QTextEdit):
        each.setPlainText('')

def disable_all_tabs_but_one(self, tab_name = 'tabWidget_2', enabled_tab_ix = 0):
    for i in range(len(getattr(self, tab_name))):
        getattr(self, tab_name).setTabEnabled(i, False)
    getattr(self, tab_name).setTabEnabled(enabled_tab_ix, True)

def decode_nth_week(input):
    nb = input[1]
    return ['一','二','三','四','五'].index(nb)

def get_date_from_nth_week(which_week, month, decode = decode_nth_week, year = None):
    which_week = decode(which_week) # 0 basis
    if year==None:
        year = datetime.date.today().year
    first_week_day, month_range = calendar.monthrange(year, month) 
    date_of_first_sunday = 7-first_week_day
    date_of_specified_sunday = date_of_first_sunday + 7 * which_week
    if date_of_specified_sunday > month_range:
        raise IndexError('The specified sunday index is too high for this month.')
    else:
        return date_of_specified_sunday

def get_dates_for_one_month(month, year = None):
    dates = []
    which_weeks = [0,1,2,3,4]
    if year==None:
        year = datetime.date.today().year
    first_week_day, month_range = calendar.monthrange(year, month) 
    date_of_first_sunday = 7-first_week_day
    for which_week in which_weeks:
        date_of_specified_sunday = date_of_first_sunday + 7 * which_week
        if date_of_specified_sunday > month_range:
            pass
        else:
            dates.append(f'{month}月{date_of_specified_sunday}日')
    return dates

def encrypt_password(password, encode = 'utf-8'):
    password = password.encode(encode)
    salt = bcrypt.gensalt(10)
    return bcrypt.hashpw(password, salt)

def confirm_password(password,encrypted_password, encode = 'utf-8'):
    return bcrypt.checkpw(str(password).encode(encode), encrypted_password)

def error_pop_up(msg_text = 'error', window_title = ['Error','Information','Warning'][0]):
    msg = QMessageBox()
    if window_title == 'Error':
        msg.setIcon(QMessageBox.Critical)
    elif window_title == 'Warning':
        msg.setIcon(QMessageBox.Warning)
    else:
        msg.setIcon(QMessageBox.Information)

    msg.setText(msg_text)
    # msg.setInformativeText('More information')
    msg.setWindowTitle(window_title)
    msg.exec_()

def map_chinese_to_eng_key(str_ch):
    map_ = {'书名':'book_name',
            '作者':'author',
            '编号':'paper_id',
            '状态':'status',
            '类别':'class',
            }
    if str_ch in map_:
        return map_[str_ch]
    else:
        return 'UNKNOWN'

def image_to_64base_string(image_path):
    with open(image_path, "rb") as img_file:
         my_string = base64.b64encode(img_file.read())
    return my_string

def image_string_to_qimage(my_string, img_format = 'PNG'):
    QByteArr = QtCore.QByteArray.fromBase64(my_string)
    QImage = QtGui.QImage()
    QImage.loadFromData(QByteArr, img_format)
    return QImage

class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """
    #{'select':'选择','paper_id':'编号','year':'年份','press':'出版社','archive_date':'入库时间','book_name':'书名','class':'类别','status':'状态','note':'备注'}
    def __init__(self, data, tableviewer, main_gui, parent=None, column_names = {}):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.column_name_map = column_names
        self._data = data
        self.tableviewer = tableviewer
        self.main_gui = main_gui

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role):
        cols = self._data.shape[1]
        checked_columns = [i for i in range(cols) if type(self._data.iloc[0, i])==np.bool_]
        if index.isValid():
            if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
                return str(self._data.iloc[index.row(), index.column()])
            #if role == QtCore.Qt.BackgroundRole and index.row()%2 == 0:
                # return QtGui.QColor('green')
                # return QtGui.QColor('DeepSkyBlue')
                #return QtGui.QColor('Blue')
            # if role == QtCore.Qt.BackgroundRole and index.row()%2 == 1:
            if role == QtCore.Qt.BackgroundRole:
                if index.column() in checked_columns:
                    return QtGui.QColor('yellow')
                else:
                    return QtGui.QColor('white')
                # return QtGui.QColor('aqua')
                # return QtGui.QColor('lightGreen')
            # if role == QtCore.Qt.ForegroundRole and index.row()%2 == 1:
            if role == QtCore.Qt.ForegroundRole:
                if index.column() in checked_columns:
                    if self._data.iloc[index.row(), index.column()]:
                        return QtGui.QColor('green')
                    else:
                        return QtGui.QColor('red')
                else:
                    return QtGui.QColor('black')
            
            if role == QtCore.Qt.CheckStateRole and index.column() in checked_columns:
                if self._data.iloc[index.row(),index.column()]:
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked
        return None

    def setData(self, index, value, role):
        cols = self._data.shape[1]
        checked_columns = [i for i in range(cols) if type(self._data.iloc[0, i])==np.bool_]        
        if not index.isValid():
            return False
        if role == QtCore.Qt.CheckStateRole and index.column() in checked_columns:
            if value == QtCore.Qt.Checked:
                self._data.iloc[index.row(),index.column()] = True
            else:
                self._data.iloc[index.row(),index.column()] = False
        else:
            if str(value)!='':
                self._data.iloc[index.row(),index.column()] = str(value)
        # if self._data.columns.tolist()[index.column()] in ['select','archive_date','user_label','read_level']:
            # self.update_meta_info_paper(paper_id = self._data['paper_id'][index.row()])
        self.dataChanged.emit(index, index)
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()
        # self.tableviewer.resizeColumnsToContents() 
        # self.tableviewer.horizontalHeader().setStretchLastSection(True)
        return True
    
    def update_view(self):
        self.tableviewer.resizeColumnsToContents() 
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

    def headerData(self, rowcol, orientation, role):
        map_chinese_words = self.column_name_map
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            tag = self._data.columns[rowcol]         
            if tag in map_chinese_words:
                return map_chinese_words[tag]
            else:
                return tag
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self._data.index[rowcol]         
        return None

    def flags(self, index):
        cols = self._data.shape[1]
        checked_columns = [i for i in range(cols) if type(self._data.iloc[0, i])==np.bool_]        
        if not index.isValid():
           return QtCore.Qt.NoItemFlags
        else:
            if index.column() in checked_columns:
                return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable)
            else:
                return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            """
            if index.column()==0:
                return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable)
            else:
                return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            """
    def sort(self, Ncol, order):
        """Sort table by given column number."""
        def _to_pinyin(s):
            return ''.join([each[:-1] for each_list in pinyin(s, style = Style.TONE3) for each in each_list])
        self._data['sort_me'] = self._data[self._data.columns.tolist()[Ncol]].apply(_to_pinyin)
        self.layoutAboutToBeChanged.emit()
        self._data = self._data.sort_values('sort_me',
                                        ascending=order == QtCore.Qt.AscendingOrder, ignore_index = True)
        # self._data = self._data.sort_values(self._data.columns.tolist()[Ncol],
                                        # ascending=order == QtCore.Qt.AscendingOrder, ignore_index = True, key=_to_pinyin)
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()
        self._data.drop(columns='sort_me', inplace=True)

class MyLogger(object):
    def __init__(self, statusbar):
        self.statusbar = statusbar

    def debug(self, msg):
        print(msg)
        if msg.startswith('[download]'):
            self.statusbar.showMessage(msg)

    def warning(self, msg):
        print(msg)
        if msg.startswith('[download]'):
            self.statusbar.showMessage(msg)

    def error(self, msg):
        print(msg)
        if msg.startswith('[download]'):
            self.statusbar.showMessage(msg)

class DownloadYoutube(QtCore.QObject):
    def __init__(self, statusbar, parent):
        super(DownloadYoutube, self).__init__()
        self.url = ''
        self.path = ''
        self.download_mp4 = False
        self.statusbar = statusbar
        self._parent = parent

    def my_hook(self, d):
        if d['status'] == 'finished':
            #file_tuple = os.path.split(os.path.abspath(d['filename']))
            self.statusbar.showMessage("Done downloading {}".format(os.path.abspath(d['filename'].replace('.webm','.mp3'))))
        if d['status'] == 'downloading':
            self.statusbar.showMessage(d['filename']+d['_percent_str']+d['_eta_str'])

    def prepare_download(self, url, file_name, download_mp4 = False):
        content_folder = Path.home() / 'pygodAppData' / 'songs'
        content_folder.mkdir(parents=True, exist_ok=True)
        self.url = url
        self.path = content_folder
        self.file_name = file_name
        self.download_mp4 = download_mp4

    def download(self):
        ydl_opts_mp3 = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'postprocessor_args': [
                '-ar', '16000'
            ],
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'outtmpl':str(self.path / f'{self.file_name}.%(ext)s'),
            'logger': MyLogger(self.statusbar),
            'progress_hooks':[self.my_hook]
            }

        ydl_opts_video = {'outtmpl':os.path.join(self.path, '/%(title)s.%(ext)s'),'format':'best'}

        if self.download_mp4:
            ydl_opts = ydl_opts_video
        else:
            ydl_opts = ydl_opts_mp3
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

class PlaylistModel(QAbstractListModel):
    def __init__(self, playlist, *args, **kwargs):
        super(PlaylistModel, self).__init__(*args, **kwargs)
        self.playlist = playlist

    def data(self, index, role):
        if role == Qt.DisplayRole:
            media = self.playlist.media(index.row())
            return media.canonicalUrl().fileName()

    def rowCount(self, index):
        return self.playlist.mediaCount()
    
def hhmmss(ms):
    # s = 1000
    # m = 60000
    # h = 360000
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, _ = divmod(r, 1000)
    return ("%d:%02d:%02d" % (h,m,s)) if h else ("%d:%02d" % (m,s))

class player_api:

    @staticmethod
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    @staticmethod
    def dropEvent(self, e):
        for url in e.mimeData().urls():
            self.playlist.addMedia(
                QMediaContent(url)
            )

        self.model.layoutChanged.emit()

        # If not playing, seeking to first of newly added + play.
        if self.player.state() != QMediaPlayer.PlayingState:
            i = self.playlist.mediaCount() - len(e.mimeData().urls())
            self.playlist.setCurrentIndex(i)
            self.player.play()

    @staticmethod
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", str(Path.home() / 'pygodAppData' / 'songs'), "mp3 Audio (*.mp3);;mp4 Video (*.mp4);;Movie files (*.mov)")
        if path:
            self.playlist.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(path)
                )
            )

        self.model.layoutChanged.emit()

    @staticmethod
    def empty_files(self):
        self.playlist.clear()

    @staticmethod
    def update_duration(self, duration):
        # print("!", duration)
        # print("?", self.player.duration())
        
        self.timeSlider.setMaximum(duration)

        if duration >= 0:
            self.totalTimeLabel.setText(hhmmss(duration))

    @staticmethod
    def update_position(self, position):
        if position >= 0:
            self.currentTimeLabel.setText(hhmmss(position))

        # Disable the events to prevent updating triggering a setPosition event (can cause stuttering).
        self.timeSlider.blockSignals(True)
        self.timeSlider.setValue(position)
        self.timeSlider.blockSignals(False)

    @staticmethod
    def playlist_selection_changed(self, ix):
        # We receive a QItemSelection from selectionChanged.
        i = ix.indexes()[0].row()
        self.playlist.setCurrentIndex(i)

    @staticmethod
    def playlist_position_changed(self, i):
        if i > -1:
            ix = self.model.index(i)
            self.playlistView.setCurrentIndex(ix)

    @staticmethod
    def erroralert(self, *args):
        print(args)
