from setuptools import setup, find_packages
setup(
    name = 'pygod',
    version = '0.1.0',
    description = 'mangoDB and PyQt5 project for scheduling event for a Church',
    author = 'Jackey Qiu',
    author_email = 'canrong.qiu@desy.de',
    url = 'https://github.com/jackey-qiu/pyworkship',
    classifiers = ['Topic::pyqt5 application', 'Programming Language::Python'],
    license = 'MIT',
    install_requires = ['PyQt5', 'pyqtgraph', 'qpageview', 'pyqtchart', 'qdarkstyle', 'numpy', 'pymongo', 'bcrypt','python-dotenv', 'pandas', 'dnspython', 'click', 'python-pptx', 'jieba', 'whoosh','yt-dlp','pyyaml'],
    packages = find_packages(),
    package_data = {'pygod.apps.bible_reader.src': ['bible_interpret/*/*', 'bibles_json/*', 'icons/*', 'notes/*', 'ui/*'], 
                    'pygod.apps.ppt_worker': ['src/bible/*'], 
                    'pygod.apps.ppt_worker.src.bkg_slides': ['holy_dinner_option1/*', 'holy_dinner_option2/*', 'others/*'], 
                    'pygod.apps.py_scheduler.resources': ['icons/*', 'private/*', 'stylesheets/*'], 
                    'pygod.apps.py_scheduler': ['ui/*.ui','config/*.yaml'],
                    'pygod.src':['*.ico']},
    scripts = [],
     entry_points = {
         'console_scripts' : [
             'ccg = pygod.bin.app_dispatcher:dispatcher',
         ],
     }
)
