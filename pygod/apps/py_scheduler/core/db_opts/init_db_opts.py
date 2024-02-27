import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
from ..util import error_pop_up
from ...widgets.dialogues import LoginDialog, RegistrationDialog

db_config_file = Path(__file__).parent.parent.parent / 'config' / 'db_matching.yaml'
db_config_info = None
with open(db_config_file, 'r', encoding='utf8') as f:
    db_config_info = yaml.safe_load(f.read())

def set_db_config(self):
    self.db_config_info = db_config_info

def start_mongo_client_cloud(self):
    try:
        if not os.path.exists(str(Path(__file__).parent.parent.parent/ "resources" / "private" / "atlas_password.dot")):
            error_pop_up('You should create a file named atlas_password under Library_Manager/resources/private folder, \
                            where you save the atlas url link for your MongoDB atlas cloud account. \
                            please use the format ATLAS_URL="URL LINK"')
        else:
            env = load_dotenv(str(Path(__file__).parent.parent.parent/ "resources" / "private" / "atlas_password.dot"))
            if env:
                url = os.getenv('ATLAS_URL') 
                login_dialog(self, url)
                #self.mongo_client = MongoClient(url,tlsCAFile=certifi.where())
            else:
                url = ''
                print('something is wrong')
    except Exception as e:
        error_pop_up('Fail to start mongo client.'+'\n{}'.format(str(e)),'Error')

def register_new_user(self):
    try:
        if not os.path.exists(str(Path(__file__).parent.parent.parent/ "resources" / "private" / "atlas_password.dot")):
            error_pop_up('You should create a file named atlas_password under Library_Manager/resources/private folder, \
                            where you save the atlas url link for your MongoDB atlas cloud account. \
                            please use the format ATLAS_URL="URL LINK"')
        else:
            env = load_dotenv(str(Path(__file__).parent.parent.parent/ "resources" / "private" / "atlas_password.dot"))
            if env:
                url = os.getenv('ATLAS_URL') 
                register_dialog(self, url)
                #self.mongo_client = MongoClient(url,tlsCAFile=certifi.where())
            else:
                url = ''
                print('something is wrong')
    except Exception as e:
        error_pop_up('Fail to start mongo client for new user registration.'+'\n{}'.format(str(e)),'Error')

def login_dialog(self, url):
    dlg = LoginDialog(self, url)
    dlg.exec()

def logout(self):
    self.name = 'undefined'
    self.user_name = 'undefined'
    self.role = 'undefined'
    self.mongo_client = None
    self.database = None
    self.removeToolBar(self.toolBar)
    try:
        self.init_gui(self.ui)
        self.statusLabel.setText('Goodbye, you are logged out!')
    except:
        pass

def register_dialog(self, url):
    dlg = RegistrationDialog(self, url)
    dlg.exec()
