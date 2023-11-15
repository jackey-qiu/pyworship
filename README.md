# To use this app
1. download the source code
2. cd to the root folder
3. install the package with the cmd: pip install .
4. once through the installation, use one of the entrypoints to launch one app: ccg --help
eg. ccg reader, ccg scheduler. You will need users login credential to login ccg atlas MangoDB.
# how to build exe file
1. cd to the folder pygod/bin, where you should see the ccg.py entry script and the created ccg.spec file
2. run from terminal: `pyinstaller ccg.spec`
3. Now inside the bin folder you will see dist folder, go there and locate the ccg folder
4. There is one package still missing in the folder, which is pptx
5. You need to manually copy the pptx (in the system-reconized python site-package folder) to this folder. Without this step, the ppt worker will not work.
6. Then you can archive this whole folder down to ccg.zip and send it around to other users.
7. People receiving this zip file, just unzip the file and run the ccg.exe file in the ccg folder.

# executable file
1. download from https://1drv.ms/u/s!AijhQio6-ElysF2IATfWSNq6qXQc?e=ffrFhu (for windowOS) or from https://1drv.ms/u/s!AijhQio6-ElysF7gsJA7Wf0s0O0z?e=Ndo6MQ (for MacOS)
2. cd to the root folder after decompressing the file
3. double click ccg.exe (windowOS) or ccg (MacOS)
4. You should be able to see the client interface of MongoDB Atlas database
5. To use it, login first to connect to Atlas cloud. Just clik the first icon (cloud-like) from the toolbar.
6. Provide you login name and password. If you don't have it, you can register by clicking the second icon. Input the info and submit it. The admin will grant you to the Atlas database access with proper rights. You need to wait for a few days depending on how fast the admin can proccess your case.
7. Once you are loggined to the Atlas cloud, you will see a list of databases in the list, which you are allowed to view/edit.
8. You need to pick one database to continue.
  - ccg-PPT: database for ppt worker. Use it if you would like to work on ppt slides for workship.
  - ccg-task: database for scheduling workship service for brothers and sisters. Use it when you want to schedule worship service.
  - ccg-finance: finance of our church.
  - ccg-bulletin: database for bulletin creator.
   
