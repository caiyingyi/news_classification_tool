# -*- coding:utf-8 -*-
import re
from nltk.tokenize import word_tokenize
from nltk.stem.lancaster import LancasterStemmer

"""
用途：从MongoDB中读取待分类数据，对其进行预处理。包括：去html标签，分词，去停用词，去标点和词干化。将处理后的数据存储     进MongoDB对应的记录中。
传入参数：MongoDB数据库连接对象，游标对象
输出参数：无
"""


class PreProcess(object):
    def __init__(self, collection, cursor):
        self.collection = collection
        self.cursor = cursor
        # 读取去停词
        self.english_stopwords = []
        with open(r"F:\news_classification_tool\classification\stopwords.txt") as stopwords_file:
            for line in stopwords_file:
                self.english_stopwords.append(line.strip())

    def data_filter(self):
        self.cursor.rewind()
        for review in self.cursor:
            if review.get("filter_data"):
                continue
            else:
                data = review["content"]

                # 去除html标签
                re_cdata = re.compile('//<!\[CDATA\[[^>]*//\]\]>', re.I)  # 匹配CDATA
                re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)  # Script
                re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)  # style
                re_br = re.compile('<br\s*?/?>')  # 处理换行
                re_h = re.compile('</?\w+[^>]*>')  # HTML标签
                re_comment = re.compile('<!--[^>]*-->')  # HTML注释
                re_blank_line = re.compile('\n+')  # 去掉多余的空行
                re_charentity = re.compile(r'&#?(?P<name>\w+);')  # 去掉特殊字符

                s = re_cdata.sub('', data)  # 去掉CDATA
                s = re_script.sub('', s)  # 去掉SCRIPT
                s = re_style.sub('', s)  # 去掉style
                s = re_br.sub('', s)  # 去掉br
                s = re_h.sub('', s)  # 去掉HTML 标签
                s = re_comment.sub('', s)  # 去掉HTML注释
                s = re_blank_line.sub('\n', s)  # 去掉多余的空行
                s = re_charentity.sub("", s)  # 去掉特殊字符

                # nltk分词
                data = [word.lower() for word in word_tokenize(s)]
                # 去停词,去标点
                # english_stopwords = stopwords.words('english')
                english_punctuations = [',', '.', ':', ';', '?', '(', ')', '[', ']', '&', '!', '*', '@', '#', '$', '%',
                                        '-']
                data = [word for word in data if word not in self.english_stopwords + english_punctuations]
                # nltk 词干化
                st = LancasterStemmer()
                data = [st.stem(word) for word in data]

                # 插入数据库
                self.collection.update({"_id": review['_id']}, {"$set": {"filter_data": data}})
