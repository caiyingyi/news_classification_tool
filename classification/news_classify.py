# -*- coding:utf-8 -*-
from news_pre_process import NewsPreProcess
import logging
from pymongo import MongoClient
from gensim.models import LdaModel
from gensim import corpora

"""
用途：从MongoDB数据库中读取待分类数据：topic为空且filter_date不为空
      进行预处理，通过LDA模型，得到所属类别。将类别存储进MongoDB数据库对应记录中。
"""


class NewsClassify(object):
    def __init__(self, collection, cursor):
        self.collection = collection
        self.cursor = cursor
        dictionary_path = "models2/dictionary.dict"
        lda_model_path = "models2/lda_model.lda"
        self.dictionary = corpora.Dictionary.load(dictionary_path)
        self.lda = LdaModel.load(lda_model_path)
        self.topic_dic = {1: "World", 4: "Sport", 0: "Business", 5: "Technology", 2: "Lifestyle", 3: "Health"}

    def run(self):
        self.cursor.rewind()
        for review in self.cursor:
            if review.get("topic"):
                continue
            if review.get("filter_data"):
                data = review["filter_data"]
                data_dictionary = self.dictionary.doc2bow(data)
                categories_list = self.lda[data_dictionary]

                # print categories_list
                categories_list.sort(key=lambda x: x[1], reverse=True)
                categories = categories_list[0][0]
                topic = self.topic_dic[categories]

                # 插入数据库
                self.collection.update({"_id": review['_id']}, {"$set": {"categories": categories, "topic": topic}})


def main():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # 连接MongoDB，读取待分类数据
    corpus_collection = MongoClient("mongodb://39.108.180.114:27017")["ennews"][
        "news"]
    reviews_cursor = corpus_collection.find(no_cursor_timeout=True)

    # 数据预处理
    NewsPreProcess(corpus_collection, reviews_cursor).data_filter()

    # 分类
    classify = NewsClassify(corpus_collection, reviews_cursor)
    classify.run()

    reviews_cursor.close()


if __name__ == '__main__':
    main()
