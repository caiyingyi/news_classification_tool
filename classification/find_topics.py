# -*- coding:utf-8 -*-

import logging
from pymongo import MongoClient
from gensim.models import LdaModel
from gensim import corpora
import sys

"""
用途：从MongoDB数据库中读取训练数据，通过LDA模型，得到所属类别。将类别存储进MongoDB数据库对应记录中。统计出topic和category对应关系
"""


class FindTopics(object):
    def __init__(self, collection, cursor):
        self.collection = collection
        self.cursor = cursor
        dictionary_path = "models/dictionary.dict"
        lda_model_path = "models/lda_model.lda"
        self.dictionary = corpora.Dictionary.load(dictionary_path)
        self.lda = LdaModel.load(lda_model_path)
        self.topics = {"World": 0, "Sport": 2, "Business": 1, "Technology": 3, "Lifestyle": 4, "Health": 5}

    def run(self):
        topics_matrix = [[0] * 6 for i in range(6)]
        self.cursor.rewind()
        for review in self.cursor:
            if review.get("filter_data"):
                data = review["filter_data"]
                topic = review['topic']

                data_dictionary = self.dictionary.doc2bow(data)
                categories_list = self.lda[data_dictionary]

                # print categories_list
                categories_list.sort(key=lambda x: x[1], reverse=True)
                categories = categories_list[0][0]

                # 计算主题矩阵
                topics_matrix[self.topics[topic]][categories] += 1

                # 插入数据库
                self.collection.update({"_id": review['_id']}, {"$set": {"categories": categories}})
        return topics_matrix


def main():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # 连接MongoDB，读取待分类数据
    corpus_collection = MongoClient("mongodb://39.108.180.114:27017")["ennews"][
        "news"]
    reviews_cursor = corpus_collection.find(no_cursor_timeout=True)

    # 分类
    find_topics = FindTopics(corpus_collection, reviews_cursor)
    topics_matrix = find_topics.run()

    # 输出主题矩阵
    # make a copy of original stdout route
    stdout_backup = sys.stdout
    # define the log file that receives your log info
    log_file = open(".\lda_topics.log", "w")
    # redirect print output to log file
    sys.stdout = log_file
    print(str(topics_matrix))
    log_file.close()
    # restore the output to initial pattern
    sys.stdout = stdout_backup

    reviews_cursor.close()


if __name__ == '__main__':
    main()
