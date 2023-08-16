# 该代码用于制作汉堡华人基督教会主日崇拜ppt
## python环境
- python3.7+
- 依赖包 python-pptx
## 代码运行步骤
1. 编辑内容文本，在content文件夹里。将里面每个TXT文件的文件名进行相应的修改，只需要更改每个文件的日期后缀，格式为月-日-年，比如08-20-2023，文件名前缀不可以更改。比如pray_list_08-16-2023.txt中的前缀pray_list_不可以修改，否则程序会出错。每个文本的内容需要遵循一定的格式，请打开每个实例文件看看内容排序的格式，应该很好理解的。
- pray_list_xx-xx-xxxx.txt: 祷告事项
- preach_list_xx-xx-xxxx.txt: 证道内容
- song_list_xx-xx-xxxx.txt: 诗歌敬拜（前三首）+回应诗歌（最后一首）
- scripture_list_xx-xx-xxxx.txt:经文列表（第一部分是宣召，第二是启应经文，第三是读经）
- report_list_xx-xx-xxxx.txt:报告列表
- worker_list_xx-xx-xxxx.txt:服事人员列表（第一部分是当前服事人员，第二部分是下周服事人员）
2.  打开主程序文件ppt_worker.py，往下拉到倒数第四行，修改敬拜时间，和前面的文本文件名的日期后缀是不一样的格式，区别是年在前面，比如 date = '2023-08-20'
3.  运行主程序文件`python ppt_worker.py`. 生成的ppt文件保存在pyworkship文件夹里
## 注意
生成的pptx文件需要进行一些小修改，在祷告事项以及证道幻灯片中的numbered list需要重新设置。所有的animation需要重新添加。还有一些标题可能需要小修。
