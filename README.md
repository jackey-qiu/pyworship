# 该代码用于制作汉堡华人基督教会主日崇拜ppt
## python环境
- python3.7+
- 依赖包 python-pptx
## 代码运行步骤
1. 编辑内容文本，在content文件夹里。将里面每个TXT文件的文件名进行相应的修改，只需要更改每个文件的日期后缀，格式为年-月-日，比如2023-08-20，文件名前缀不可以更改。比如pray_list_2023-08-16.txt中的前缀pray_list_不可以修改，否则程序会出错。每个文本的内容需要遵循一定的格式，请打开每个实例文件看看内容排序的格式，应该很好理解的。
- pray_list_xxxx-xx-xx.txt: 祷告事项
- preach_list_xxxx-xx-xx.txt: 证道内容
- song_list_xxxx-xx-xx.txt: 诗歌敬拜（前三首）+回应诗歌（最后一首）
- scripture_list_xxxx-xx-xx.txt:经文列表（第一部分是宣召，第二是启应经文，第三是读经）
- report_list_xxxx-xx-xx.txt:报告列表
- worker_list_xxxx-xx-xx.txt:服事人员列表（第一部分是当前服事人员，第二部分是下周服事人员）
2. 运行主程序文件`python ppt_worker.py`. 程序启动前你需要提供日期，格式和前面的文件日期后缀是一样的，
3. 程序检查必须得文本文件是否已经存在，如果存在，程序启动，否则报告缺失的文件，程序终止运行。用户新建缺失文件后，重新运行程序。
3. 如果程序运行成功，生成的ppt文件保存在pyworkship文件夹里
## 注意
生成的pptx文件需要进行一些小修改，在祷告事项以及证道幻灯片中的numbered list需要重新设置。所有的animation需要重新添加。还有一些标题可能需要小修。
