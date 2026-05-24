import PyQt5
import pyqtgraph as pg
from PyQt5.QtCore import QDate, QRectF, Qt
from ..db_opts.common_db_opts import *

class VerticalTextAxis(pg.AxisItem):
    """Bottom AxisItem that draws tick labels rotated 90° (vertical)."""
    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
        p.setRenderHint(p.Antialiasing, False)
        p.setRenderHint(p.TextAntialiasing, True)
        pen, p1, p2 = axisSpec
        p.setPen(pen)
        p.drawLine(p1, p2)
        for pen, p1, p2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(p1, p2)
        for rect, flags, text in textSpecs:
            p.save()
            # anchor at top-centre of the original label rect
            p.translate(rect.x() + rect.width() / 2, rect.y())
            p.rotate(90)
            # after +90° rotation: +x goes down on screen
            # draw text extending downward from the anchor
            p.drawText(
                QRectF(0, -rect.width() / 2, rect.height() * 6, rect.width()),
                Qt.AlignLeft | Qt.AlignVCenter,
                text,
            )
            p.restore()

def init_pandas_model_from_db(self, pandas_data = None):
    args = {'self': self, 
            'tab_indx': 1, 
            'single_collection': True, 
            'contrains': [], 
            'onclicked_func': update_selected_person_info,
            'pandas_data': pandas_data}
    init_pandas_model_from_db_base(**args)

def load_db_pe(self, pandas_data = None, resize = True):
    init_pandas_model_from_db(self, pandas_data)
    if resize:
        self.tableView_book_info.resizeColumnsToContents()
    seed_checkin_for_date(self)

def rerender_tableview(self, pandas_data):
    load_db_pe(self, pandas_data)
    self.tableView_book_info.selectRow(0)

#apis for personal database
def load_img_from_file(self):
    img_format = open_image_file(self, widget_view = self.widget_img_view)
    self.lineEdit_img_format.setText(img_format)

def get_data_for_widget_img_view(self):
    return self.img_in_base64_format

def set_data_for_widget_img_view(self, data):
    self.img_in_base64_format = data
    self.widget_img_view.clear()
    self.widget_img_view.loadImages([image_string_to_qimage(data, img_format = self.lineEdit_img_format.text())])
    self.widget_img_view.show() 

def add_personal_info(self):
    cbs = [init_pandas_model_from_db]
    collection = 'personal_info'
    if self.database[collection].count_documents({'name': self.lineEdit_name_ccg_note.text()})==1:
        update_one_record(self, '人事', collection, constrain= {'name': self.lineEdit_name_ccg_note.text()}, cbs=cbs)
    elif self.database[collection].count_documents({'name': self.lineEdit_name_ccg_note.text()})==0:
        add_one_record(self, '人事', collection, cbs=cbs)

def delete_one_person(self):
    delete_one_record(self, self.database_type, {'name':self.lineEdit_name_ccg_note.text()}, cbs = [init_pandas_model_from_db])

def update_selected_person_info(self, index = None):
    name = self.pandas_model._data['name'].tolist()[index.row()]
    collection =  'personal_info'
    constrain = {'name': name}
    extract_one_record(self, self.database_type, collection, constrain)

def clear_all_input(self, layout_name):
    count = getattr(self, layout_name).count()
    for i in range(count):
        if type(getattr(self, layout_name).itemAt(i).widget()) == PyQt5.QtWidgets.QLineEdit:
            getattr(self, layout_name).itemAt(i).widget().clear()

def seed_checkin_for_date(self):
    """Ensure every member has an attended=False record for the selected date.
    Uses $setOnInsert so existing attended=True records are never overwritten.
    All upserts are sent in one bulk_write round-trip."""
    if not hasattr(self, 'database') or self.database is None:
        return
    from pymongo import UpdateOne
    date_str = self.dateEdit_checkin_date.date().toString("yyyy-MM-dd")
    names = [
        m['name'].strip()
        for m in self.database['personal_info'].find({}, {'name': 1})
        if m.get('name', '').strip()
    ]
    if not names:
        return
    ops = [
        UpdateOne(
            {'name': name, 'date': date_str},
            {'$setOnInsert': {'name': name, 'date': date_str, 'attended': False}},
            upsert=True,
        )
        for name in names
    ]
    self.database['member_checkin'].bulk_write(ops, ordered=False)
    self.statusLabel.setText(f"已为 {date_str} 初始化 {len(names)} 位成员的签到记录 (默认缺席)")

def init_checkin_defaults(self):
    """Set dateEdit_checkin_date to today and date range to last 3 months."""
    today = QDate.currentDate()
    self.dateEdit_checkin_date.setDate(today)
    self.dateEdit_checkin_to.setDate(today)
    self.dateEdit_checkin_from.setDate(today.addMonths(-3))
    self.widget_attendance_chart.setBackground('w')
    self.checkBox_attended.setChecked(False)

def add_checkin_record(self):
    name = self.lineEdit_name_ccg_note.text().strip()
    if not name:
        self.statusLabel.setText("请先在人事信息表中选择人员")
        return
    date_str = self.dateEdit_checkin_date.date().toString("yyyy-MM-dd")
    attended = self.checkBox_attended.isChecked()
    self.database['member_checkin'].replace_one(
        {'name': name, 'date': date_str},
        {'name': name, 'date': date_str, 'attended': attended},
        upsert=True
    )
    status = "出席" if attended else "缺席"
    self.statusLabel.setText(f"签到已记录: {name}  {date_str}  {status}")

def _sundays_in_range(date_from, date_to):
    from datetime import datetime, timedelta
    start = datetime.strptime(date_from, "%Y-%m-%d")
    end = datetime.strptime(date_to, "%Y-%m-%d")
    # advance to first Sunday (weekday 6)
    offset = (6 - start.weekday()) % 7
    cur = start + timedelta(days=offset)
    result = []
    while cur <= end:
        result.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(weeks=1)
    return result

def view_attendance_chart(self):
    name = self.lineEdit_name_ccg_note.text().strip()
    if not name:
        self.statusLabel.setText("请先在人事信息表中选择人员")
        return
    date_from = self.dateEdit_checkin_from.date().toString("yyyy-MM-dd")
    date_to = self.dateEdit_checkin_to.date().toString("yyyy-MM-dd")

    # build lookup from DB records
    records = self.database['member_checkin'].find(
        {'name': name, 'date': {'$gte': date_from, '$lte': date_to}}
    )
    db_map = {r['date']: r.get('attended', False) for r in records}

    # all Sundays in range, defaulting to False when no record exists
    dates = _sundays_in_range(date_from, date_to)
    attended = [1 if db_map.get(d, False) else 0 for d in dates]
    x = list(range(len(dates)))

    chart = self.widget_attendance_chart
    chart.clear()

    if not dates:
        self.statusLabel.setText(f"{name}: 所选时间段内无主日 ({date_from} ~ {date_to})")
        return
    present = sum(attended)
    total = len(attended)

    black = pg.mkColor('k')
    bottom_axis = VerticalTextAxis(orientation='bottom')
    bottom_axis.setHeight(80)
    bottom_axis.setPen(black)
    bottom_axis.setTextPen(black)
    plot = chart.addPlot(title=f"{name} 出勤记录", axisItems={'bottom': bottom_axis})
    plot.titleLabel.item.setDefaultTextColor(black)
    left_ax = plot.getAxis('left')
    left_ax.setPen(black)
    left_ax.setTextPen(black)

    brushes = [pg.mkBrush('g') if a else pg.mkBrush('r') for a in attended]
    bg = pg.BarGraphItem(x=x, height=attended, width=0.6, brushes=brushes)
    plot.addItem(bg)

    rate_curve = plot.plot(x, attended, pen=pg.mkPen('b', width=2), name="出勤率")

    axis = plot.getAxis('bottom')
    axis.setTicks([[(i, d) for i, d in enumerate(dates)]])
    plot.setYRange(0, 1.3)
    plot.setLabel('left', '出席(1) / 缺席(0)', color='k')
    plot.addLegend()

    self.statusLabel.setText(f"{name}: {present}/{total} 次出席 ({present/total*100:.1f}%)")

def process_scan_input(self):
    """Called when scanner gun fires Enter after reading a QR code."""
    scan_value = self.lineEdit_scan_input.text().strip()
    self.lineEdit_scan_input.clear()
    if not scan_value:
        return

    # Look up member by name (QR encodes the member's name)
    record = self.database['personal_info'].find_one({'name': scan_value})
    if not record:
        self.statusLabel.setText(f"未找到成员: {scan_value}")
        return

    name = record['name']
    date_str = self.dateEdit_checkin_date.date().toString("yyyy-MM-dd")
    self.database['member_checkin'].replace_one(
        {'name': name, 'date': date_str},
        {'name': name, 'date': date_str, 'attended': True},
        upsert=True
    )
    # Mirror name into the manual input field for visual feedback
    self.lineEdit_name_ccg_note.setText(name)
    self.checkBox_attended.setChecked(False)
    self.statusLabel.setText(f"扫码签到成功: {name}  {date_str}")

def generate_qr_codes(self):
    """Generate a QR code PNG for every member in personal_info and save to a folder."""
    try:
        import qrcode
    except ImportError:
        self.statusLabel.setText("请先安装 qrcode 库: pip install qrcode[pil]")
        return

    from pathlib import Path
    from PyQt5.QtWidgets import QFileDialog
    import os

    out_dir = QFileDialog.getExistingDirectory(self, "选择二维码保存目录")
    if not out_dir:
        return

    members = list(self.database['personal_info'].find({}, {'name': 1}))
    if not members:
        self.statusLabel.setText("personal_info 集合中无成员数据")
        return

    count = 0
    for m in members:
        name = m.get('name', '').strip()
        if not name:
            continue
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(name)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        # safe filename: replace problematic chars
        safe_name = name.replace('/', '_').replace('\\', '_')
        img.save(os.path.join(out_dir, f"{safe_name}.png"))
        count += 1

    self.statusLabel.setText(f"已生成 {count} 个二维码，保存至: {out_dir}")
