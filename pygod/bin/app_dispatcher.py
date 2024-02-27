import click, sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))
from pygod.apps.ppt_worker.scripts.ppt_worker import ppt
from pygod.apps.bible_reader.scripts.bible_reader_gui import reader
from pygod.apps.py_scheduler.bin.manager_gui import scheduler

@click.group()
def dispatcher():
    pass

dispatcher.add_command(ppt)
dispatcher.add_command(reader)
dispatcher.add_command(scheduler)

if __name__=='__main__':
    '''use guide
    1. launch ppt worker: python app_dispatcher.py ppt 2023-09-03 2 or cgg ppt 2023-09-03 2 once installed
    2. launch bible reader: python add_dispatcher.py reader or cgg reader once installed
    3. launch database app: python add_dispatcher.py scheduler or cgg scheduler once installed
    '''
    dispatcher()