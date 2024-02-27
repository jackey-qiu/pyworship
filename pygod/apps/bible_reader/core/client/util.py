book_corr_lib={"路":"Luke",
               "书":"Joshua",
               "赛":"Isaiah",
               "箴言":"Proverbs",
               "帖前":"1_Thessalonians",
               "帖后":"1_Thessalonians",
               "诗篇":"Psalm",
               "耶":"Jeremiah",
               "约":"John",
               "来":"Hebrews",
               "哀":"Lamentations",
               "结":"Ezekiel",
               "雅":"James",
               "彼前":"1_Peter",
               "彼后":"2_Peter",
               "约一":"1_John",
               "约二":"2_John",
               "约三":"3_John",
               "犹":"Jude",
               "何":"Hosea",
               "提多书":"Titus",
               "珥":"Joel",
               "摩":"Amos",
               "俄":"Obadiah",
               "启":"Revelation",
               "拿":"Jonah",
               "弥":"Micah",
               "鸿":"Nahum",
               "哈":"Habakkuk",
               "番":"Zephaniah",
               "该":"Haggai",
               "亚":"Zechariah",
               "玛":"Malachi",
               "但":"Daniel",
               "传道书":"Ecclesiastes",
               "提前":"1_Timothy",
               "提后":"2_Timothy",
               "雅歌":"Song_of_Songs",
               "腓利门书":"Philemon",
               "创":"Genesis",
               "太":"Matthew"}
#collection of (chaper,verse) of Book Proverbs to be shown underneath the message reminder each day!
chapter_verse_proverbs=[(1,7),(1,20),(1,33),(2,2),(2,6),(2,10),(2,20),(2,21),(3,5),(3,7),(3,13),(3,19),(3,27),(3,35),\
                        (4,8),(4,13),(8,12),(9,9),(9,10),(11,19),(11,25),(11,30),(12,25),(15,1),(15,4),(15,13),(15,23),\
                        (15,30),(15,30),(15,33),(16,9),(16,16),(16,20)]

def alignment(str1, space, align = 'left'):
    length = len(str1.encode('gb2312'))
    space = space - length if space >=length else 0
    if align == 'left':
        str1 = str1 + ' ' * space
    elif align == 'right':
        str1 = ' '* space +str1
    elif align == 'center':
        str1 = ' ' * (space //2) +str1 + ' '* (space - space // 2)
    return str1