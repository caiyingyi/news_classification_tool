# -*- coding:utf-8 -*-
from pre_process import PreProcess
import logging
from pymongo import MongoClient
from gensim.models import LdaModel
from gensim import corpora

"""
用途：从MongoDB数据库中读取待分类数据，进行预处理，通过LDA模型，得到所属类别。将类别存储进MongoDB数据库对应记录中。
"""


class Classify(object):
    def __init__(self, collection, cursor):
        self.collection = collection
        self.cursor = cursor
        dictionary_path = "models2/dictionary.dict"
        lda_model_path = "models2/lda_model.lda"
        self.dictionary = corpora.Dictionary.load(dictionary_path)
        self.lda = LdaModel.load(lda_model_path)

    def run(self):
        self.cursor.rewind()
        for review in self.cursor:
            if review.get("filter_data"):
                data = review["filter_data"]
                data_dictionary = self.dictionary.doc2bow(data)
                categories_list = self.lda[data_dictionary]

                # print categories_list
                categories_list.sort(key=lambda x: x[1], reverse=True)
                categories = categories_list[0][0]

                # 插入数据库
                self.collection.update({"_id": review['_id']}, {"$set": {"categories": categories}})


def main():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # 连接MongoDB，读取待分类数据
    corpus_collection = MongoClient("mongodb://localhost:27017")["ennews"][
        "upi"]
    reviews_cursor = corpus_collection.find(no_cursor_timeout=True)

    # 数据预处理
    PreProcess(corpus_collection, reviews_cursor).data_filter()

    # 分类
    classify = Classify(corpus_collection, reviews_cursor)
    classify.run()

    reviews_cursor.close()


if __name__ == '__main__':
    main()