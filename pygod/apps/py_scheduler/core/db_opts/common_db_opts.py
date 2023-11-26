from functools import partial
import pandas as pd
import io
from PyQt5.QtWidgets import QMessageBox,QAbstractItemView
from PyQt5.QtWidgets import QFileDialog
import codecs
from PIL import ImageGrab
from ..util import error_pop_up, image_string_to_qimage, image_to_64base_string, disable_all_tabs_but_one, PandasModel

def init_pandas_model_from_db_base(self, tab_indx, single_collection, contrains, onclicked_func, update_func = None, pandas_data = None, tab_widget_name = 'tabWidget_2', table_view_widget_name='tableView_book_info'):
    #disable_all_tabs_but_one(self, tab_widget_name, tab_indx)
    getattr(self, tab_widget_name).setCurrentIndex(tab_indx)
    if type(pandas_data)!=pd.DataFrame:
        data = create_pandas_data_from_db(self, db_type=self.database_type, single_collection= single_collection, constrains=contrains)
    else:
        data = pandas_data
    header_name_map = {}
    if len(data)!=0:
        header_name_map = list(self.db_config_info['db_types'][self.database_type]['table_viewer'].values())[0]
    self.pandas_model = PandasModel(data = data, tableviewer = getattr(self, table_view_widget_name), main_gui = self, column_names=header_name_map)
    #sort the table according to the first column
    try:#for some db, first column is bool checked values
        self.pandas_model.sort(0, False)
    except:
        pass
    if update_func!=None:
        self.pandas_model.dataChanged.connect(partial(update_func,self))
    getattr(self, table_view_widget_name).setModel(self.pandas_model)
    getattr(self, table_view_widget_name).resizeColumnsToContents()
    getattr(self, table_view_widget_name).setSelectionBehavior(QAbstractItemView.SelectRows)
    getattr(self, table_view_widget_name).horizontalHeader().setStretchLastSection(True)
    try:
        getattr(self, table_view_widget_name).clicked.disconnect()
    except:
        pass
    getattr(self, table_view_widget_name).clicked.connect(partial(onclicked_func,self))
    populate_search_field(self, )

def populate_search_field(self, field_comboBox_widget_name='comboBox_search_item'):
    name_map = list(self.db_config_info['db_types'][self.database_type]['table_viewer'].values())[0]
    fields = list(name_map.values())
    getattr(self, field_comboBox_widget_name).clear()
    getattr(self, field_comboBox_widget_name).addItems(fields)
    
def get_collection_list_from_yaml(self, db_type):
    return list(self.db_config_info['db_types'][db_type]['collections'].keys()) + \
           list(self.db_config_info['db_types']['share']['collections'].keys())

def get_document_info_from_yaml(self, db_type, collection):
    if collection in list(self.db_config_info['db_types']['share']['collections'].keys()):
        return self.db_config_info['db_types']['share']['collections'][collection]
    else:
        return self.db_config_info['db_types'][db_type]['collections'][collection]

def get_tableviewer_info_from_yaml(self, db_type, collection):
    if list(self.db_config_info['db_types'][db_type]['table_viewer'].keys()) == ['all_collections']:
        return self.db_config_info['db_types'][db_type]['table_viewer']['all_collections']
    else:
        return self.db_config_info['db_types'][db_type]['table_viewer'][collection]

def create_pandas_data_from_db(self, db_type = 'book', single_collection = True, constrains = [], limit = 50):
    """extact data from database and create a pandas dataframe to be used as table model input for table 
       viewer widget

    Args:
        db_type (str, optional): database type you specify in the yaml file. Defaults to 'book'.
        single_collection (bool, optional): extract data from single collection or not. Defaults to True.
        constrains (list, optional): in the case of multiple collections, you need to give the constrains to fielter out one record.
                                     eg. ['date','2023-09-03'], this constrain will extract the record in each collection where collection.date = '2032-09-03'
    """
    data = {}
    var_column_names = list(self.db_config_info['db_types'][db_type]['table_viewer'].values())[0]
    collections = list(self.db_config_info['db_types'][db_type]['table_viewer'].keys())
    assert len(collections)>=1, "no collection is provided in yaml"
    for key, value in var_column_names.items():
        data[key] = []
    if single_collection:
        # for each in self.database[collections[0]].find().limit(limit):
        for each in self.database[collections[0]].find():
            for each_key in data:
                data[each_key].append(each.get(each_key, 'NA'))
    else:
        assert len(constrains) == 2, "You need two item list for constrains in the mode."
        data = {}
        data['collections'] = []
        for key, value in var_column_names.items():
            data[key] = []
        if 'all_collections' in collections:
            collections = list(self.db_config_info['db_types'][db_type]['collections'].keys())
            excluded_collections = self.db_config_info['db_types'][db_type]['table_viewer']['excluded_collections']
            collections = [each for each in collections if each not in excluded_collections]
        else:
            pass
        for collection in collections:
            for each in self.database[collection].find():
            # for each in self.database[collection].find().limit(limit):
                #if constrains[0] not in each:
                #    break
                assert constrains[0] in each, 'The constrain key' + {constrains[0]} + 'is not found in the database'
                if each[constrains[0]] == constrains[1]:
                    for each_key in data:
                        if each_key!='collections':
                            data[each_key].append(each.get(each_key, 'NA'))
                    data['collections'].append(self.db_config_info['db_types'][db_type]['collections'][collection].get('map_name', collection))
                    break
    return pd.DataFrame(data)


#widget_view is qpageview.View instance widget
def open_image_file(self, widget_view):
    self.action.setView(widget_view)
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","image file (*.*)", options=options)
    if fileName:
        base64_data = image_to_64base_string(fileName)
        self.img_in_base64_format = base64_data
        img_format =  fileName.rsplit('.')[-1]
        #self.img_format = img_format
        widget_view.clear()
        widget_view.loadImages([image_string_to_qimage(base64_data, img_format = img_format)])
        widget_view.show()
        return img_format

#widget_view is qpageview.View instance widget
def paste_image_to_viewer_from_clipboard(self, widget_view, base64_string_var_name = 'base64_string_img'):
    self.action.setView(widget_view)
    # Pull image from clibpoard
    img = ImageGrab.grabclipboard()
    # Get raw bytes
    img_bytes = io.BytesIO()
    try:
        img.save(img_bytes, format='PNG')
        # Convert bytes to base64
        base64_data = codecs.encode(img_bytes.getvalue(), 'base64')
        setattr(self, base64_string_var_name, base64_data)
        #self.base64_string_temp = base64_data
        widget_view.clear()
        widget_view.loadImages([image_string_to_qimage(base64_data, img_format = 'PNG')])
        widget_view.show()
    except:
        error_pop_up('Fail to paste image from clipboard.','Error')
        return

def convert_clipboard_buffer_to_base64_string(self):
    # Pull image from clibpoard
    img = ImageGrab.grabclipboard()
    # Get raw bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    # Convert bytes to base64
    base64_data = codecs.encode(img_bytes.getvalue(), 'base64')
    return base64_data, 'PNG'

def load_img_from_base64(self, widget_view_name, base64_string, base64_string_var_name = 'base64_string_img'):
    setattr(self, base64_string_var_name, base64_string)
    qimage = image_string_to_qimage(base64_string, 'PNG')
    view = getattr(self, widget_view_name)
    view.clear()
    view.loadImages([qimage])
    view.show()

def extract_one_record(self, db_type, collection, constrain, cache = None, db = None):
    #specify the db name if you are not using the context database
    doc_info = get_document_info_from_yaml(self, db_type=db_type, collection = collection)
    if cache==None:
        if db!=None:
            data_from_db = self.mongo_client[db][collection].find_one(constrain)
        else:
            data_from_db = self.database[collection].find_one(constrain)
    else:
        data_from_db = cache
    NO_RECORD = False
    if data_from_db==None:
        NO_RECORD = True
        #error_pop_up('No data record can be found in the database!')
        #return False
    format_ = '{}'.format
    format_html = '<p style="color:white;margin:0px;font-size:18px">{}</p>'.format
    for doc, widget in doc_info.items():
        if doc == "map_name" or widget == 'None':
            continue
        else:
            cmd = None
            format_text = format_
            if widget.startswith('lineEdit'):
                cmd = 'Text'
                widget_set_api = eval(f'self.{widget}.set{cmd}')
            elif widget.startswith('comboBox'):
                cmd = 'CurrentText'
                widget_set_api = eval(f'self.{widget}.set{cmd}')
            elif widget.startswith('textEdit'):
                cmd = 'PlainText'
                widget_set_api = eval(f'self.{widget}.set{cmd}')
            else:
                widget_set_api = eval(f'self.set_data_for_{widget}')
                format_text = lambda x:x
            # print(format_text(str(data_from_db[doc])))
            if NO_RECORD:
                widget_set_api(format_text('NO RECORD!!!'))
            else:
                if doc not in data_from_db:
                    widget_set_api(format_text('0'))
                else:
                    widget_set_api(format_text(str(data_from_db[doc])))

    return not NO_RECORD

def delete_one_record(self, db_type, constrain, cbs = [], silent = False, msg = 'Are you sure to delete this paper?'):
    if not silent:
        reply = QMessageBox.question(self, 'Message', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            try:
                for collection in self.database.list_collection_names():
                    self.database[collection].delete_many(constrain)
                self.statusbar.clearMessage()
                self.statusbar.showMessage(f'The record {constrain} is deleted from DB successfully.')
                for cb in cbs:
                    cb(self)
            except Exception as e:
                error_pop_up('Failure to append paper info!\n{}'.format(str(e)),'Error') 
    else:
        try:
            for collection in self.database.list_collection_names():
                self.database[collection].delete_many(constrain)
            self.statusbar.clearMessage()
            self.statusbar.showMessage(f'The record {constrain} is deleted from DB successfully.')
            for cb in cbs:
                cb(self)
        except Exception as e:
            error_pop_up('Failure to append paper info!\n{}'.format(str(e)),'Error') 

def update_one_record(self, db_type, collection, constrain, extra_info = {}, cbs = [], silent = False):
    doc_info = get_document_info_from_yaml(self, db_type=db_type, collection = collection)
    data_from_client = {}
    data_from_db = self.database[collection].find_one(constrain)
    for doc, widget in doc_info.items():
        if doc == "map_name" or widget == 'None':
            continue
        else:
            cmd = None
            #note this way to distinguish float from str is not robust, developer need to stick to specific naming rules
            content_type = float
            if widget.endswith('note'):
                content_type = str
            if widget.startswith('lineEdit'):
                cmd = 'text'
                get_api_str = f'self.{widget}.{cmd}'
            elif widget.startswith('comboBox'):
                cmd = 'currentText'
                get_api_str = f'self.{widget}.{cmd}'
            elif widget.startswith('textEdit'):
                cmd = 'toPlainText'
                get_api_str = f'self.{widget}.{cmd}'
            else:
                get_api_str = f'self.get_data_for_{widget}'
            widget_get_api = eval(get_api_str)
            result = widget_get_api()
            if type(result)==bool:
                content_type = bool                
            data_from_client[doc] = content_type(result)
    data_from_client.update(extra_info)

    try:        
        if not silent:
            message = 'Would you like to update your database with new input?'
            reply = QMessageBox.question(self, 'Message', message, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                for key in data_from_db:
                    if key not in data_from_client and key!='_id':
                        data_from_client[key] = data_from_db[key]
                self.database[collection].replace_one(data_from_db, data_from_client)
                for cb in cbs:
                    cb(self)
                self.statusbar.clearMessage()
                self.statusbar.showMessage("'Update the record info successfully")
                return True
            else:
                return False
        else:
            for key in data_from_db:
                if key not in data_from_client and key!='_id':
                    data_from_client[key] = data_from_db[key]
            self.database[collection].replace_one(data_from_db, data_from_client)
            for cb in cbs:
                cb(self)
            self.statusbar.clearMessage()
            self.statusbar.showMessage("'Update the record info successfully")
    except Exception as e:
        self.statusbar.clearMessage()
        self.statusbar.showMessage("'Fail to update the record info!")
        error_pop_up('Fail to update record :-(\n{}'.format(str(e)),'Error')     
        return False


def add_one_record(self, db_type, collection, extra_info = {}, cbs = []):
    doc_info = get_document_info_from_yaml(self, db_type=db_type, collection = collection)
    data_from_client = {}
    for doc, widget in doc_info.items():
        if doc == "map_name" or widget == 'None':
            continue
        else:
            cmd = None
            #note this way to distinguish float from str is not robust, developer need to stick to specific naming rules
            content_type = float
            if widget.endswith('note'):
                content_type = str
            if widget.startswith('lineEdit'):
                cmd = 'text'
                get_api_str = f'self.{widget}.{cmd}'
            elif widget.startswith('comboBox'):
                cmd = 'currentText'
                get_api_str = f'self.{widget}.{cmd}'
            elif widget.startswith('textEdit'):
                cmd = 'toPlainText'
                get_api_str = f'self.{widget}.{cmd}'
            else:
                get_api_str = f'self.get_data_for_{widget}'
            widget_get_api = eval(get_api_str)
            result = widget_get_api()
            if type(result)==bool:
                content_type = bool
            data_from_client[doc] = content_type(result)            
    try:
        data_from_client.update(extra_info)
        self.database[collection].insert_one(data_from_client)
        self.statusbar.clearMessage()
        self.statusbar.showMessage(f'Append the {extra_info} sucessfully!')
        for cb in cbs:
            cb(self)
        return data_from_client
    except Exception as e:
        error_pop_up('Failure to append paper info!\n{}'.format(str(e)),'Error') 


def text_query_by_field(self, field, query_string, target_field, collection_name, database = None):
    """
    Args:
        field ([string]): in ['author','book_name','book_id','status','class']
        query_string ([string]): [the query string you want to perform, e.g. 1999 for field = 'year']
        target_filed([string]): the targeted filed you would like to extract, single string or a list of strings
        collection_name([string]): the collection name you would like to target

    Returns:
        [list]: [value list of target_field with specified collection_name]
    e.g.
    general_query_by_field(self, field='name', query_string='jackey', target_field='email', collection_name='user_info')
    means I would like to get a list of email for jackey in user_info collection in the current database
    """
    if database == None:
        database = self.database
    index_key = (database.name, collection_name, field)
    if index_key not in self.index_names:
        index_name = database[collection_name].create_index([(field,'text')])
        self.index_names[index_key] = index_name
    targets = database[collection_name].find({"$text": {"$search": "\"{}\"".format(query_string)}})
    # print([each for each in targets])
    #drop the index afterwards
    if type(target_field)==list:
        return_list = []
        for field in target_field:
            targets = database[collection_name].find({"$text": {"$search": "\"{}\"".format(query_string)}})
            #print(field)
            return_list.append([each[field] for each in targets])
    else:
        return_list = [each[target_field] for each in targets]
    # self.database.paper_info.drop_index(index_name)
    #database[collection_name].drop_index(index_name)
    return return_list  

#eg name == 'jackey' and birth_year== '1983'
#logical_opt = 'and'
#field_values_cases = [{'name': 'jackey'},{'birth_year': '1983'}]
def logical_query_within_two_fields(self, collection, logical_opt, field_value_cases, return_fields = None):
    assert type(field_value_cases)==list and len(field_value_cases)>1, "field_value_cases should be a list of dictionary"
    if return_fields==None:
        return self.database[collection].find({
            f"${logical_opt}":field_value_cases
        })
    else:
        return self.database[collection].find({
            f"${logical_opt}":field_value_cases
        }, dict(zip(return_fields,[1]*len(return_fields))))
    
#eg year > 1983
#logical_opt = 'gt', field = 'year', limit = 1983
def logical_query_one_field(self, collection, logical_opt, field, limit, return_fields = None):
    if return_fields==None:
        return self.database[collection].find({field:
            {f"${logical_opt}": limit}
        })
    else:
        return self.database[collection].find({field:
            {f"${logical_opt}":limit}
        }, dict(zip(return_fields,[1]*len(return_fields))))
    
#eg year > 1983 and year <2000
#logical_opts= ['gt','lt'], limits = [1983, 2000], field = 'year'
def logical_range_query_one_field(self, collection, logical_opts, field, limits, return_fields = None):
    assert len(logical_opts)==len(limits), "operators and limits should be of a same number!"
    if return_fields==None:
        return self.database[collection].find({"$and":
            [
            {field: {f"${logical_opts[i]}": limits[i]}}
            for i in range(len(limits))
            ]
        })
    else:
        return self.database[collection].find({"$and":
            [
            {field: {f"${logical_opts[i]}": limits[i]}}
            for i in range(len(limits))
            ]
        }, dict(zip(return_fields,[1]*len(return_fields))))