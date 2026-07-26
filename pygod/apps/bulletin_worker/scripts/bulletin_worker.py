import os, sys, subprocess, calendar
from xml.sax.saxutils import escape
from docx.oxml.ns import nsdecls, qn
from docx.oxml import parse_xml
from docx import Document 
from docx.shared import Pt, RGBColor        # Shared classes with defined ”Unit” and ”Colors”
from docx.enum.dml import MSO_THEME_COLOR   # Enumerations class with various definitions
from docx.enum.text import WD_UNDERLINE,WD_ALIGN_PARAGRAPH,WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml.ns import qn
from docx.shared import Inches, Cm, Mm
from docx.text.run import Run
from pathlib import Path
import copy

root = Path(__file__).parent.parent

try:
    from zhconv import convert as _zh_convert
except ImportError:
    _zh_convert = None

def to_simplified(text):
    """normalise the odd traditional character that comes out of the database

    entries are typed by different people, so 奉獻 / 交託 / 牧師 / 莊 turn up mixed in with
    the simplified text. 'zh-hans' converts the script only - unlike 'zh-cn' it does not
    also swap regional wording, which could rewrite names.
    if zhconv is not installed the text is left exactly as it was.
    """
    if _zh_convert==None or text=='':
        return text
    return _zh_convert(text, 'zh-hans')


from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_border(cell, left = False, right = False, up = False, down = False):
    #it is used for border control only (with(out) border lines)
    kwargs_template = {
        'top':{"sz": 0, "val": "nil", "color": "#060606FF", "space": "0"},
        'bottom':{"sz": 0, "color": "#131313", "val": "nil"},
        'start':{"sz": 0, "val": "dashed", "shadow": "true"},
        'end':{"sz": 0, "val": "dashed"}}
    kwargs = {'top': kwargs_template['top'] | {'val': ['nil','single'][int(up)]},
              'bottom':kwargs_template['bottom'] | {'val': ['nil','single'][int(down)]},
              'start':kwargs_template['start'] | {'val': ['nil','single'][int(left)]},
              'end':kwargs_template['end'] | {'val': ['nil','single'][int(right)]}}

    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    # check for tag existnace, if none found, then create one
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)

    # list over all available tags
    for edge in ('start', 'top', 'end', 'bottom', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)

            # check for tag existnace, if none found, then create one
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)

            # looks like order of attributes is important
            for key in ["sz", "val", "color", "space", "shadow"]:
                if key in edge_data:
                    element.set(qn('w:{}'.format(key)), str(edge_data[key]))

class makeBulletin(object):
    top_margin = Mm(6)
    bottom_margin = Mm(6)
    left_margin = Mm(5)
    right_margin = Mm(5)
    shade_color_code = '9CC2E5'#'6495ED'
    #the header block (月报 line + 年度主题 line) is set in the round font, one size for both.
    #the size is what gets nudged by hand when the header has to fit a tighter column
    header_font = 'FZZhunYuan-M02S'
    header_font_size = 12
    #width of one of the two text columns: page width less the margins, less the gap
    #between the columns, halved. a table has to be built to this or word squeezes it
    #and the cell text wraps
    column_width = 396.8
    format_report = {
            'style':'List Number',
            'font_name':'FZShuSong-Z01S',
            'font_size': 10,
            'bold': False,
            'line_spacing': 12,
            'space_after':0,
            'space_before':0,
            'alignment':WD_ALIGN_PARAGRAPH.LEFT,
            'font_style': 'FontReportStyle'
    }
    format_body = {
            'style':'Normal',
            'font_name':'FZShuSong-Z01S',
            'font_size': 10.5,
            'bold': False,
            'line_spacing': 10,
            'space_after':0,
            'space_before':0,
            'alignment':WD_ALIGN_PARAGRAPH.LEFT,
            'font_style': 'FontBodyStyle'
    }
    format_title_big = {
            'style':'Normal',
            'font_name':'FZZhunYuan-M02S',
            'font_size': 24,
            'bold': True,
            'line_spacing': 12,
            'space_after':0,
            'space_before':0,
            'alignment':WD_ALIGN_PARAGRAPH.LEFT,
            'font_style': 'FontTitleBigStyle'
    }
    #the section headings on page 1 are set in the gothic face a point larger than the
    #body, so they read as headings - in the book face at body size they disappear into
    #the text under them
    format_heading = {
            'style':'Normal',
            'font_name':'FZHei-B01S',
            'font_size': 11,
            'bold': True,
            'line_spacing': 10,
            'space_after':5,
            'space_before':5,
            'alignment':WD_ALIGN_PARAGRAPH.LEFT,
            'font_style': 'FontHeadingStyle'
    }
    format_list = [format_title_big, format_body, format_report, format_heading]
    format_style_list = ['FontTitleBigStyle','FontBodyStyle','FontReportStyle','FontHeadingStyle']

    #the two hard breaks cut the bulletin into three independently flowing regions:
    #page 1 (two columns), then the left and the right column of page 2
    regions = ['page1', 'col1', 'col2']
    #the right column of page 2 - the title block down to the meetup list - is set in the
    #round font throughout. everything before it keeps the book face each block asks for
    region_fonts = {'col2': header_font}

    def __init__(self, year, month, font_scale=1.0, line_scale=1.0, line_scales=None):
        self.font_scale = font_scale
        #the leading is scaled per region, leaving the type sizes alone, so each region
        #can be filled to the foot of its column on its own
        self.line_scales = {each: line_scale for each in self.regions}
        if line_scales!=None:
            self.line_scales.update(line_scales)
        self.region = self.regions[0]
        self.doc = Document()
        self.year = year
        self.month = month
        self.change_orientation(self.doc)
        self.make_two_columns()
        self.set_margin()
        self.add_customized_style()
        self.set_list_indent()

    @property
    def line_scale(self):
        return self.line_scales[self.region]

    def font_for_region(self, font_name):
        return self.region_fonts.get(self.region, font_name)

    def add_customized_style(self):
        obj_styles = self.doc.styles
        for i, format in enumerate(self.format_list):
            name = self.format_style_list[i]
            obj_charstyle = obj_styles.add_style(name, WD_STYLE_TYPE.CHARACTER)
            obj_font = obj_charstyle.font
            obj_font.size = int(format['font_size'])
            obj_font.name = format['font_name']
            #obj_font.bold = format['bold']

    def change_orientation(self, doc):
        current_section = doc.sections[-1]
        #new_width, new_height = current_section.page_height, current_section.page_width
        new_height, new_width = Mm(210), Mm(297)
        # new_section = doc.add_section(WD_SECTION.CONTINUOUS)
        current_section.orientation = WD_ORIENT.LANDSCAPE
        current_section.page_width = new_width
        current_section.page_height = new_height
        return current_section

    def make_two_columns(self):
        section = self.doc.sections[-1]
        sectPr = section._sectPr
        cols = sectPr.xpath('./w:cols')[0]
        cols.set(qn('w:num'),'2')
        cols.set(qn('w:space'), '400')

    def set_margin(self):
        current_section = self.doc.sections[-1]
        current_section.top_margin = self.top_margin
        current_section.bottom_margin = self.bottom_margin
        current_section.left_margin = self.left_margin
        current_section.right_margin = self.right_margin

    def add_spacing(self, line_spacing = 10):
        self.add_paragraphs([''], self.format_body, line_spacing = line_spacing)

    def _add_break(self, break_type):
        #the break has to hang off a paragraph, so keep that paragraph as short as
        #possible - otherwise it pushes what follows a whole line down the new column
        pg = self.doc.add_paragraph()
        pg.paragraph_format.line_spacing = Pt(1)
        pg.paragraph_format.space_before = Pt(0)
        pg.paragraph_format.space_after = Pt(0)
        run = pg.add_run()
        run.font.size = Pt(1)
        run.add_break(break_type)

    def add_page_break(self):
        self._add_break(WD_BREAK.PAGE)

    def add_column_break(self):
        self._add_break(WD_BREAK.COLUMN)

    def add_paragraphs(self, par_text_list, format, **kwargs):
        format = copy.copy(format)
        format.update(kwargs)
        format['font_size'] = format['font_size'] * self.font_scale
        format['line_spacing'] = format['line_spacing'] * self.font_scale * self.line_scale
        #the space above and below a paragraph is leading like any other, so it rides the
        #region's scale too - left fixed it would be height the fitter cannot give back,
        #and every point of that is a point it can no longer use to fill the column
        space_after = format['space_after'] * self.line_scale
        space_before = format['space_before'] * self.line_scale
        for each in par_text_list:
            pg = self.doc.add_paragraph(style = format['style'])
            pg.paragraph_format.line_spacing = Pt(format['line_spacing'])
            pg.paragraph_format.space_after = Pt(space_after)
            pg.paragraph_format.space_before = Pt(space_before)
            pg.paragraph_format.alignment = format['alignment']
            _each = each.rsplit('+')
            for idx, each_item in enumerate(_each):
                run = pg.add_run(each_item, style = format['font_style'])
                run.font.name = 'Times New Roman'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), self.font_for_region(format['font_name']))
                run.font.size = Pt(format['font_size'])
                # first segment is bold when '+' is used as bold/normal separator
                if idx == 0 and len(_each) > 1:
                    run.font.bold = True
                else:
                    run.font.bold = format['bold']

    def add_table(self, font_size, content = [[]], row_base = True, alignments = WD_ALIGN_PARAGRAPH.CENTER,style = 'Table Grid', borders = {'left':False,'right':False,'up':False,'down':False}, row_height_factor=1.5, bold_cols=None, bold_rows=None, row_spans=None, bold_cols_by_row=None, col_widths=None, valign=None, outer_sides_only=False):
        assert type(content)==list, "The content of table must be in a list form"
        assert len(content)>0, "There is nothing to fill the table"
        assert len(content[0])>0, "Column or row content is empty"
        font_size = font_size * self.font_scale
        if row_base:
            rows = len(content)
            cols = len(content[0])
        else:
            cols = len(content)
            rows = len(content[0])
        if row_spans!=None:
            #the grid is as wide as the spans say, not as wide as the first row's cells
            cols = sum(row_spans[0])
        tb = self.doc.add_table(rows = rows, cols=cols, style = style)
        #python-docx builds the table as wide as the whole text area, which is twice the
        #column it has to live in -> every table is pinned to the real column width, so it
        #spans the column exactly instead of being squeezed or left short of the edge
        if col_widths==None:
            col_widths = [self.column_width/cols]*cols
        assert len(col_widths)==cols, 'one width is needed per grid column'
        #col_widths only says how the columns relate to each other - rescale them so the
        #table spans the column exactly whatever numbers were handed in
        col_widths = [each*self.column_width/sum(col_widths) for each in col_widths]
        tb.autofit = False
        for gridCol, each in zip(tb._tbl.find(qn('w:tblGrid')).findall(qn('w:gridCol')), col_widths):
            gridCol.set(qn('w:w'), str(Pt(each).twips))
        if type(alignments)!=list:
            alignments = [alignments]*cols
        else:
            assert len(alignments)==cols, 'Not enough alignment signatures!'
        #tb.autofit = True
        for i in range(rows):
            if row_base:
                row_content = content[i]
            else:
                row_content = [each[i] if i<len(each) else '' for each in content]
            #row_spans lets rows of a single table hold different numbers of cells - the
            #contact list and the finance report both need that, and splitting them into
            #one table per row shape would leave gaps between the pieces.
            #cell_slots holds, per logical cell, the grid column it starts at
            if row_spans==None:
                cell_slots, spans = list(range(cols)), [1]*cols
            else:
                spans = row_spans[i]
                assert sum(spans)==cols, f'row {i} spans {sum(spans)} of {cols} grid columns'
                cell_slots, at = [], 0
                for span in spans:
                    cell_slots.append(at)
                    at = at + span
                #merging by grid index stays valid: python-docx keeps one entry per grid
                #column and repeats the merged cell
                for slot, span in zip(cell_slots, spans):
                    if span>1:
                        tb.rows[i].cells[slot].merge(tb.rows[i].cells[slot+span-1])
            #an incomplete schedule (missing db record, or only some weeks filled in) gives
            #rows shorter than the header row -> pad with blanks so the table still builds
            if len(row_content)<len(cell_slots):
                row_content = list(row_content) + ['']*(len(cell_slots)-len(row_content))
            tb.rows[i].height = Pt(font_size * row_height_factor * self.line_scale)
            cells = tb.rows[i].cells
            for j, slot in enumerate(cell_slots):
                if outer_sides_only:
                    #rule only down the two outer edges of the table, not between columns
                    cell_borders = dict(borders)
                    cell_borders['left'] = borders['left'] and slot==0
                    cell_borders['right'] = borders['right'] and (slot+spans[j])==cols
                else:
                    cell_borders = borders
                set_cell_border(cells[slot], **cell_borders)
                cells[slot].text = row_content[j]
                if valign!=None:
                    cells[slot].vertical_alignment = valign
                #a merged cell is as wide as all the grid columns it covers
                cells[slot].width = Pt(sum(col_widths[slot:slot+spans[j]]))
                is_bold = ((bold_cols is not None and j in bold_cols) or
                           (bold_rows is not None and i in bold_rows) or
                           (bold_cols_by_row is not None and j in bold_cols_by_row.get(i, [])))
                for pg in cells[slot].paragraphs:
                    pg.paragraph_format.line_spacing = Pt(font_size * 1.2 * self.line_scale)
                    pg.alignment = alignments[j]
                    for run in pg.runs:
                        run.font.name = 'Times New Roman'
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), self.font_for_region("FZShuSong-Z01S"))
                        run.font.size = Pt(font_size)
                        run.font.bold = is_bold
        return tb

    def _shade_cell(self, cell, fill=None, color=None):

        if fill:
            shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), fill))
            cell._tc.get_or_add_tcPr().append(shading_elm)

        if color:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = RGBColor.from_string(color)

    def shade_row(self, tb, which_row, fill, color):
        for cell in tb.rows[which_row].cells:
            self._shade_cell(cell, fill, color)

    #the logo and the whatsapp qr code float over the text rather than sitting in the
    #flow, so they can hang off the right edge of their column
    logo_file = root / 'src' / 'resources' / 'ccg_logo.png'
    qr_file = root / 'src' / 'resources' / 'qr_whatsapp.png'
    facebook_file = root / 'src' / 'resources' / 'facebook.png'
    #stands in for an icon while the cell is still plain text
    icon_token = '{icon}'

    def replace_token_with_image(self, cell, img_path, height, token = None):
        """swap the marker in a table cell for a picture set in the line of the text

        the table is built from strings, so an icon that has to sit mid-sentence cannot go
        in with the content. the run carrying the marker is split in three - the text
        before it, the picture, and the text after - each a copy of the original, so they
        all keep the font and size the table gave them.
        """
        token = token if token!=None else self.icon_token
        for pg in cell.paragraphs:
            for run in pg.runs:
                if token not in run.text:
                    continue
                before, after = run.text.split(token, 1)
                run.text = before
                picture, tail = copy.deepcopy(run._r), copy.deepcopy(run._r)
                run._r.addnext(tail)
                run._r.addnext(picture)
                picture_run, tail_run = Run(picture, pg), Run(tail, pg)
                picture_run.text = ''
                picture_run.add_picture(str(img_path), height=Pt(height))
                tail_run.text = after
                return

    anchor_xml = (
        '<wp:anchor {nsdecls} distT="0" distB="0" distL="0" distR="0" simplePos="0"'
        ' relativeHeight="{depth}" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">'
        '<wp:simplePos x="0" y="0"/>'
        '<wp:positionH relativeFrom="{rel_h}"><wp:posOffset>{off_x}</wp:posOffset></wp:positionH>'
        '<wp:positionV relativeFrom="{rel_v}"><wp:posOffset>{off_y}</wp:posOffset></wp:positionV>'
        '<wp:extent cx="{cx}" cy="{cy}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        '<wp:wrapNone/>'
        '<wp:docPr id="{pic_id}" name="{name}"/>'
        '<wp:cNvGraphicFramePr/>'
        '</wp:anchor>')

    def add_floating_picture(self, img_path, width, height, off_x, off_y, name,
                             rel_h = 'column', rel_v = 'paragraph', paragraph = None):
        """hang a floating picture off a paragraph at a fixed offset, in points

        python-docx can only place a picture inline, so the picture goes in inline first
        and its wp:inline wrapper is then swapped for a wp:anchor - that is what lets the
        image overlap the text instead of taking up a line of its own.
        """
        img_path = str(img_path)
        assert os.path.exists(img_path), f"The image {img_path} is not existing!"
        if paragraph==None:
            paragraph = self.doc.paragraphs[-1]
        run = paragraph.add_run()
        run.add_picture(img_path, width=Pt(width), height=Pt(height))
        drawing = run._r.find(qn('w:drawing'))
        inline = drawing.find(qn('wp:inline'))
        self._pic_id = getattr(self, '_pic_id', 1000) + 1
        anchor = parse_xml(self.anchor_xml.format(nsdecls=nsdecls('wp'),
                                                  depth=self._pic_id,
                                                  rel_h=rel_h, rel_v=rel_v,
                                                  off_x=Pt(off_x).emu, off_y=Pt(off_y).emu,
                                                  cx=Pt(width).emu, cy=Pt(height).emu,
                                                  pic_id=self._pic_id, name=name))
        anchor.append(inline.find(qn('a:graphic')))
        drawing.replace(inline, anchor)

    def _insert_img_in_table(self, tb_obj, img_path, row, col, width, height):
        pg = tb_obj.rows[row].cells[col].paragraphs[0]
        run = pg.add_run()
        assert os.path.exists(img_path), "The provided image path is not existing!"
        run.add_picture(img_path, width = Pt(width), height = Pt(height))

    def add_finance_table(self, table_data):
        assert type(table_data)==dict, 'The table data has to be given in dict format'
        assert 'income' in table_data and 'expanse' in table_data and 'summary' in table_data, "The table data must have three keys: income and expanse and summary. One or both are missing"
        self.add_paragraphs(['财务报告（单位：EUR）'],self.format_title_big, font_size=12)
        income_end = len(table_data['income'])
        #one table on a 4 column grid: the income/expense lines take two cells of two
        #columns each, the summary rows underneath take all four
        main = [['进项','']]+table_data['income']+[['支出','']]+table_data['expanse']
        summary = [['','总进','总支','结余']]+table_data['summary']
        if len(table_data['summary'])<2:
            #no year-to-date row in the content file - leave the placeholder to fill by hand
            summary = summary+[["202？（?-?月)年度",'?? €','?? €','?? €']]
        #the label side takes the wider share: the longest entry ('奉献 OMF 葛美恩传道德语青少年
        #福音事工') has to stay on one line, while the amounts are short
        row_spans = [[2,2]]*len(main) + [[1,1,1,1]]*len(summary)
        alignments = [WD_TABLE_ALIGNMENT.LEFT,WD_TABLE_ALIGNMENT.RIGHT,WD_TABLE_ALIGNMENT.RIGHT,WD_TABLE_ALIGNMENT.RIGHT]
        tb = self.add_table(font_size=10, content=main+summary, alignments=alignments,borders = {'left':False,'right':False,'up':False,'down':False}, row_spans=row_spans, bold_rows=[0, income_end+1, len(main)], col_widths=[105, 100, 96, 95.8])
        month = self.month
        pre_month = month - 1 if month!=1 else 12
        year_pre_month = self.year if month!=1 else self.year - 1
        self.add_spacing(3)
        self.add_spacing(3)
        footnote = table_data.get('footnote', {})
        #the figures are quoted as of the last day of the month the report covers
        last_day = calendar.monthrange(year_pre_month, pre_month)[1]
        def _amounts(tag, count):
            #'???' keeps an unfilled figure visible for the hand-editing pass
            values = [each.replace('€','').strip() for each in footnote.get(tag, [])]
            return (values+['???']*count)[:count]
        deficit, = _amounts('deficit', 1)
        build_in, build_out, build_rest = _amounts('fund_building', 3)
        seminary_out, seminary_rest = _amounts('fund_seminary', 2)
        mission_rest, = _amounts('fund_mission', 1)
        self.add_paragraphs([f'截止到{year_pre_month}年{pre_month}月，教会主要账户（不含各类基金）累计收支赤字为 {deficit} 欧，请弟兄姊妹为此在祷告中纪念，我们相信  神会有预备。'], format=self.format_body, font_size = 9, bold = True, alignment=WD_ALIGN_PARAGRAPH.LEFT)
        self.add_spacing(3)
        self.add_paragraphs([f'* 堂址维护基金：至{pre_month}月{last_day}日止，总进为{build_in}欧，总支为{build_out}欧，结余为{build_rest}欧。\
                             \n* 神学教育基金：支持 CCG Bremen 神学生支出 {seminary_out} 欧，至{pre_month}月{last_day}日止，结余为{seminary_rest}欧。 \n* 教会宣教广传事工基金：至 {pre_month} 月 {last_day} 日止，结余 {mission_rest} 欧。'], format=self.format_body, font_size = 9, alignment=WD_ALIGN_PARAGRAPH.LEFT)
        self.add_spacing(3)

    def add_corresponding_table(self):
        self.add_paragraphs(['教会牧者执事联络电话'],self.format_title_big, font_size = 12)
        table_content = [
                        ['吴振忠牧师温淑芳师母','04068860416','管惠萍牧师','04076900694'],
                        ['校园事工宣教士吴雨洁','015753937836','青少年事工宣教士葛美恩'],
                        ['主　席','邵　颢弟兄','017634968872','财务组','马内利弟兄','017655495554'],
                        ['秘　书','王泽宇弟兄','015735390792','服务组','余余子姊妹','01794638359'],
                        ['礼拜组','李　帆弟兄','017670728016','教育组','王　榛弟兄','01796843477'],
                        ['图书组','黄罗佳弟兄','017660470014','福音事工组','刘朗朗弟兄','017664073888'],
                        ['管堂组','周　斌弟兄','01796737203','x','x','x'],
        ]
        #one table on a 7 column grid - the pastor rows and the deacon rows hold a
        #different number of cells, so each row gets its own grid spans
        row_spans = [[2,1,2,2],[2,1,4]] + [[1,1,1,1,2,1]]*(len(table_content)-2)
        bold_cols_by_row = {0:[0,2], 1:[0,2]}
        for i in range(2, len(table_content)):
            bold_cols_by_row[i] = [0,3]
        bold_cols_by_row[len(table_content)-1] = [0]
        #name columns wide enough that '邵　颢弟兄' does not break over two lines
        col_widths = [58.8, 58.8, 89.3, 58.7, 31.0, 27.7, 89.4]
        self.add_table(font_size = 9, content = table_content, alignments=WD_TABLE_ALIGNMENT.LEFT,borders = {'left':False,'right':False,'up':False,'down':False}, row_spans=row_spans, bold_cols_by_row=bold_cols_by_row, col_widths=col_widths)

    def add_whatsapp_info_table(self):
        #the qr code hangs off the right of the table, level with the two text lines
        self.add_floating_picture(self.qr_file, 46.7, 48.0, off_x=338, off_y=2, name='qr_whatsapp')
        contents = [['欢迎大家加入教会的WhatsApp 通知群组'],['bit.ly/ccgh-whatsapp 获得更多信息 ']]
        self.add_table(font_size=10, content = contents, alignments=WD_TABLE_ALIGNMENT.LEFT,borders = {'left':False,'right':False,'up':False,'down':False})

    def add_lesson_table(self):
        #the facebook page is marked with its own logo - there is no emoji for it, so a
        #placeholder rides through the table build and is swapped for the image after
        contents = [
            ['🏠Dulsberg-Süd 26, 22049 Hamburg','成人主日学','每周日上午09:00'],
            ['🚉乘 U1 至 Straßburger Str. 站下车，','主日崇拜','每周日上午10:30'],
            [' 步行十分钟即至。','幼儿主日学','每周日上午10:30'],
            [f'🌍ccg-ham.de {self.icon_token}ccg.hamburg','儿童主日学','每周日上午10:30'],
            ['🏛chinese-library.de','少年主日学','每周日上午10:30']
        ]
        tb = self.add_table(font_size= 10, content = contents, alignments=WD_TABLE_ALIGNMENT.LEFT,borders = {'left':False,'right':False,'up':False,'down':False}, bold_cols=[1])
        self.replace_token_with_image(tb.rows[3].cells[0], self.facebook_file, height=9)

    def add_meetup_info(self):
        #dotted rule separating the lesson table from the meetup list
        self.add_paragraphs(['…'*47], format = self.format_body, font_name = 'SimSun')
        contents = ['福音性查经+    每周五19:30 （实体）',
        '联络：吴振忠牧师（688 604 16）   ⚓Dulsberg-Süd 26    🚉U1 Straßburger Str.',
        '',
        '线上查经班+    每月第二、四个周三19:30 （线上ZOOM）',
        '联络：管惠萍牧师（769 006 94）',
        '',
        '长青团契+\t     每月第一、三个周五10:00-14:00',
        '联络：吴振忠牧师（688 604 16）   ⚓Blumenau 29   🚉U1 Wartenau',
        '',
        '青年团契+\t     每月周六14:00-16:00 （实体）',
        '联络：刘朗朗弟兄（017664073888）    ⚓Dulsberg-Süd 26   🚉U1 Straßburger Str.',
        '',
        '伉俪团契+\t     每月第二个周六14:00-16:30 （实体）',
        '联络：黄罗佳弟兄、杨琪姊妹（017660470014） 陈玮弟兄、蔡文彦姊妹（015142674175） 张勇弟兄、黄多姊妹（017623606936）',
        '',
        '妈妈小组+\t     每月第一、三个周五晚20:30-22:00 （线上ZOOM）',
        '联络：徐圣佳姊妹（017670728041）   ⚓Dulsberg-Süd26    🚉U1 Straßburger Str.',
        '',
        '🎦Zoom ID: 5861908437，会议室密码: 903600']
        self.add_paragraphs(contents, format = self.format_body, line_spacing = 12)

    def add_preach_table(self, contents):
        #append icon at the beginning place
        if len(contents)==4:
            contents = [['📅']+contents[0],\
                        ['✒️']+contents[1],\
                        ["🤵"]+contents[2],\
                        ['🏷️']+contents[3]]
        #ruled top and bottom, plus a line down each outer edge - nothing between columns
        tb = self.add_table(font_size= 10, content = contents, alignments=WD_TABLE_ALIGNMENT.CENTER,borders = {'left':True,'right':True,'up':True,'down':True}, outer_sides_only=True, valign=WD_ALIGN_VERTICAL.CENTER)
        self.shade_row(tb, 0, self.shade_color_code, None)
        self.shade_row(tb, 2, self.shade_color_code, None)

    def test_add_preach_table(self):
        contents = [['📅','10月1日','10月8日','10月15日','10月22日','10月29日'],
                    ['✒️','事奉 • 我 •我的家','敬畏神','耶稣接待我们','让基督在我\n身上照常显大','从深处发出\n的祷告'],
                    ["🤵",'管惠萍牧师','吴振忠牧师','吴雨洁传道','吴振忠牧师','吴温淑芳师母'],
                    ['✝️','约书亚记\n24:14-18','传道书\n12:9-14','路加福音\n9:10-17','腓立比书\n1:1-27','诗篇130, \n131']]
        self.add_preach_table(contents)

    def add_header_info(self,contents = ['年度主题：复兴我灵、更新我心','我要使他们有合一的心，也要将新灵放在他们里面，又从他们肉体中除掉石心，赐给他们肉心，使他们顺从我的律例，谨守遵行我的典章。他们要作我的子民，我要作他们的　神。							以西结书11 : 19-20']):
        year, month = self.year, self.month
        year_next_month = year if month!=12 else year + 1
        next_month = month + 1 if month!=12 else 1
        self.add_paragraphs( ['德国汉堡华人基督教会'], format=self.format_title_big, font_size = 24, space_before=20, space_after = 2)
        #logo sits top right of the column, level with the church name. the offset is
        #measured from the title paragraph, and has to leave the top of the image on the
        #page - any further up and the printer clips it
        self.add_floating_picture(self.logo_file, 55.4, 53.5, off_x=331, off_y=-12, name='ccg_logo')
        self.add_paragraphs( [f'{year_next_month}年{next_month}月份月报'], format=self.format_body, font_name = self.header_font, font_size = self.header_font_size, space_before =8, space_after =2)
        #the YearScripture section holds the theme on the first line and the verse on the second
        theme = contents[0] if len(contents)>0 else ''
        verse = contents[1] if len(contents)>1 else ''
        if theme:
            #the db record often carries the '年度主题：' prefix already -> don't print it twice
            theme = theme[len('年度主题：'):] if theme.startswith('年度主题：') else theme
            self.add_paragraphs( [f'年度主题：{theme}'], format=self.format_body, font_name = self.header_font, font_size = self.header_font_size,space_after = 2, space_before = 5)
        if verse:
            self.add_year_scripture_box(verse)

    #a table cell can only have square corners, so the year verse goes in a rounded
    #rectangle shape instead. arcsize is in 1/65536 of the shorter side
    verse_box_xml = (
        '<w:p {nsdecls} xmlns:v="urn:schemas-microsoft-com:vml">'
        '<w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr><w:r><w:pict>'
        '<v:roundrect style="width:{width}pt;height:{height}pt;mso-fit-shape-to-text:t"'
        ' arcsize="{arcsize}f" fillcolor="white" strokecolor="black" strokeweight=".5pt">'
        '<v:textbox inset="6pt,4pt,6pt,4pt"><w:txbxContent>'
        '<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="{line}" w:lineRule="exact"/></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"'
        ' w:eastAsia="{font}"/><w:sz w:val="{half_pt}"/></w:rPr>'
        '<w:t xml:space="preserve">{verse}</w:t></w:r></w:p>'
        '</w:txbxContent></v:textbox></v:roundrect></w:pict></w:r></w:p>')

    def add_year_scripture_box(self, verse, font_size = 10, spacing = 4):
        """the year verse, in a rounded box with a little air above and below"""
        self.add_spacing(spacing)
        box = self.verse_box_xml.format(nsdecls=nsdecls('w'),
                                        width=round(self.column_width-6, 1),
                                        height=round(font_size*2.2, 1),
                                        arcsize=8000,
                                        line=int(font_size*1.4*20*self.line_scale),
                                        font=self.font_for_region(self.format_body['font_name']),
                                        half_pt=int(font_size*2),
                                        verse=escape(verse))
        #add_paragraph puts the element in the right place (before the sectPr); swap the
        #empty paragraph for the shape once it is parked there
        anchor = self.doc.add_paragraph()._p
        anchor.addprevious(parse_xml(box))
        anchor.getparent().remove(anchor)
        self.add_spacing(spacing)

    def add_report(self, contents):
        self.add_paragraphs(['教会通讯'],format = self.format_heading)
        self.add_paragraphs(contents, format = self.format_report, line_spacing = 15)

    #how far the numbered lists are indented, in twips, matching the polished bulletins.
    #word's own default for 'List Number' is 360
    list_indent = 442

    def set_list_indent(self, indent = None):
        """indent the numbered lists at the numbering definition rather than the paragraph

        word takes two separate measurements off the level: the number is dropped on the
        level's tab stop, and the wrapped lines start at the level's indent. setting only
        the paragraph indent moves the second and leaves the first where it was, which
        pulls the two apart instead of lining them up - so both are set here, together.
        """
        indent = self.list_indent if indent==None else indent
        w = qn('w:ind').rsplit('}')[0] + '}'
        numbering = self.doc.part.numbering_part.element
        for lvl in numbering.iter(f'{w}lvl'):
            style = lvl.find(f'{w}pStyle')
            if style==None or style.get(f'{w}val')!='ListNumber':
                continue
            ppr = lvl.find(f'{w}pPr')
            if ppr==None:
                continue
            for tab in ppr.iter(f'{w}tab'):
                tab.set(f'{w}pos', str(indent))
            ind = ppr.find(f'{w}ind')
            if ind!=None:
                ind.set(f'{w}left', str(indent))
                ind.set(f'{w}hanging', str(indent))

    def restart_list_numbering(self):
        """give the next 'List Number' paragraphs a numbering of their own, starting at 1

        the report list and the prayer list share the 'List Number' style, so word runs one
        sequence straight through both. this clones the style's numbering with a start
        override and hands back the new numId to put on the prayer paragraphs.
        """
        w = qn('w:numId').rsplit('}')[0] + '}'
        numbering = self.doc.part.numbering_part.element
        style_num = self.doc.styles['List Number'].element.find(f'.//{w}numPr/{w}numId')
        if style_num==None:
            return None
        abstract = None
        for num in numbering.findall(f'{w}num'):
            if num.get(f'{w}numId')==style_num.get(f'{w}val'):
                abstract = num.find(f'{w}abstractNumId').get(f'{w}val')
        if abstract==None:
            return None
        new_id = str(max(int(each.get(f'{w}numId')) for each in numbering.findall(f'{w}num')) + 1)
        numbering.append(parse_xml(
            f'<w:num {nsdecls("w")} w:numId="{new_id}">'
            f'<w:abstractNumId w:val="{abstract}"/>'
            '<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride>'
            '</w:num>'))
        return new_id

    def add_pray_list(self, contents):
        self.add_paragraphs(['感恩、代祷事项'],format = self.format_heading)
        first = len(self.doc.paragraphs)
        self.add_paragraphs(contents, format = self.format_report)
        num_id = self.restart_list_numbering()
        if num_id!=None:
            for pg in self.doc.paragraphs[first:]:
                pg._p.get_or_add_pPr().append(parse_xml(
                    f'<w:numPr {nsdecls("w")}><w:ilvl w:val="0"/>'
                    f'<w:numId w:val="{num_id}"/></w:numPr>'))

    def add_monthly_scripture(self, contents):
        self.add_paragraphs(['†每月金句'],format = self.format_body, font_size = 12, bold = True)
        self.add_spacing(3)
        self.add_paragraphs(contents, format = self.format_body, font_size = 10)
        
    def add_monthly_service_table(self, contents):
        self.add_paragraphs(['主日崇拜服事表'],format = self.format_heading)
        tb = self.add_table(font_size=10, content=contents,borders = {'left':True,'right':True,'up':True,'down':True}, bold_cols=[0], bold_rows=[0], valign=WD_ALIGN_VERTICAL.CENTER)
        for i in range(1, len(contents),2):
            self.shade_row(tb, i, self.shade_color_code, '000000')

    def add_last_month_record_table(self, offering_attendence_content, bible_study_attendence_content):
        self.add_paragraphs(['奉献纪录，主日及各查经小组出席人数'],format = self.format_heading)
        tb = self.add_table(font_size=10, content=offering_attendence_content,borders = {'left':True,'right':True,'up':True,'down':True}, bold_cols=[0], bold_rows=[0])
        self.shade_row(tb, 0, self.shade_color_code, '000000')
        self.add_spacing(5)
        tb = self.add_table(font_size=10, content=bible_study_attendence_content,borders = {'left':True,'right':True,'up':True,'down':True}, bold_cols=[0], bold_rows=[0])
        self.shade_row(tb, 0, self.shade_color_code, '000000')

    #the account itself is set a size larger than the note about the payment codes
    bank_lines = [('教会奉献账号 户名 CCG Hamburg e.V.银行 Ev. Kreditgenossenschaft e.G.', 11),
                  ('IBAN DE73 5206 0410 0006 6031 30     BIC/SWIFT GENODEF1EK1', 11),
                  ('汇款特别奉献请在汇款目的栏填写相应的两位数字代码（不填表示为一般奉献）', 10),
                  ('00 建堂基金 / 02 神学教育基金 / 12 吕贝克查经班', 10)]

    def add_bank_info(self, spacing = 4):
        #one shaded cell holding the four lines, each written on its own so the two note
        #lines can be a point smaller than the account lines above them
        tb = self.add_table(font_size= 11, content = [['']], alignments=WD_TABLE_ALIGNMENT.CENTER,borders = {'left':False,'right':False,'up':False,'down':False})
        cell = tb.rows[0].cells[0]
        last = len(self.bank_lines) - 1
        for i, (text, size) in enumerate(self.bank_lines):
            pg = cell.paragraphs[0] if i==0 else cell.add_paragraph()
            pg.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pg.paragraph_format.line_spacing = Pt(size * 1.25 * self.line_scale)
            #the air above and below sits on the outer two lines, so it falls inside the
            #shaded cell rather than pushing the shading apart from the rest of the column
            pg.paragraph_format.space_before = Pt(spacing if i==0 else 0)
            pg.paragraph_format.space_after = Pt(spacing if i==last else 0)
            run = pg.add_run(text)
            run.font.name = 'Times New Roman'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), self.font_for_region(self.format_body['font_name']))
            run.font.size = Pt(size * self.font_scale)
        self.shade_row(tb,0,self.shade_color_code,None)

    def test_add_finance_table(self):
        table_data = {'income':[['主日敬拜奉献',	'+1,612.88']]*3,
                      'expanse': [['奉献FMCD吴牧师德国宣教事工',	'-3,000.00']]*3,
                      'summary':[['2022年11月份','+11,362.39','-12,933.49','-1,571.10']]*2}
        self.add_finance_table(table_data)

    def test_add_monthly_service_table(self):
        content = [
            ['日期',	'1月1日',	'1月8日',	'1月15日',	'1月22日',	'1月29日'],
            ['司会',	'邵　颢弟兄',	'陈思源姊妹',	'马内利弟兄',	'黄代伟弟兄',	'刘芸竺姊妹'],
            ['司琴',	'邵　颢弟兄',	'陈思源姊妹',	'马内利弟兄',	'黄代伟弟兄',	'刘芸竺姊妹'],
            ['领唱小组',	'陈思源姊妹\n袁家辉弟兄',	'韩　菲姊妹\n刘朗朗弟兄',	'郑美灵姊妹\n谢泰昌弟兄',	'周诚英姊妹\n王　进弟兄',	'莊雅玲姊妹\n黄代伟弟兄'],
            ['领唱小组',	'陈思源姊妹\n袁家辉弟兄',	'韩　菲姊妹\n刘朗朗弟兄',	'郑美灵姊妹\n谢泰昌弟兄',	'周诚英姊妹\n王　进弟兄',	'莊雅玲姊妹\n黄代伟弟兄'],
        ]*3
        self.add_monthly_service_table(content)

    def test_add_last_month_record_table(self):
        table1 = [['日　期','8月6日','8月13日','8月20日','8月27日'],
        ['成人 / 少儿','76 / 22+4','92 / 30+4','92 / 41+4','103 / 44+4'],
        ['奉　献','524.74 €','513.99 €' ,'541.29 €','384.93 €']]

        table2 = [['日　期','8月4日','8月9/11日','8月18日','8月23/25日'],
        ['福音性查经','10','16','8','9'],
        ['线上查经班','-','13','-','11']]

        self.add_last_month_record_table(table1, table2)

    def test_add_report(self):
        pars = [
            '本月每周日 9:00-10:00 的成人主日学主题为《箴言》解读，由管惠萍传道主讲，欢迎所有弟兄姊妹准时参加。',
            '元月 8 日（日）主日爱宴后会有诗班练唱，请诗班和参与的弟兄姊妹预留时间参加。',
            '元月份青年团契的活动安排，请联系马内利弟兄或见青年团契的通知。欢迎青年弟兄姊妹及朋友们参加。',
            '元月 15 日（日）爱宴后将召开2023年度会友大会，会中有2022年执事分享并同时进行教会新一届执事改选。执事候选人名单已由执事会选举产生，请拿到选票的会友在神面前安静祷告后，选出合神心意的九位执事。如有查询，请与李帆弟兄联系。',
            '元月 22 日（日）爱宴后教会举办2023年新春聚会，主题为《岁岁平安》。欢迎大家多多邀请亲朋好友，和我们共度传统佳节。请愿意参与表演节目的弟兄姊妹尽快与邵颢弟兄报名。',
            '元月 29 日（日）爱宴后将举行教会新年感恩祷告会，一年伊始，让我们同心向上主献上感恩及祷告。',
            '2023年德国华人基督徒门徒造就营将于4月6日至10日（复活节假期）在法兰克福青年旅馆举行。营会讲员为：孙宝玲牧师（台南神学院客座教授）和黄正人长老（中华福音神学院老师，台北基督徒双和礼拜堂长老）。主题是 “重建生命、分别为圣”。同时会有多堂专题工作坊。教会团体报名截止日期是 2023年1月29日。名额有限，请弟兄姊妹踊跃向刘朗朗弟兄报名。',
            '4月6日至10日（复活节假期） 同时会有在Wiesbaden举行的德语青年营。报名截止日期是 2023年2月28日。详情及报名请联络李衍炀牧师 youth@chinese-library.de。',
            '本月寿星：沈轶蕴、余余子、付军、谢泰昌、徐敏书、孙路加、李大鹏、张天轶、施俊浩、张在勇、徐小琼、陈泇希、郑炜、吴宇辰(辰辰) 、钱恩雨（Anneliese）。',
        ]
        self.add_report(pars)
        self.add_spacing(10)
        self.add_pray_list(pars)

    def _extract_content_from_file(self, file_path, content_type):
        possible_types = ['YearScripture','MonthlyScripture','MonthlyServiceTable','Report','Pray','LastMonthRecord','FinanceTable','PreachTable']
        assert content_type in possible_types, f"Not one of the possible content type. Possible ones are:\n {possible_types}"
        begin_line, end_line = None, None
        begin_tag, end_tag = f'<{content_type}>', f'</{content_type}>'
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith(begin_tag):
                    begin_line = i
                elif line.startswith(end_tag):
                    end_line = i
                    break
            if begin_line==None:
                begin_line = -1
                end_line = 0
            raw = [to_simplified(each.rstrip()) for each in lines[begin_line+1:end_line]]
            if content_type=='MonthlyServiceTable':
                raw = [each.replace('+','\n') for each in raw]
            if content_type in ['YearScripture','MonthlyScripture','Report', 'Pray']:
                return raw# paragraph content like ['item1','item2']
            else:#table content like [['item1','item2'],['item3','item4']]
                formated_content = []
                for each in raw:
                    if content_type == 'FinanceTable':
                        formated_content.append(each.rsplit('&'))
                    else:
                        formated_content.append(each.rsplit(','))
                if content_type == 'FinanceTable':
                    #further formating is needed for finance table content
                    #rows tagged with a leading '@' are not table lines: they carry the
                    #year-to-date row and the fund/deficit figures of the footnote.  Content
                    #files written before those existed simply have none of them.
                    extras = {}
                    rows = []
                    for row in formated_content:
                        if row[0].startswith('@'):
                            extras[row[0][1:]] = row[1:]
                        else:
                            rows.append(row)
                    end_income_index = 0
                    for i in range(len(rows)-1):
                        if rows[i][-1].startswith('+'):
                            end_income_index = i+1
                    formated_content_dict = {'income':rows[0:end_income_index],
                                            'expanse': rows[end_income_index:-1],
                                            'summary': [rows[-1]]}
                    if 'summary_ytd' in extras:
                        formated_content_dict['summary'].append(extras.pop('summary_ytd'))
                    formated_content_dict['footnote'] = extras
                    return formated_content_dict
                else:
                    return formated_content

    def prepare_contents(self, file_path):
        assert os.path.exists(file_path), 'The given file is not existing!'
        self.contents = {}
        for content_type in  ['YearScripture','MonthlyScripture','MonthlyServiceTable','Report','Pray','LastMonthRecord','FinanceTable','PreachTable']:
            self.contents[content_type] = self._extract_content_from_file(file_path, content_type)

    def make_doc_in_one_go(self, content_file_path, doc_file_path = None, section_spacing = 6):
        self.prepare_contents(content_file_path)
        self.add_monthly_scripture(contents=self.contents['MonthlyScripture'])
        self.add_spacing(line_spacing=section_spacing)
        self.add_monthly_service_table(contents = self.contents['MonthlyServiceTable'])
        self.add_spacing(line_spacing = section_spacing)
        self.add_report(self.contents['Report'])
        self.add_spacing(line_spacing = section_spacing)
        self.add_pray_list(self.contents['Pray'])
        self.add_spacing(line_spacing = section_spacing)
        self.add_last_month_record_table(self.contents['LastMonthRecord'][0:3],self.contents['LastMonthRecord'][3:])
        #the finance report has to open page 2 in the left column
        self.add_page_break()
        self.region = 'col1'
        self.add_finance_table(self.contents['FinanceTable'])
        self.add_spacing(line_spacing = section_spacing)
        self.add_corresponding_table()
        self.add_spacing(line_spacing = section_spacing)
        self.add_whatsapp_info_table()
        #the title block has to open the right column of page 2
        self.add_column_break()
        self.region = 'col2'
        self.add_header_info(self.contents['YearScripture'])
        self.add_spacing(line_spacing = section_spacing)
        self.add_preach_table(self.contents['PreachTable'])
        self.add_spacing(line_spacing = section_spacing)
        self.add_lesson_table()
        self.add_spacing(line_spacing = section_spacing)
        self.add_meetup_info()
        self.add_spacing(line_spacing = section_spacing)
        self.add_bank_info()
        self.add_spacing(line_spacing = section_spacing)
        self.save_doc(doc_file_path)

    def save_doc(self, file_path = None):
        if file_path==None:
            file_path = root / 'src' / f'bulletin-{self.year}-{self.month}.docx'
        self.doc.save(file_path)
        self.saved_path = str(file_path)

#a column runs from just under the top margin to just above the bottom one
COLUMN_TOP = 17
COLUMN_BOTTOM = 570
COLUMN_HEIGHT = COLUMN_BOTTOM - COLUMN_TOP
#page 1 flows through two columns before its region ends, the page 2 regions only one
REGION_COLUMNS = {'page1': 2, 'col1': 1, 'col2': 1}

def measure_layout(doc_path):
    """how many pages, and the y at which each region runs out, as word lays it out

    none of this is in the .docx - it only exists once word has laid the document out -
    so this drives word over com. the regions are found by the break characters
    (chr 12 = page break, chr 14 = column break) so the probe stays ascii.
    returns None when word cannot be reached, and the caller then skips fitting.
    """
    probe = ("$ErrorActionPreference='Stop';"
             "$w=New-Object -ComObject Word.Application;$w.Visible=$false;$w.DisplayAlerts=0;"
             f"$d=$w.Documents.Open('{doc_path}',$false,$true);$d.Repaginate();"
             "$a=-1;$b=-1;"
             "foreach($p in $d.Paragraphs){$t=$p.Range.Text;"
             "if($a -lt 0 -and $t.Contains([char]12)){$a=[math]::Round($p.Range.Information(6),0)};"
             "if($b -lt 0 -and $t.Contains([char]14)){$b=[math]::Round($p.Range.Information(6),0)}};"
             "$c=[math]::Round($d.Paragraphs.Item($d.Paragraphs.Count).Range.Information(6),0);"
             "Write-Output (($d.ComputeStatistics(2)),$a,$b,$c -join ',');"
             "$d.Close($false);$w.Quit()")
    try:
        done = subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',probe],
                              capture_output=True, text=True, timeout=180)
        pages, a, b, c = [int(float(each)) for each in done.stdout.strip().rsplit('\n')[-1].split(',')]
        return pages, {'page1': a, 'col1': b, 'col2': c}
    except Exception:
        return None

def main(year, month, content_file, doc_file=None, font_scale=1.0, fit_pages=2,
         line_scale=1.0, rounds=8, tolerance=16, min_line_scale=0.6, max_line_scale=2.5,
         progress=None):
    """build the bulletin and set each region's leading so it fills its column

    the two hard breaks in make_doc_in_one_go pin the finance report to the top of the
    left column of page 2 and the title block to the top of the right column, and they
    also split the document into three regions that flow independently. each region gets
    its own leading, stretched or squeezed until it ends at the foot of its column, so
    there is no gap left underneath. the type sizes are never touched.
    an overlong region pushes a third page rather than quietly shifting the fixed blocks,
    so `pages == fit_pages` is what says the whole layout is still sound.
    `tolerance` is how close to the foot of the column counts as filled. leading only
    moves the text a whole line at a time, so asking for closer than one line box just
    makes the loop chase a gap it cannot close and run out of rounds instead.
    pass fit_pages=None to build once at the given scale and skip word altogether.
    `progress` is called as progress(step, total, message) after every build and every
    measurement, so a caller with a gui can show how far along the fitting is.
    """
    scales = {each: line_scale for each in makeBulletin.regions}
    #one build, then a measure/build pair per round. `rounds` is only an upper bound and
    #it usually settles in about four, so the bar is scaled to that and simply waits on
    #the last step if a month takes longer - better than crawling to a third of the way
    #and then jumping to the end
    expected_steps = 2 + 4*2
    done_steps = 0

    def _report(message, final=False):
        if progress!=None:
            progress(expected_steps if final else min(done_steps, expected_steps-1),
                     expected_steps, message)

    def _build():
        worker = makeBulletin(year, month, font_scale=font_scale, line_scales=dict(scales))
        worker.make_doc_in_one_go(content_file, doc_file)
        return worker.saved_path

    def _finish(path):
        #the .docx is the deliverable - it still gets a pass by hand before it goes out,
        #and the pdf is exported from word at that point
        _report('完成', final=True)
        return path

    _report('正在生成月报…')
    path = _build()
    done_steps = done_steps + 1
    if not fit_pages:
        return _finish(path)

    good, good_gap = None, None
    for round_no in range(rounds):
        _report(f'检查排版（第 {round_no+1} 轮）…')
        measured = measure_layout(path)
        done_steps = done_steps + 1
        if measured==None:
            #word is not available, so the document stays as it was built
            _report('完成', final=True)
            return path
        pages, ends = measured
        if pages<=fit_pages:
            #the round worth keeping is the one whose worst-placed region sits closest to
            #the foot of its column, not simply the last one that came in under the page
            #count - a later round can still fit and yet leave a wider gap than one before it
            gap = max(abs(ends[each]-COLUMN_BOTTOM) for each in scales)
            if good_gap==None or gap<good_gap:
                good, good_gap = dict(scales), gap
            if gap<=tolerance:
                return _finish(path)
            #room left over (or slightly too much): move each region's leading by the
            #ratio of the space it should span to the space it currently spans
            for region in scales:
                filled = (REGION_COLUMNS[region]-1)*COLUMN_HEIGHT + (ends[region]-COLUMN_TOP)
                wanted = REGION_COLUMNS[region]*COLUMN_HEIGHT
                if filled>0:
                    scales[region] = round(min(max_line_scale, max(min_line_scale,
                                                scales[region]*wanted/filled)), 3)
        elif good!=None:
            #the last change overshot into a third page - go back and take half of it
            for region in scales:
                scales[region] = round((scales[region]+good[region])/2, 3)
        else:
            #too long even at the starting leading, so tighten everything
            for region in scales:
                scales[region] = round(max(min_line_scale, scales[region]-0.05), 3)
        _report('正在调整行距…')
        path = _build()
        done_steps = done_steps + 1

    if good!=None and good!=scales:
        _report('正在还原最合适的行距…')
        scales.update(good)
        path = _build()
    return _finish(path)


emojs = ['🏠','🚉','🎁','📅''✝️','🕮','🌍','🏴󠁢󠁲󠁧󠁯󠁿','📍','👉','✬','♛','👨🏻‍🏫','✍🏽','🏛','💎','📝','📧','📙','📖','📃','✒️','🎦','🌐',\
         '➡️','💬','🤍','☞', '🏳️','⌨️','📪']
if __name__ == '__main__':
    worker = makeBulletin(2025, 1)
    worker.make_doc_in_one_go("C:\\Users\\qiucanro\\pygodAppData\\content_files\\bulletin_2025-1.txt")
    '''
    worker.add_monthly_scripture(contents=['只要你们行事为人与基督的福音相称，叫我或来见你们，或不在你们那里，可以听见你们的景况，知道你们同有一个心志，站立得稳，为所信的福音齐心努力。 腓立比书1:27 '])
    worker.add_spacing(line_spacing = 10)
    worker.test_add_monthly_service_table()
    worker.add_spacing(line_spacing = 10)
    worker.test_add_report()
    worker.add_spacing(line_spacing = 10)
    worker.test_add_last_month_record_table()
    worker.add_spacing(line_spacing = 10)
    worker.test_add_finance_table()
    worker.add_spacing(line_spacing = 10)
    worker.add_corresponding_table()
    worker.add_spacing(line_spacing = 10)
    worker.add_whatsapp_info_table()
    worker.add_spacing(line_spacing = 10)
    worker.add_header_info()
    worker.add_spacing(line_spacing = 10)
    worker.test_add_preach_table()
    worker.add_spacing(line_spacing = 10)
    worker.add_lesson_table()
    worker.add_spacing(line_spacing = 10)
    worker.add_meetup_info()
    worker.add_spacing(line_spacing = 10)
    worker.add_bank_info()
    worker.add_spacing(line_spacing = 10)
    worker.save_doc()
    '''