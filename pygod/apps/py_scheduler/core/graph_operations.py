from PyQt5.QtChart import QChart, QPieSeries
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
import pyqtgraph as pg
import numpy as np
from functools import partial
import datetime

def create_piechart(self, accordingto = 'income'):
    # year = datetime.date.today().year
    year = self.lineEdit_year_finance.text()
    group_id = f'{year}_{self.comboBox_finance_month.currentText()}'
    series = QPieSeries()
    data = self.pandas_model._data[self.pandas_model._data['group_id']==group_id]
    income_offering_onside = list(data['income_offering_onside'].astype(np.float))[0]
    income_offering_online = list(data['income_offering_online'].astype(np.float))[0]
    total_income = list(data['total_income'].astype(np.float))[0]
    others = total_income - income_offering_online - income_offering_onside
    sorted_dict = {'主日奉献收入':income_offering_onside, '银行转账收入': income_offering_online, '其它收入': others}
    if accordingto == 'income':
        pass
    else:
        pass
    for key, value in sorted_dict.items():
            series.append('{}:{}%'.format(key,round(value/sum(list(sorted_dict.values()))*100,2)), value)

    for i in range(5):
        if (i+1)>len(series.slices()):
            pass
        else:
            slice = series.slices()[-i-1]
            slice.setLabelVisible(True)

    chart = QChart()
    chart.addSeries(series)
    chart.createDefaultAxes()
    chart.setAnimationOptions(QChart.SeriesAnimations)
    if accordingto == 'income':
        chart.setTitle("{}收入占比饼状图:总进项为{}元".format(group_id,round(sum(list(sorted_dict.values())),3)))
    else:
        chart.setTitle("当月支出占比饼状图:总进项为{}元".format(round(sum(list(sorted_dict.values())),3)))

    chart.legend().setVisible(True)
    chart.legend().setAlignment(Qt.AlignLeft)
    self.widget_chart.setChart(chart)
    self.widget_chart.setRenderHint(QPainter.Antialiasing)

def plot_finance_details(self):
    pd_df = self.pandas_model._data
    data = {'x': list(zip(range(len(pd_df)), pd_df['group_id'])),
            'y1': list(pd_df['total_income']),
            'y2': list(pd_df['total_expense'])
            }
    axis_labels = {'bottom': '年月', 'left': '当月总入(€)', 'right': '当月总支(€)'}
    axis_colors = {'bottom': 'w', 'left': 'g', 'right': 'y'} 
    lw = 2
    line_colors = ['g', 'y']
    mouseMove_slot_func = mouseMoved_slot
    make_double_ax_plot(self, data, axis_labels, axis_colors, lw, line_colors, mouseMove_slot_func)

def make_double_ax_plot(self, data = {'x': list(range(10)), 'y1': list(range(10)), 'y2': np.array(range(10))-2}, \
                        axis_labels = {'bottom': 'x', 'left': 'left', 'right': 'right'}, \
                        axis_colors = {'bottom': 'w', 'left': 'g', 'right': 'y'}, lw = 2, colors = ['g', 'y'],
                        mouseMove_slot = lambda x:x):
    self.widget_profile.clear()
    self.ax = self.widget_profile.addPlot(clear = True)
    data = data
    x_tick_lable=[]
    x = []
    ticks = [()]
    if len(data['x'])>0:
        if type(data['x'][0])==tuple:
            for x_, lb_ in data['x']:
                x.append(x_)
                x_tick_lable.append(lb_)
            ticks = data['x']
        else:
            x = data['x']
            x_tick_lable = map(str, x)
            ticks = list(zip(x, x_tick_lable))
        


    self.proxy = pg.SignalProxy(self.ax.scene().sigMouseMoved, rateLimit=60, slot=partial(mouseMove_slot, self))
    self.ax.plot(x=x, y=data['y1'], clear = True, pen=pg.mkPen(colors[0], width=lw))
    self.ax_movable = self.ax.plot(x=[x[0]], y=[data['y1'][0]], pen=None, symbolBrush=(200,200,0), symbolPen='w', symbol='o', symbolSize=10)
    self.ax.getAxis('left').setLabel(axis_labels['left'])
    self.ax.getAxis('left').setPen(pg.mkPen(axis_colors['left'], width=2))
    self.ax.getAxis('bottom').setLabel(axis_labels['bottom'])
    self.ax.getAxis('bottom').setTicks([ticks])

    self.ax_right_curves = _add_one_y_axis(self.ax, axis_labels['right'],2, [axis_labels['right'], 'right_single_point'])
    self.ax_right_curves[0].setData(x=x, y=data['y2'])
    self.ax_right_curves[0].setPen(pg.mkPen(colors[1], width=lw))
    self.ax_right_curves[1].setData(x=x[0:1], y=data['y2'][0:1],pen=None, symbolBrush=(0,200,200),symbol='o', symbolSize=10)

    self.vLine = pg.InfiniteLine(angle=90, movable=False)
    self.hLine = pg.InfiniteLine(angle=0, movable=False)
    self.ax.addItem(self.vLine, ignoreBounds = True)
    self.ax.addItem(self.hLine, ignoreBounds = True)

def _add_one_y_axis(original_ax, y_label, number_curves, names = [], axis_color = 'y', axis_width = 2):
    assert number_curves == len(names), "The total number of curves must be equivalent to the total items in names list"
    original_ax.showAxis('right')
    original_ax.setLabel('right', y_label)
    original_ax.getAxis('right').setPen(pg.mkPen(color = axis_color, width = axis_width))
    #link viewbox
    vb = pg.ViewBox()
    original_ax.scene().addItem(vb)
    original_ax.getAxis('right').linkToView(vb)
    vb.setXLink(original_ax)

    curves = []
    for i in range(number_curves):
        curves.append(pg.PlotDataItem(name=names[i]))
        vb.addItem(curves[-1])

    _updateViews(vb, original_ax)
    original_ax.getViewBox().sigResized.connect(lambda:_updateViews(vb, original_ax))
    #return curve handle list
    return curves    

def mouseMoved_slot(self,evt):
    pos = evt[0]  ## using signal proxy turns original arguments into a tuple
    pd_df = self.pandas_model._data
    data = {'x': list(range(len(pd_df))),
            'y1': list(pd_df['total_income']),
            'y2': list(pd_df['total_expense'])
            }
    if self.ax.sceneBoundingRect().contains(pos):
        mousePoint = self.ax.vb.mapSceneToView(pos)
        self.vLine.setPos(mousePoint.x())
        index = mousePoint.x()
        which = np.argmin(abs(np.array(data['x'])-index))
        x, y1, y2 = [np.array(data['x'])[which]], [np.array(data['y1'])[which]],[np.array(data['y2'])[which]]
        self.ax_movable.setData(x=x, y=y1)
        self.hLine.setPos(y1[0])
        self.vLine.setPos(x[0])
        self.ax_right_curves[1].setData(x=[x], y=[y2])
        #update the combo item, 2023_ --> 1月
        self.comboBox_finance_month.setCurrentText(list(pd_df['group_id'])[which].rsplit('_')[1])
        self.lineEdit_year_finance.setText(list(pd_df['group_id'])[which].rsplit('_')[0])
        create_piechart(self)

def _updateViews(p2, p):
    p2.setGeometry(p.getViewBox().sceneBoundingRect())
    p2.linkedViewChanged(p.getViewBox(), p2.XAxis)