#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os,json, qdarkstyle, sys
import click
from pathlib import Path
msg_path = Path(__file__).parent.parent / 'src' / 'notes'
desertscripture_path = msg_path / 'desertscripture.json'
ui_path = msg_path.parent / 'ui' / 'bible_reader.ui'
sys.path.append('C:\\Users\\qiucanro\\apps\\pyworkship')
#The following three lines are necessary as a detoure to the incompatibiltiy of Qt5 APP showing in Big Sur OS
#This solution seems non-sense, since the matplotlib is not used in the app.
#But if these lines are removed, the app GUI is not gonna pop up.
#This situation may change in the future.
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
import pandas as pd
from jieba.analyse import ChineseAnalyzer
from whoosh.index import create_in
from whoosh.qparser import QueryParser
from whoosh.fields import Schema
from whoosh import fields
from whoosh.index import open_dir
import urllib
from urllib.parse import quote
import string
from lxml import etree
import datetime
from email.mime.text import MIMEText
import sys,os
from pyqtgraph.Qt import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QGraphicsScene, QPlainTextEdit, QMessageBox, QLineEdit
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from PyQt5.QtCore import QDate, Qt, QAbstractListModel,QUrl
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from PyQt5 import QtCore
from pygod.apps.bible_reader.core.client.util import *
from random import randint
from pygod.apps.bible_reader.core.client.langconv import *
convert = Converter('zh-hans').convert
#import youtube_dl
import yt_dlp as youtube_dl
from pygod.apps.bible_reader.core.client.bible_book import *
analyzer = ChineseAnalyzer()
# print(msg_path)

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

def hhmmss(ms):
    # s = 1000
    # m = 60000
    # h = 360000
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, _ = divmod(r, 1000)
    return ("%d:%02d:%02d" % (h,m,s)) if h else ("%d:%02d" % (m,s))

class DownloadYoutube(QtCore.QObject):
    def __init__(self):
        super(DownloadYoutube, self).__init__()
        self.url = ''
        self.path = ''
        self.download_mp4 = False

    def prepare_download(self, url, path, download_mp4):
        self.url = url
        self.path = path
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
            'outtmpl':self.path + '/%(title)s.%(ext)s'
            }

        ydl_opts_video = {'outtmpl':self.path + '/%(title)s.%(ext)s','format':'best'}

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

class MyMainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MyMainWindow, self).__init__(parent)
        #pg.mkQApp()
        self.document_folder = ''
        self.download = DownloadYoutube()
        self.thread_download = QtCore.QThread()
        self.download.moveToThread(self.thread_download)
        self.thread_download.started.connect(self.download.download)
        uic.loadUi(ui_path,self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(str(msg_path.parent/'icons'/'bible.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.setIconSize(QtCore.QSize(24, 24))
        self.load_reading_plan()
        self.plainTextEdit.setStyleSheet(
                        """QPlainTextEdit {background-color: #FFFFFF;
                           color: #3300CC;}""")
        self.plainTextEdit_desert.setStyleSheet(
                        """QPlainTextEdit {
                           color: gold;}""")

        self.plainTextEdit_scripture_explain.setStyleSheet(
                        """QPlainTextEdit {background-color: #FFFFFF;
                           color: #6600CC;}""")
        self.setWindowTitle('Bible Reader')
        self.html_overview_ds = 'error'
        with open(desertscripture_path,'r') as f:
            self.desert_scripture = json.load(f)

        self.html_scripture = "https://dailyverses.net/tc/"
        self.get_golden_scripture()

        self.bible_chinese_json = ''
        with open(os.path.join(msg_path.parent / 'bibles_json','chinese_bible.json'),'r') as f:
            self.bible_chinese_json = json.load(f)

        self.bible_english_json = ''
        self.update_bible_version()

        self.bible_today_tag = ""
        self.today_date = None
        self.spring_desert_date = None
        self.total_chapter = 1189
        self.old_testimony = 929
        self.reading_plan = ['4-2-2','2'][0]
        self.speed = 2
        self.first_day_in_plan = None 
        self.comboBox_book.clear()
        self.comboBox_book.addItems(bible_books)
        # self.update_reading_plan()
        self.update_count_down_time()
        try:
            self.get_spring_desert_article()
        except:
            pass
        self.check_read_or_not()
        self.get_scripture_for_today_local_disk()
        #signal-slot-pair connection
        self.calendarWidget.selectionChanged.connect(self.get_spring_desert_article)
        self.pushButton_today.clicked.connect(self.update_count_down_time_today)
        self.pushButton_save_plan.clicked.connect(self.update_reading_plan)
        self.pushButton_today.clicked.connect(self.get_scripture_for_today_local_disk)
        self.pushButton_specified.clicked.connect(self.get_scripture_specified)
        self.pushButton_load.clicked.connect(self.load_all_notes_json)
        self.pushButton_save.clicked.connect(self.save_notes_json_overwrite)
        self.pushButton_append.clicked.connect(self.save_notes_json_append)
        self.pushButton_before.clicked.connect(self.update_count_down_time)
        self.pushButton_before.clicked.connect(self.get_scripture_for_today_local_disk)
        self.pushButton_check.clicked.connect(self.update_check_read)
        self.pushButton_change.clicked.connect(self.get_golden_scripture)
        self.pushButton_save_current.clicked.connect(self.save_scripture)
        self.pushButton_load_saved.clicked.connect(self.load_all_scriptures)
        self.pushButton_search.clicked.connect(self.search_bible)
        self.spinBox_start_date.valueChanged.connect(self.update_count_down_time)
        self.spinBox_start_month.valueChanged.connect(self.update_count_down_time)
        self.spinBox_start_year.valueChanged.connect(self.update_count_down_time)
        self.comboBox_book.currentIndexChanged.connect(self.set_bible_book)
        self.comboBox_book_chapter.currentIndexChanged.connect(self.set_book_chapter)
        self.comboBox_bible_version.currentIndexChanged.connect(self.update_bible_version)
        self.pushButton_show_notes.clicked.connect(self.show_note_panel)
        self.pushButton_show_scripture.clicked.connect(self.show_scripture_panel)
        self.pushButton_load_json.clicked.connect(self.load_json)
        self.pushButton_save_json_as.clicked.connect(self.save_json_as)
        self.pushButton_save_json.clicked.connect(self.save_json)
        self.pushButton_new.clicked.connect(self.new_json)
        self.pushButton_load_folder.clicked.connect(self.load_doc_files)
        self.listWidget_docs.itemDoubleClicked.connect(self.open_selected_doc_in_listWidget)
        self.pushButton_next_chapter.clicked.connect(self.go_to_next_chapter)
        self.pushButton_last_chapter.clicked.connect(self.go_to_last_chapter)
        self.pushButton_clear_all.clicked.connect(self.clear_all_items_in_listWidget)
        self.pushButton_new_chapter.clicked.connect(self.add_new_chapter_in_the_selected_book)
        ####qmediaplayer settings from this line on####
        self.player = QMediaPlayer()
        self.player.error.connect(self.erroralert)
        self.player.play()
        # Setup the playlist.
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)
        self.player.setVideoOutput(self.videowidget)
        # Connect control buttons/slides for media player.
        self.playButton.pressed.connect(self.player.play)
        self.pauseButton.pressed.connect(self.player.pause)
        self.stopButton.pressed.connect(self.player.stop)
        self.volumeSlider.valueChanged.connect(self.player.setVolume)
        self.previousButton.pressed.connect(self.playlist.previous)
        self.nextButton.pressed.connect(self.playlist.next)

        self.model = PlaylistModel(self.playlist)
        self.playlistView.setModel(self.model)
        self.playlist.currentIndexChanged.connect(self.playlist_position_changed)
        selection_model = self.playlistView.selectionModel()
        selection_model.selectionChanged.connect(self.playlist_selection_changed)

        self.player.durationChanged.connect(self.update_duration)
        self.player.positionChanged.connect(self.update_position)
        self.timeSlider.valueChanged.connect(self.player.setPosition)

        self.pushButton_load_file.clicked.connect(self.open_file)
        self.pushButton_remove.clicked.connect(self.empty_files)
        self.pushButton_download.clicked.connect(self.download_file)
        self.setAcceptDrops(True)

        #update terminal widget
        self.widget_terminal.update_name_space('main_win',self)

        #update folder path for songs downloaded from YouTube
        self.lineEdit_save_path.setText(os.path.join(msg_path,))

    def clear_all_items_in_listWidget(self):
        self.listWidget_docs.clear()
        self.lineEdit_book_title.clear()
        self.comboBox_book_chapter.clear()
        self.plainTextEdit_scripture_explain.clear()

    def add_new_chapter_in_the_selected_book(self):
        self.plainTextEdit_scripture_explain.setPlainText("这里开始编辑新章节内容，编辑完毕请点击保存按键！")
        self.lineEdit_new_chapter.setText('请输入新章节名称')

    def open_selected_doc_in_listWidget(self):
        fileName = os.path.join(self.document_folder,self.listWidget_docs.currentItem().text())
        if fileName:
            self.scripture_explain_file_name = fileName
            with open(fileName,'r') as f:
                self.scripture_explain = json.load(f)
            self.lineEdit_book_title.setText(fileName)
            self.comboBox_book_chapter.clear()
            self.comboBox_book_chapter.addItems(sorted(list(self.scripture_explain.keys()))) 

    def load_doc_files(self):
        '''
        load all json files(*.json) located in a selected folder
        '''
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.document_folder = folder
        self.listWidget_docs.clear()
        if folder=='':
            return
        for file in os.listdir(folder):
            if file.endswith('.json'):
                self.listWidget_docs.addItem(file)

    def download_file(self):
        url = self.lineEdit_url.text()
        path = self.lineEdit_save_path.text()
        download_mp4 = self.checkBox_video.isChecked()
        self.download.prepare_download(url, path, download_mp4)
        if not Path(path).exists():
            error_pop_up(f'{path} does not exists!','Error')
            return
        else:
            try:
                self.thread_download.terminate()
            except:
                pass
            try:
                #self._download(url, path, download_mp4)
                #self.download.download()
                self.thread_download.start()
            except:
                
                #self._download(url, path, download_mp4)
                error_pop_up(f'Fail to download {url}!','Error')

    def _download(self, url, path, download_mp4 = False):
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
            'outtmpl':path + '/%(title)s.%(ext)s'
            }

        ydl_opts_video = {'outtmpl':path + '/%(title)s.%(ext)s','format':'best'}

        if download_mp4:
            ydl_opts = ydl_opts_video
        else:
            ydl_opts = ydl_opts_mp3
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

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

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "mp3 Audio (*.mp3);mp4 Video (*.mp4);Movie files (*.mov);All files (*.*)")

        if path:
            self.playlist.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(path)
                )
            )

        self.model.layoutChanged.emit()

    def empty_files(self):
        self.playlist.clear()

    def update_duration(self, duration):
        # print("!", duration)
        # print("?", self.player.duration())
        
        self.timeSlider.setMaximum(duration)

        if duration >= 0:
            self.totalTimeLabel.setText(hhmmss(duration))

    def update_position(self, position):
        if position >= 0:
            self.currentTimeLabel.setText(hhmmss(position))

        # Disable the events to prevent updating triggering a setPosition event (can cause stuttering).
        self.timeSlider.blockSignals(True)
        self.timeSlider.setValue(position)
        self.timeSlider.blockSignals(False)

    def playlist_selection_changed(self, ix):
        # We receive a QItemSelection from selectionChanged.
        i = ix.indexes()[0].row()
        self.playlist.setCurrentIndex(i)

    def playlist_position_changed(self, i):
        if i > -1:
            ix = self.model.index(i)
            self.playlistView.setCurrentIndex(ix)

    def toggle_viewer(self, state):
        if state:
            self.viewer.show()
        else:
            self.viewer.hide()

    def erroralert(self, *args):
        print(args)

    def new_json(self):
        text, okPressed = QInputDialog.getText(self, "Get text","File name:", QLineEdit.Normal, "newfile.json")
        if okPressed and text != '':
            if self.document_folder=='':
                self.document_folder = msg_path 
            fileName = os.path.join(self.document_folder,text)
            self.lineEdit_book_title.setText(fileName)
            self.comboBox_book_chapter.clear()
            self.comboBox_book_chapter.addItems(['init'])
            with open(fileName,'w') as f:
                #self.lineEdit_new_chapter.setText('init')
                self.plainTextEdit_scripture_explain.setPlainText('')
                json.dump({convert('init'):convert(self.plainTextEdit_scripture_explain.toPlainText())},f)
            with open(fileName,'r') as f:
                self.scripture_explain = json.load(f)
            self.listWidget_docs.clear()
            self.listWidget_docs.addItem(text)
            self.statusbar.showMessage('New json file is created!')

    def load_json(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Data Files (*.json)", options=options)
        if fileName:
            self.scripture_explain_file_name = fileName
            if self.document_folder=='':
                self.document_folder = os.path.dirname(fileName)
                self.listWidget_docs.clear()
                self.listWidget_docs.addItem(os.path.basename(fileName))
            with open(fileName,'r') as f:
                self.scripture_explain = json.load(f)
            self.lineEdit_book_title.setText(fileName)
            self.comboBox_book_chapter.clear()
            self.comboBox_book_chapter.addItems(sorted(list(self.scripture_explain.keys())))

    def save_json_as(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "Save file as", "", "json file (*.json);;all files (*.*)")
        fileName = convert(fileName)
        if fileName:
            with open(fileName,'w') as f:
                keys = list(self.scripture_explain.keys())
                json_content = {}
                if self.lineEdit_new_chapter.text()!='':
                    json_content.update({convert(self.lineEdit_new_chapter.text()):convert(self.plainTextEdit_scripture_explain.toPlainText())})
                for each in keys:
                    if each == self.comboBox_book_chapter.currentText():
                        if self.lineEdit_new_chapter.text()=='':
                            #json.dump({convert(os.path.basename(fileName)):convert(self.plainTextEdit_scripture_explain.toPlainText())},f)
                            json_content.update({convert(each):convert(self.plainTextEdit_scripture_explain.toPlainText())})
                        else:
                            json_content.update({convert(each):convert(self.scripture_explain[each])})
                    else:
                        json_content.update({convert(each):convert(self.scripture_explain[each])})
                json.dump(json_content,f)
            with open(fileName,'r') as f:
                self.scripture_explain = json.load(f)
            self.lineEdit_book_title.setText(fileName)
            self.comboBox_book_chapter.clear()
            self.comboBox_book_chapter.addItems(sorted(list(self.scripture_explain.keys())))
            self.statusbar.clearMessage()
            self.statusbar.showMessage("新的json文件保存成功！")

    def save_json(self):
        fileName = convert(self.lineEdit_book_title.text())
        if fileName:
            with open(fileName,'w') as f:
                keys = list(self.scripture_explain.keys())
                json_content = {}
                if self.lineEdit_new_chapter.text()!='':
                    json_content.update({convert(self.lineEdit_new_chapter.text()):convert(self.plainTextEdit_scripture_explain.toPlainText())})
                for each in keys:
                    if each == self.comboBox_book_chapter.currentText():
                        if self.lineEdit_new_chapter.text()=='':
                            #json.dump({convert(os.path.basename(fileName)):convert(self.plainTextEdit_scripture_explain.toPlainText())},f)
                            json_content.update({convert(each):convert(self.plainTextEdit_scripture_explain.toPlainText())})
                        else:
                            json_content.update({convert(each):convert(self.scripture_explain[each])})
                    else:
                        json_content.update({convert(each):convert(self.scripture_explain[each])})
                json.dump(json_content,f)
            with open(fileName,'r') as f:
                self.scripture_explain = json.load(f)
            self.lineEdit_book_title.setText(fileName)
            self.comboBox_book_chapter.clear()
            self.comboBox_book_chapter.addItems(sorted(list(self.scripture_explain.keys())))
            self.lineEdit_new_chapter.setText('')
            self.statusbar.clearMessage()
            self.statusbar.showMessage("json文件保存成功！")

    def set_book_chapter(self):
        current_text = self.comboBox_book_chapter.currentText()
        if current_text!='':
            self.plainTextEdit_scripture_explain.setPlainText(self.scripture_explain[current_text])

    def go_to_next_chapter(self):
        current_index = self.comboBox_book_chapter.currentIndex()
        total_items = self.comboBox_book_chapter.count()
        if current_index==(total_items-1):
            pass
        else:
            self.comboBox_book_chapter.setCurrentIndex(current_index+1)
            self.set_book_chapter()

    def go_to_last_chapter(self):
        current_index = self.comboBox_book_chapter.currentIndex()
        if current_index==0:
            pass
        else:
            self.comboBox_book_chapter.setCurrentIndex(current_index-1)
            self.set_book_chapter()

    def show_note_panel(self):
        if self.pushButton_show_notes.text()=='显示笔记':
            self.pushButton_show_notes.setText('隐藏笔记')
            self.widget_notes.show()
        else:
            self.pushButton_show_notes.setText('显示笔记')
            self.widget_notes.hide()

    def show_scripture_panel(self):
        if self.pushButton_show_scripture.text()=='显示经文':
            self.pushButton_show_scripture.setText('隐藏经文')
            self.tabWidget.setVisible(True)
        else:
            self.pushButton_show_scripture.setText('显示经文')
            self.tabWidget.setVisible(False)

    def update_bible_version(self):
        bible_version = self.comboBox_bible_version.currentText()
        with open(os.path.join(msg_path.parent / 'bibles_json','english_bible_{}.json'.format(bible_version)),'r') as f:
            self.bible_english_json = json.load(f)

    def get_golden_scripture(self):
        from datetime import datetime, timedelta
        begin = datetime.strptime('2021-1-1','%Y-%m-%d')
        span = timedelta(days = randint(0,364))
        now = begin + span
        url_scripture = "https://dailyverses.net/tc/{}/{}/{}".format(now.year, now.month, now.day)
        sock = urllib.request.urlopen(url_scripture)
        self.html_scripture = etree.HTML(sock.read())
        sock.close()
        try:
            self.scripture_list = [self.html_scripture.xpath("//div/span[@class='v1']/text()")[0] + '\n' + self.html_scripture.xpath("//div/a[@class='vc']/text()")[0]]
            self.scripture_img_link = "https://dailyverses.net" + self.html_scripture.xpath('//a/img/@src')[0]
            # print(self.scripture_img_link)
        except:
            return
        f = open(os.path.join(msg_path,'scripture_photo.jpg'),'wb')           
        f.write(urllib.request.urlopen(self.scripture_img_link).read())
        f.close()
        self.label_scripture.setPixmap(QPixmap(os.path.join(msg_path,'scripture_photo.jpg')))
        self.label_scripture.setScaledContents(True)
        s1 = self.scripture_list[0]
        self.textBrowser_scripture.clear()
        cursor = self.textBrowser_scripture.textCursor()
        cursor.insertHtml('''<p><span style="color: red;">{} <br></span>'''.format(" "))
        self.textBrowser_scripture.setText(''.join(['\n',s1])) 

    def search_bible(self):
        if self.lineEdit_key_words.text()=='':
            return
        chinese = '\u4e00'<=self.lineEdit_key_words.text()[0]<='\u9fa5' 
        if chinese:
            self.search_bible_chinese()
        else:
            self.search_bible_english()

    def search_bible_chinese(self):
        phrase = self.lineEdit_key_words.text()
        hit_book, hit_verse, hit_chapter = [],[],[]
        if phrase == '':
            return
        bible_content = self.bible_chinese_json
        if not os.path.exists("index"):
            reply = QMessageBox.information(self,"建立字段搜索序列","初次使用搜索功能，需要建立搜索index查询库，大概需要1分钟左右，请耐心等候。下次使用，这步会跳过！")
            schema = Schema(book_name=fields.TEXT(stored=True,analyzer=analyzer), chapter=fields.TEXT(stored=True), verse = fields.TEXT(stored=True),content=fields.TEXT(analyzer=analyzer))
            os.mkdir("index")
            ix = create_in("index", schema)
            writer = ix.writer()
            for book in bible_content:
                for chapter in bible_content[book]:
                    for verse in bible_content[book][chapter]:
                        writer.add_document(book_name=book, chapter=chapter, verse = verse,
                            content=bible_content[book][chapter][verse])
            writer.commit()
        else:
            ix = open_dir('index')
            ix.writer().commit()
        with ix.searcher() as searcher:
            query = QueryParser("content", ix.schema).parse(phrase)
            results = searcher.search(query,limit = None)
            for each in results:
                hit_book.append(each['book_name'])
                hit_chapter.append(each['chapter'])
                hit_verse.append(each['verse'])
            results_pd = pd.DataFrame({'book':hit_book,'chapter':hit_chapter,'verse':hit_verse})
            results_pd = results_pd.sort_values(['book','chapter','verse'])
            hit_book, hit_chapter, hit_verse = list(results_pd['book']),list(results_pd['chapter']),list(results_pd['verse'])
            search_results = []
            for i in range(len(hit_book)):
                search_results.append('{}.[{}]({}:{}):{}\n'.format(i+1,hit_book[i],hit_chapter[i],hit_verse[i],\
                                       self.bible_chinese_json[hit_book[i]][hit_chapter[i]][hit_verse[i]]))

            self.textBrowser_search_results.clear()
            cursor = self.textBrowser_search_results.textCursor()
            cursor.insertHtml('''<p><span style="color: #ffc100;">{} <br></span>'''.format(" "))
            self.textBrowser_search_results.setText(''.join(search_results)) 

    def search_bible_english(self):
        phrase = self.lineEdit_key_words.text()
        bible_version = self.comboBox_bible_version.currentText()
        hit_book, hit_verse, hit_chapter = [],[],[]
        #bible_english_json = self.bible_english_json
        if phrase == '':
            return
        #bible_content = self.bibe_english_json
        if not os.path.exists(os.path.join(msg_path,"index_{}".format(bible_version))):
            reply = QMessageBox.information(self,"建立字段搜索序列","初次使用搜索功能，需要建立搜索index查询库，大概需要1分钟左右，请耐心等候。下次使用，这步会跳过！")
            schema = Schema(book_name=fields.TEXT(stored=True), chapter=fields.TEXT(stored=True), verse = fields.TEXT(stored=True),content=fields.TEXT)
            os.mkdir(os.path.join(msg_path,"index_{}".format(bible_version)))
            ix = create_in(os.path.join(msg_path,"index_{}".format(bible_version)), schema)
            writer = ix.writer()
            for book in self.bible_english_json:
                for chapter in self.bible_english_json[book]:
                    for verse in self.bible_english_json[book][chapter]:
                        writer.add_document(book_name=book, chapter=chapter, verse = verse,
                            content=self.bible_english_json[book][chapter][verse])
            writer.commit()
        else:
            ix = open_dir(os.path.join(msg_path,"index_{}".format(bible_version)))
            ix.writer().commit()
        with ix.searcher() as searcher:
            query = QueryParser("content", ix.schema).parse(phrase)
            results = searcher.search(query,limit = None)
            for each in results:
                hit_book.append(each['book_name'])
                hit_chapter.append(each['chapter'])
                hit_verse.append(each['verse'])
            results_pd = pd.DataFrame({'book':hit_book,'chapter':hit_chapter,'verse':hit_verse})
            results_pd = results_pd.sort_values(['book','chapter','verse'])
            hit_book, hit_chapter, hit_verse = list(results_pd['book']),list(results_pd['chapter']),list(results_pd['verse'])
            search_results = []
            for i in range(len(hit_book)):
                search_results.append('{}.[{}]({}:{}):{}\n\n'.format(i+1,hit_book[i],hit_chapter[i],hit_verse[i],\
                                       self.bible_english_json[hit_book[i]][hit_chapter[i]][hit_verse[i]]))
            self.textBrowser_search_results.clear()
            cursor = self.textBrowser_search_results.textCursor()
            cursor.insertHtml('''<p><span style="color: #ffc100;">{} <br></span>'''.format(" "))
            self.textBrowser_search_results.setText(''.join(search_results)) 

    def check_read_or_not(self):
        today = datetime.date.today()
        y,m,d = today.year, today.month, today.day
        with open(os.path.join(msg_path,'read_or_not.txt'),'r') as f:
            date = f.readlines()[0]
            if date.rstrip()=='{}.{}.{}'.format(d,m,y):
                self.pushButton_check.setText('今日已读')
            else:
                self.pushButton_check.setText('今日打卡')

    def update_check_read(self):
        today = datetime.date.today()
        y,m,d = today.year, today.month, today.day
        with open(os.path.join(msg_path,'read_or_not.txt'),'w') as f:
            f.write('{}.{}.{}'.format(d,m,y))
            self.pushButton_check.setText('今日已读')


    def load_extra_chapter_number(self):
        with open(os.path.join(msg_path,'extra_chapter_number.txt'),'r') as f:
            old, new = list(map(int,f.readlines()[0].rstrip().rsplit()))
            self.spinBox_more_old.setValue(old)
            self.spinBox_more_new.setValue(new)
    
    def update_extra_chapter_number(self):
        with open(os.path.join(msg_path,'extra_chapter_number.txt'),'w') as f:
            text_to_write = '{}  {}'.format(self.spinBox_more_old.value(),self.spinBox_more_new.value())
            f.write(text_to_write)

    def load_reading_plan(self):
        with open(os.path.join(msg_path,'current_read_plan.txt'),'r') as f:
            lines = f.readlines()
            for each in lines:
                items = each.rstrip().rsplit()
                if items[0] == 'read_order':
                   self.checkBox_order.setChecked(eval(items[1])) 
                elif items[0] == 'offset':
                    self.spinBox_more_old.setValue(eval(items[1]))
                    self.spinBox_more_new.setValue(eval(items[2]))
                elif items[0] == 'speed':
                    self.spinBox_old.setValue(eval(items[1]))
                    self.spinBox_new.setValue(eval(items[2]))
                elif items[0] == 'begin':
                    self.spinBox_start_year.setValue(eval(items[1]))
                    self.spinBox_start_month.setValue(eval(items[2]))
                    self.spinBox_start_date.setValue(eval(items[3]))

    def update_reading_plan(self):
        with open(os.path.join(msg_path,'current_read_plan.txt'),'w') as f:
            f.write('read_order {}\n'.format(self.checkBox_order.isChecked()))
            f.write('offset {}  {}\n'.format(self.spinBox_more_old.value(),self.spinBox_more_new.value()))
            f.write('speed {}  {}\n'.format(self.spinBox_old.value(),self.spinBox_new.value()))
            f.write('begin {}  {} {}\n'.format(self.spinBox_start_year.value(),self.spinBox_start_month.value(),self.spinBox_start_date.value()))
        self.statusbar.clearMessage()
        self.statusbar.showMessage("读经计划保存成功！")

    def get_scripture_specified_english(self):
        chapter_content = []
        book = self.lineEdit_book.text()
        if book not in bible_books:
            for each in bible_books:
                if sum([int(each_charater in each) for each_charater in book])==len(book):
                    book = each
                    break
        book = bible_book_english[bible_books.index(book)]
        #assert book in bible_books,'something is wrong about typed book name!'
        # book = 'Genesis'
        chapters_bounds = [int(self.lineEdit_book_chapter.text()),int(self.lineEdit_book_chapter2.text())]
        chapters = range(chapters_bounds[0],chapters_bounds[1]+1)
        for chapter in chapters:
            try:
                current_content = ['<{}>Chapter{}'.format(book,chapter)]+list(self.bible_english_json[book][str(chapter)].values())
            except:
                return chapter_content
            for i in range(len(current_content)):
                if i!=0:
                    chapter_content.append('{}{}'.format(i,current_content[i]))
                else:
                   chapter_content.append('{}'.format(current_content[i])) 
        return chapter_content

    def get_scripture_specified(self):
        chapter_content_eng = []
        chapter_content = []
        if self.radioButton_eng.isChecked() or self.radioButton_cn_eng.isChecked():
            chapter_content_eng = self.get_scripture_specified_english()
        if self.radioButton_cn_eng.isChecked() or self.radioButton_cn.isChecked():
            book = self.lineEdit_book.text()
            if book not in bible_books:
                for each in bible_books:
                    if sum([int(each_charater in each) for each_charater in book])==len(book):
                        book = each
                        break
            #assert book in bible_books,'something is wrong about typed book name!'
            # book = 'Genesis'
            chapters_bounds = [int(self.lineEdit_book_chapter.text()),int(self.lineEdit_book_chapter2.text())]
            chapters = range(chapters_bounds[0],chapters_bounds[1]+1)
            for chapter in chapters:
                url = quote("http://mobile.chinesebibleonline.com/book/{}/{}".format(book,chapter),safe=string.printable)
                sock_temp =urllib.request.urlopen(url)
                html_temp = etree.HTML(sock_temp.read())
                sock_temp.close()
                book_name = ["《{}》第{}章".format(book,chapter)]
                try:
                    scriptures = html_temp.xpath("/html/body/div[2]/div/span[2]/text()")
                    verse_number = html_temp.xpath("/html/body/div[2]/div/span[1]/text()")
                    combined = [verse_number[ii].rstrip()+scriptures[ii].rstrip() for ii in range(len(scriptures))]
                    chapter_content = chapter_content + book_name + combined
                except:
                    pass
        chapter_content_all = []
        if len(chapter_content_eng)==0 or len(chapter_content)==0:
            chapter_content_all = chapter_content_eng + chapter_content
            chapter_content_all = [each+'\n' for each in chapter_content_all]
        else:
            if len(chapter_content)>len(chapter_content_eng):
                chapter_content_eng = chapter_content_eng + (len(chapter_content)-len(chapter_content_eng))*['\n']
            elif len(chapter_content)<len(chapter_content_eng):
                chapter_content = chapter_content + (len(chapter_content_eng)-len(chapter_content))*['\n'] 
            else:
                pass
            chapter_content_all_ = list(zip(chapter_content,chapter_content_eng))
            for each_ in chapter_content_all_:
                chapter_content_all.append(each_[0])
                chapter_content_all.append(each_[1]+'\n')

        self.textBrowser_bible.clear()
        cursor = self.textBrowser_bible.textCursor()
        cursor.insertHtml('''<p><span style="color: #ffc100;">{} <br></span>'''.format(" "))
        self.textBrowser_bible.setText('\n'.join(chapter_content_all)) 
        

    def get_book_chapters(self,days_elapsed =2, speed = 2, offset = 0, plan_type = 'all', bible_books = bible_books):
        if plan_type == 'all':
            bible_books_ = bible_books
        elif plan_type == 'new':
            bible_books_ = bible_books[39:]
        elif plan_type == 'old':
            bible_books_ = bible_books[0:39]
        bible_chinese_json = self.bible_chinese_json
        hit_book, hit_chapter = [], []
        total_chapter_read = days_elapsed * speed + offset

        if plan_type in ['all','new','old']:
            chapters_accum = 0
            for each in bible_books_:
                current_book_chapters = len(bible_chinese_json[each])
                if chapters_accum+current_book_chapters<=total_chapter_read:
                    chapters_accum = chapters_accum + current_book_chapters
                else:
                    hit_book.append(each)
                    hit_chapter.append(total_chapter_read-chapters_accum+1)
                    break

            if plan_type=='old':
                if offset!=self.spinBox_more_old.value():
                    speed = speed + self.spinBox_new.value()
            chapters_accum = 0
            for each in bible_books_:
                current_book_chapters = len(bible_chinese_json[each])
                if chapters_accum+current_book_chapters<=(total_chapter_read+speed-1):
                    chapters_accum = chapters_accum + current_book_chapters
                else:
                    hit_book.append(each)
                    hit_chapter.append(total_chapter_read+speed-1-chapters_accum+1)
                    break
            if len(hit_book)==0:
                return [],[]
            elif len(hit_book)==1:
                # return hit_book,list(range(int(hit_chapter[0]),len(bible_chinese_json[hit_book[0]])+1))
                return hit_book,[str(hit_chapter[0])]
            else:
                if hit_book[0]==hit_book[1]:
                    hit_chapter=list(range(hit_chapter[0],hit_chapter[1]+1))
                    hit_book = [hit_book[0]]*speed
                else:
                    num_books_in_between = bible_books_.index(hit_book[1]) - bible_books_.index(hit_book[0])
                    books_in_between = bible_books_[(bible_books_.index(hit_book[0])+1):(bible_books_.index(hit_book[0])+num_books_in_between)]
                    books_in_between_all =[]
                    chapters_in_between_all = []
                    for each in books_in_between:
                        # books_in_between_all=books_in_between_all+[each]*len(bible_books[each])
                        books_in_between_all=books_in_between_all+[each]*len(bible_chinese_json[each])
                        chapters_in_between_all=chapters_in_between_all+list(range(1,len(bible_chinese_json[each])+1))
                    hit_book = [hit_book[0]]*(len(bible_chinese_json[hit_book[0]])-hit_chapter[0]+1)+books_in_between_all+[hit_book[1]]*hit_chapter[1]
                    hit_chapter = list(range(hit_chapter[0],len(bible_chinese_json[hit_book[0]])+1))+chapters_in_between_all+list(range(1,hit_chapter[1]+1))
                return hit_book,[str(each) for each in hit_chapter]

            
    def get_num_chapters_left(self, book, chapter,scope = 'all', bible_books = bible_books):
        num_chapters_left = 0
        if scope=='all':
            next_book_index = bible_books.index(book)+1
            for i in range(next_book_index,len(bible_books)):
                num_chapters_left = num_chapters_left + len(self.bible_chinese_json[bible_books[i]])
            num_chapters_left = num_chapters_left + len(self.bible_chinese_json[book]) - int(chapter)
            return num_chapters_left
        elif scope =='new':
            bible_books =bible_books[39:] 
            next_book_index = bible_books.index(book)+1
            for i in range(next_book_index,len(bible_books)):
                num_chapters_left = num_chapters_left + len(self.bible_chinese_json[bible_books[i]])
            num_chapters_left = num_chapters_left + len(self.bible_chinese_json[book]) - int(chapter)
            return num_chapters_left
        elif scope =='old':
            bible_books =bible_books[0:39] 
            next_book_index = bible_books.index(book)+1
            for i in range(next_book_index,len(bible_books)):
                num_chapters_left = num_chapters_left + len(self.bible_chinese_json[bible_books[i]])
            num_chapters_left = num_chapters_left + len(self.bible_chinese_json[book]) - int(chapter)
            return num_chapters_left

    def get_scripture_for_today_local_disk(self):
        self.textBrowser_bible.clear()
        cursor = self.textBrowser_bible.textCursor()
        cursor.insertHtml('''<p><span style="color: #ffc100;">{} <br></span>'''.format(" "))
        #setup for reading from beginning to end mode
        #are you in new testimony today?
        in_new_testimony = (self.days_elapsed*self.spinBox_old.value()+self.spinBox_more_old.value()-self.old_testimony)>=0
        speed_all = [self.spinBox_old.value(),self.spinBox_new.value()][int(in_new_testimony)]
        offset_all = [self.spinBox_more_old.value(),self.spinBox_more_new.value()][int(in_new_testimony)]
        hit_books,hit_chapters = self.get_book_chapters(days_elapsed =self.days_elapsed, speed = speed_all, offset = offset_all, plan_type = 'all')
        if len(hit_books)==0:
            num_days_left_all = 0
        else:
            num_days_left_all = int(self.get_num_chapters_left(hit_books[-1],hit_chapters[-1],'all')/speed_all)
        #setup for the other mode, ie reading chapters from old testimony and new testimony at the same time
        hit_books_new,hit_chapters_new = self.get_book_chapters(days_elapsed =self.days_elapsed, speed = self.spinBox_new.value(), offset = self.spinBox_more_new.value(), plan_type = 'new')
        hit_chapters_new = [str(each) for each in hit_chapters_new]
        if len(hit_books_new)==0:#if we finish reading the new testimony
            extra_offset = self.days_elapsed*self.spinBox_new.value()+self.spinBox_more_new.value() - (self.total_chapter-self.old_testimony)
            # print("extra offset",extra_offset)
            num_chapters_left_new = 0
            hit_books_old,hit_chapters_old = self.get_book_chapters(days_elapsed =self.days_elapsed, speed = self.spinBox_old.value(), offset = self.spinBox_more_old.value()+extra_offset, plan_type = 'old')
        else:
            num_chapters_left_new = self.get_num_chapters_left(hit_books_new[-1],hit_chapters_new[-1],'new')
            hit_books_old,hit_chapters_old = self.get_book_chapters(days_elapsed =self.days_elapsed, speed = self.spinBox_old.value(), offset = self.spinBox_more_old.value(), plan_type = 'old')
        if len(hit_books_old)==0:
            num_chapters_left_old = 0
        else:
            num_chapters_left_old = self.get_num_chapters_left(hit_books_old[-1],hit_chapters_old[-1],'old')
        # print(num_chapters_left_new,num_chapters_left_old)
        num_days_left_all_together = int((num_chapters_left_old+num_chapters_left_new)/(self.spinBox_old.value()+self.spinBox_new.value()))

        #update reading status now
        if self.checkBox_order.isChecked():
            self.lineEdit_count_down.setText(str(num_days_left_all))
            self.progressBar.setValue(int(100*(1-num_days_left_all/(self.days_elapsed+num_days_left_all))))
        else:
            self.lineEdit_count_down.setText(str(num_days_left_all_together))
            self.progressBar.setValue(int(100*(1-num_days_left_all_together/(self.days_elapsed+num_days_left_all_together))))

        old_testimony_content_cn = []
        new_testimony_content_cn = []
        old_testimony_content_eng = []
        new_testimony_content_eng = []
        all_content_cn, all_content_eng = [], []
        read_chapters_for_today = []
        if self.radioButton_cn.isChecked():
            if self.checkBox_order.isChecked():
                for i,each in enumerate(hit_books):
                    all_content_cn_ = self.bible_chinese_json[each][hit_chapters[i]]
                    all_content_cn.append('《{}》第{}章'.format(each,hit_chapters[i]))
                    read_chapters_for_today.append(all_content_cn[-1])
                    for each_verse, each_scripture in all_content_cn_.items():
                        all_content_cn.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                self.textBrowser_bible.setText('\n\n\n'.join(all_content_cn)) 
            else:
                for i,each in enumerate(hit_books_old):
                    old_testimony_content_cn_ = self.bible_chinese_json[each][hit_chapters_old[i]]
                    old_testimony_content_cn.append('《{}》第{}章'.format(each,hit_chapters_old[i]))
                    read_chapters_for_today.append(old_testimony_content_cn[-1])
                    for each_verse, each_scripture in old_testimony_content_cn_.items():
                        old_testimony_content_cn.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                for i,each in enumerate(hit_books_new):
                    new_testimony_content_cn_ = self.bible_chinese_json[each][hit_chapters_new[i]]
                    new_testimony_content_cn.append('《{}》第{}章'.format(each,hit_chapters_new[i]))
                    read_chapters_for_today.append(new_testimony_content_cn[-1])
                    for each_verse, each_scripture in new_testimony_content_cn_.items():
                        new_testimony_content_cn.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                self.textBrowser_bible.setText('\n\n\n'.join(old_testimony_content_cn+new_testimony_content_cn)) 
        elif self.radioButton_eng.isChecked():
            if self.checkBox_order.isChecked():
                hit_books = [bible_book_english[bible_books.index(each)] for each in hit_books]
                for i,each in enumerate(hit_books):
                    all_content_eng_ = self.bible_english_json[each][hit_chapters[i]]
                    all_content_eng.append('<{}>Chapter{}'.format(each,hit_chapters[i]))
                    read_chapters_for_today.append(all_content_eng[-1])
                    for each_verse, each_scripture in all_content_eng_.items():
                        all_content_eng.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                self.textBrowser_bible.setText('\n\n\n'.join(all_content_eng)) 
            else:
                hit_books_old = [bible_book_english[bible_books.index(each)] for each in hit_books_old]
                hit_books_new = [bible_book_english[bible_books.index(each)] for each in hit_books_new]
                for i,each in enumerate(hit_books_old):
                    old_testimony_content_eng.append('<{}> Chapter{}'.format(each,hit_chapters_old[i]))
                    read_chapters_for_today.append(old_testimony_content_eng[-1])
                    old_testimony_content_eng_ = self.bible_english_json[each][hit_chapters_old[i]]
                    for each_verse, each_scripture in old_testimony_content_eng_.items():
                        old_testimony_content_eng.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                for i,each in enumerate(hit_books_new):
                    new_testimony_content_eng.append('<{}> Chapter{}'.format(each,hit_chapters_new[i]))
                    read_chapters_for_today.append(new_testimony_content_eng[-1])
                    new_testimony_content_eng_ = self.english_bible_json[each][hit_chapters_new[i]]
                    for each_verse, each_scripture in new_testimony_content_eng_.items():
                        new_testimony_content_eng.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                self.textBrowser_bible.setText('\n\n\n'.join(old_testimony_content_eng+new_testimony_content_eng)) 
        elif self.radioButton_cn_eng.isChecked():
            if self.checkBox_order.isChecked():
                #chinese bible
                for i,each in enumerate(hit_books):
                    all_content_cn_ = self.bible_chinese_json[each][hit_chapters[i]]
                    all_content_cn.append('《{}》第{}章'.format(each,hit_chapters[i]))
                    read_chapters_for_today.append(all_content_cn[-1])
                    for each_verse, each_scripture in all_content_cn_.items():
                        all_content_cn.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                #english bible
                hit_books = [bible_book_english[bible_books.index(each)] for each in hit_books]
                for i,each in enumerate(hit_books):
                    all_content_eng_ = self.bible_english_json[each][hit_chapters[i]]
                    all_content_eng.append('<{}>Chapter{}'.format(each,hit_chapters[i]))
                    for each_verse, each_scripture in all_content_eng_.items():
                        all_content_eng.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                try:
                    zip_content = zip(all_content_cn,all_content_eng)
                    display_content = []
                    for each_item in zip_content:
                        display_content.append(each_item[0]+'\n')
                        display_content.append(each_item[1]+'\n\n')
                    self.textBrowser_bible.setText(''.join(display_content)) 
                except:
                    self.textBrowser_bible.setText('\n\n'.join(all_content_cn+all_content_eng)) 
            else:
                #chinese bible
                for i,each in enumerate(hit_books_old):
                    old_testimony_content_cn.append('《{}》第{}章'.format(each,hit_chapters_old[i]))
                    read_chapters_for_today.append(old_testimony_content_cn[-1])
                    old_testimony_content_cn_ = self.bible_chinese_json[each][hit_chapters_old[i]]
                    for each_verse, each_scripture in old_testimony_content_cn_.items():
                        old_testimony_content_cn.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                for i,each in enumerate(hit_books_new):
                    new_testimony_content_cn.append('《{}》第{}章'.format(each,hit_chapters_new[i]))
                    read_chapters_for_today.append(new_testimony_content_cn[-1])
                    new_testimony_content_cn_ = self.bible_chinese_json[each][hit_chapters_new[i]]
                    for each_verse, each_scripture in new_testimony_content_cn_.items():
                        new_testimony_content_cn.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                #english bible
                hit_books_old = [bible_book_english[bible_books.index(each)] for each in hit_books_old]
                hit_books_new = [bible_book_english[bible_books.index(each)] for each in hit_books_new]
                for i,each in enumerate(hit_books_old):
                    old_testimony_content_eng.append('<{}> Chapter{}'.format(each,hit_chapters_old[i]))
                    old_testimony_content_eng_ = self.bible_english_json[each][hit_chapters_old[i]]
                    for each_verse, each_scripture in old_testimony_content_eng_.items():
                        old_testimony_content_eng.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                for i,each in enumerate(hit_books_new):
                    new_testimony_content_eng.append('<{}> Chapter{}'.format(each,hit_chapters_new[i]))
                    new_testimony_content_eng_ = self.bible_english_json[each][hit_chapters_new[i]]
                    for each_verse, each_scripture in new_testimony_content_eng_.items():
                        new_testimony_content_eng.append('{}.{}'.format(each_verse,each_scripture.rstrip()))
                cn_content = old_testimony_content_cn+new_testimony_content_cn
                eng_content = old_testimony_content_eng+new_testimony_content_eng
                try:
                    zip_content = zip(cn_content,eng_content)
                    display_content = []
                    for each_item in zip_content:
                        display_content.append(each_item[0]+'\n')
                        display_content.append(each_item[1]+'\n\n')
                    self.textBrowser_bible.setText(''.join(display_content)) 
                except:
                    self.textBrowser_bible.setText('\n\n'.join(cn_content+eng_content)) 
        self.statusbar.clearMessage()
        self.statusbar.showMessage('+'.join(read_chapters_for_today))

    def get_scripture_for_today(self):
        books = []
        chapters = []
        method = self.reading_plan.rsplit("-")
        # print(method)
        self.speed = int(method[0])
        if len(method)==1:
            speed = int(method[0])
        elif len(method)==3:
            speed_old = int(method[1])
            speed_new = int(method[2])
        if 'speed' in locals().keys():
            chapter_content = self.craw_bible_chapters(scope='all',speed = speed)
        else:
            chapter_content_new = self.craw_bible_chapters(scope='new',speed = speed_new)
            if chapter_content_new == 'End':
                chapter_content_old = self.craw_bible_chapters(scope='old',speed = speed_old, more = speed_new)
            else:
                chapter_content_old = self.craw_bible_chapters(scope='old',speed = speed_old)
            if chapter_content_new=='End':
                chapter_content_new = ['\n']
            chapter_content = chapter_content_old + chapter_content_new

        self.textBrowser_bible.clear()
        # chapter_content = ['--------------------------------------------------------------------------------------------------------------------------------------------\n'] + chapter_content
        cursor = self.textBrowser_bible.textCursor()
        cursor.insertHtml('''<p><span style="color: blue;">{} <br></span>'''.format(" "))
        self.textBrowser_bible.setText('\n\n'.join(chapter_content)) 

    #get chapter by crawling from website, not used anymore
    def craw_bible_chapters(self,scope = 'all',speed=2, more = 0):
        offset = 0
        append_chapters = 0
        if scope=='all':
            num_nodes_book =  len(self.html_overview.xpath("/html/body/div[2]/ul/div")) 
            append_chapters = int(self.spinBox_more_old.value())+int(self.spinBox_more_new.value())
        elif scope=='new':
            num_nodes_book = 27
            offset = 40
            append_chapters = int(self.spinBox_more_new.value())
        elif scope=='old':
            num_nodes_book = 39
            append_chapters = int(self.spinBox_more_old.value())
        acc_chapters = 0
        node_index = []
        book_names = []
        start_chapter_index = []
        end_chapter_index = []
        target_chapters = speed*(int(self.total_chapter/self.speed)+[1,0][int((self.total_chapter%self.speed)==0)]-int(self.lineEdit_count_down.text())) + append_chapters
        if scope=='new':
            if target_chapters > (self.total_chapter - self.old_testimony):
                return 'End'
            else:
                pass
        # print('target_chapters',scope,target_chapters,speed,more)
        for i in range(num_nodes_book+1):
            current_book_length = len(self.html_overview.xpath("/html/body/div[2]/ul/div[{}]/ul/li".format(offset+i+1)))
            acc_chapters+= current_book_length
            if acc_chapters>target_chapters:
                node_index.append(i+1+offset)
                start_chapter_index.append(target_chapters - (acc_chapters - current_book_length) + 1)
                end_chapter_index_= start_chapter_index[-1] + speed + more
                if end_chapter_index_>current_book_length:
                    end_chapter_index.append(current_book_length+1)
                    if (end_chapter_index_ - current_book_length-1)<=len(self.html_overview.xpath("/html/body/div[2]/ul/div[{}]/ul/li".format(offset+i+1+1))):
                        end_chapter_index.append(end_chapter_index_ - current_book_length)
                        start_chapter_index.append(1)
                    else:
                        start_chapter_index.append(1)
                        start_chapter_index.append(1)
                        end_chapter_index.append(len(self.html_overview.xpath("/html/body/div[2]/ul/div[{}]/ul/li".format(offset+i+1+1))))
                        end_chapter_index.append(end_chapter_index_ - current_book_length - len(self.html_overview.xpath("/html/body/div[2]/ul/div[{}]/ul/li".format(offset+i+1+1))))
                    if len(self.html_overview.xpath("/html/body/div[2]/ul/div[{}]/ul/li".format(offset+i+2)))==0:
                        node_index.append(offset+i+3)
                    else:
                        node_index.append(offset+i+2)
                else:
                    end_chapter_index.append(end_chapter_index_)
                break
        # print(node_index,start_chapter_index,end_chapter_index) 
        chapter_content = []
        for i in range(len(node_index)):
            each_node_index = node_index[i]
            start, end = start_chapter_index[i], end_chapter_index[i]
            for j in range(start, end):
                try:
                    url_tail = self.html_overview.xpath("/html/body/div[2]/ul/div[{}]/ul/li[{}]/a/@href".format(each_node_index,j))[0]
                except:
                    url_tail = self.html_overview.xpath("/html/body/div[2]/ul/div[{}]/ul/li[{}]/a/@href".format(each_node_index+1,j))[0]
                print(url_tail)
                url = "http://mobile.chinesebibleonline.com{}".format(url_tail)
                sock_temp =urllib.request.urlopen(url)
                html_temp = etree.HTML(sock_temp.read())
                sock_temp.close()
                book_name = ["《{}》第{}章".format(html_temp.xpath("/html/body/div[2]/div[1]/text()")[0],j)]
                try:
                    scriptures = html_temp.xpath("/html/body/div[2]/div/span[2]/text()")
                    verse_number = html_temp.xpath("/html/body/div[2]/div/span[1]/text()")
                    combined = [verse_number[ii].rstrip()+scriptures[ii].rstrip() for ii in range(len(scriptures))]
                    chapter_content = chapter_content + book_name + combined
                except:
                    pass
        return chapter_content

    def get_spring_desert_article(self):
        selected_date = self.calendarWidget.selectedDate().toPyDate()
        y,m,d = selected_date.year, selected_date.month, selected_date.day
        first_data_of_year = datetime.date(y,1,1)
        which_day_of_today = (selected_date - first_data_of_year).days
        try:
            content = [self.desert_scripture['{}_cn'.format(which_day_of_today)],self.desert_scripture['{}_eng'.format(which_day_of_today)]]
            self.plainTextEdit_desert.clear()
            self.plainTextEdit_desert.setPlainText('\n'.join(content))
            self.pushButton_before.click()
        except:
            pass

    #not in use any more
    def update_reading_plan_old(self):
        plan = self.comboBox_plan.currentText()
        if plan == "一天四章（新旧各两章）":
            self.reading_plan = '4-2-2'
            self.speed = 4
        elif plan == "一天两章（顺序）":
            self.reading_plan = '2'
            self.speed = 2
        self.update_count_down_time()

    def update_count_down_time(self):
        start_month = int(self.spinBox_start_month.value())
        start_date = int(self.spinBox_start_date.value())
        start_year = int(self.spinBox_start_year.value())
        #start_year = int(datetime.date.today().year)
        start = datetime.date(start_year, start_month, start_date)
        date_before = self.calendarWidget.selectedDate().toPyDate()
        self.days_elapsed=(date_before-start).days
        self.load_specified_notes_json(date_before.year,date_before.month,date_before.day)

        # count_down =  int(self.total_chapter/self.speed)+[1,0][int((self.total_chapter%self.speed)==0)] - (datetime.date.today()-start).days

    def update_count_down_time_today(self):
        start_month = int(self.spinBox_start_month.value())
        start_date = int(self.spinBox_start_date.value())
        start_year = int(self.spinBox_start_year.value())
        # start_year = int(datetime.date.today().year)
        start = datetime.date(start_year, start_month, start_date)
        self.days_elapsed  = (datetime.date.today()-start).days
        self.calendarWidget.setSelectedDate(QDate(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
        self.load_specified_notes_json(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day)
        #count_down =  int(self.total_chapter/(int(self.spinBox_old.value())+int(self.spinBox_new.value()))) - (datetime.date.today()-start).days
        #self.lineEdit_count_down.setText(str(count_down))
        #total_days = self.total_chapter/(int(self.spinBox_old.value())+int(self.spinBox_new.value()))
        #self.progressBar.setValue(100*(1-count_down/total_days))

    def update_count_down_time_2(self):
        start_month = int(self.spinBox_start_month.value())
        start_date = int(self.spinBox_start_date.value())
        start_year = int(self.spinBox_start_year.value())
        # start_year = int(datetime.date.today().year)
        start = datetime.date(start_year, start_month, start_date)
        count_down =  int(self.total_chapter/self.speed)+[1,0][int((self.total_chapter%self.speed)==0)] - (self.calendarWidget.selectedDate().toPyDate()-start).days
        self.lineEdit_count_down.setText(str(count_down))
        total_days = self.total_chapter/self.speed
        self.progressBar.setValue(100*(1-count_down/total_days))

    def set_bible_book(self):
        self.lineEdit_book.setText(self.comboBox_book.currentText())

    def save_notes(self):
        notes_path = os.path.join(msg_path,'Bible_reader_notes.txt')
        # y,m,d = datetime.date.today().year, datetime.date.today().month, datetime.date.today().day
        date=self.calendarWidget.selectedDate().toPyDate()
        y,m,d = date.year, date.month, date.day
        if self.plainTextEdit.toPlainText()!='':
            if not os.path.exists(notes_path):
                with open(notes_path,'w') as f:
                    f.write("{}月{}月{}日\n".format(y,m,d))
                    f.write(self.plainTextEdit.toPlainText())
            else:
                with open(notes_path,'a+') as f:
                    f.write("\n\n{}月{}月{}日\n".format(y,m,d))
                    # f.write("{}-{}-{}\n".format(y,m,d))
                    f.write(self.plainTextEdit.toPlainText())
            
            self.statusbar.clearMessage()
            self.statusbar.showMessage("读经笔记保存成功！")
        else:
            pass

    def save_notes_json_overwrite(self):
        notes_path = os.path.join(msg_path,'Bible_reader_notes.json')
        # y,m,d = datetime.date.today().year, datetime.date.today().month, datetime.date.today().day
        date=self.calendarWidget.selectedDate().toPyDate()
        y,m,d = date.year, date.month, date.day
        notes_dict = {}
        if self.plainTextEdit.toPlainText()!='':
            if not os.path.exists(notes_path):
                notes_dict = {}
                with open(notes_path,'w') as f:
                    notes_dict["{}月{}月{}日".format(y,m,d)] = self.plainTextEdit.toPlainText()
                    json.dump(notes_dict,f)
            else:
                with open(notes_path,'r') as f:
                    notes_dict = json.load(f)
                key_today = "{}月{}月{}日".format(y,m,d)
                notes_dict[key_today] = self.plainTextEdit.toPlainText()
                with open(notes_path,'w') as f:
                    json.dump(notes_dict,f)
            self.statusbar.clearMessage()
            self.statusbar.showMessage("读经笔记覆盖保存成功！")
        else:
            pass

    def save_notes_json_append(self):
        notes_path = os.path.join(msg_path,'Bible_reader_notes.json')
        #y,m,d = datetime.date.today().year, datetime.date.today().month, datetime.date.today().day
        date=self.calendarWidget.selectedDate().toPyDate()
        y,m,d = date.year, date.month, date.day
        notes_dict = {}
        if self.plainTextEdit.toPlainText()!='':
            if not os.path.exists(notes_path):
                notes_dict = {}
                with open(notes_path,'w') as f:
                    notes_dict["{}月{}月{}日".format(y,m,d)] = self.plainTextEdit.toPlainText()
                    json.dump(notes_dict,f)
            else:
                with open(notes_path,'r') as f:
                    notes_dict = json.load(f)
                key_today = "{}月{}月{}日".format(y,m,d)
                if key_today in notes_dict:
                    notes_dict[key_today] = notes_dict[key_today]+'\n\n'+self.plainTextEdit.toPlainText()
                else:
                    notes_dict[key_today] = self.plainTextEdit.toPlainText()
                with open(notes_path,'w') as f:
                    json.dump(notes_dict,f)
            self.statusbar.clearMessage()
            self.statusbar.showMessage("读经笔记追加保存成功！")
        else:
            pass

    def load_all_notes_json(self):
        notes_path = os.path.join(msg_path,'Bible_reader_notes.json')
        # self.save_notes()
        if os.path.exists(notes_path):
            with open(notes_path,'r') as f:
                notes_all = json.load(f)
                content_together = []
                for each in notes_all:
                    content_together.append('{}\n{}\n\n\n'.format(each,notes_all[each]))
                self.plainTextEdit.setPlainText("".join(content_together))
        else:
            pass

    def load_specified_notes_json(self,y,m,d):
        notes_path = os.path.join(msg_path,'Bible_reader_notes.json')
        # self.save_notes()
        if os.path.exists(notes_path):
            with open(notes_path,'r') as f:
                notes_all = json.load(f)
                if "{}月{}月{}日".format(y,m,d) in notes_all:
                    content_together = [notes_all["{}月{}月{}日".format(y,m,d)]]
                    self.plainTextEdit.setPlainText("".join(content_together))
                else:
                    self.plainTextEdit.setPlainText("")
        else:
            pass

    def load_all_notes(self):
        notes_path = os.path.join(msg_path,'Bible_reader_notes.txt')
        # self.save_notes()
        if os.path.exists(notes_path):
            with open(notes_path,'r') as f:
                self.plainTextEdit.setPlainText("".join(f.readlines()))
        else:
            pass

    def save_scripture(self):
        notes_path = os.path.join(msg_path,'Bible_scriptures.txt')
        y,m,d = datetime.date.today().year, datetime.date.today().month, datetime.date.today().day
        if self.textBrowser_scripture.toPlainText()!='':
            if not os.path.exists(notes_path):
                with open(notes_path,'w') as f:
                    f.write("{}月{}月{}日\n".format(y,m,d))
                    f.write(self.textBrowser_scripture.toPlainText())
            else:
                with open(notes_path,'a+', encoding='utf-8') as f:
                    f.write("\n\n{}月{}月{}日\n".format(y,m,d))
                    # f.write("{}-{}-{}\n".format(y,m,d))
                    f.write(self.textBrowser_scripture.toPlainText())
            self.statusbar.clearMessage()
            self.statusbar.showMessage("今日金句保存成功！")
        else:
            pass

    def load_all_scriptures(self):
        notes_path = os.path.join(msg_path,'Bible_scriptures.txt')
        # self.save_notes()
        if os.path.exists(notes_path):
            with open(notes_path,'r') as f:
                self.textBrowser_scripture.setText("".join(f.readlines()))
        else:
            pass

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program? If yes, the notes will be overwritten!"
        reply = QMessageBox.question(self, 'Message', 
                        quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.save_notes_json_overwrite()
            event.accept()
        else:
            event.ignore()

@click.command()
def reader():
    QApplication.setStyle("windows")
    # QApplication.setStyle("fusion")
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    reader()