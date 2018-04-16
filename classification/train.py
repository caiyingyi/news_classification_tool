# -*- coding:utf-8 -*-
from pymongo import MongoClient
import logging
from gensim import corpora
from gensim.corpora import BleiCorpus
import gensim
from pre_process import PreProcess

"""
用途：从MongoDB中读取语料，进行预处理后，训练LDA模型
"""


class Dictionary(object):
    def __init__(self, cursor, dictionary_path):
        self.cursor = cursor
        self.dictionary_path = dictionary_path

    def build(self):
        self.cursor.rewind()
        dictionary = corpora.Dictionary(review["filter_data"] for review in self.cursor if review.get("filter_data"))
        dictionary.filter_extremes(keep_n=10000)
        dictionary.compactify()
        corpora.Dictionary.save(dictionary, self.dictionary_path)

        return dictionary


class Corpus(object):
    def __init__(self, cursor, reviews_dictionary, corpus_path):
        self.cursor = cursor
        self.reviews_dictionary = reviews_dictionary
        self.corpus_path = corpus_path

    def __iter__(self):
        self.cursor.rewind()
        for review in self.cursor:
            if review.get("filter_data"):
                yield self.reviews_dictionary.doc2bow(review["filter_data"])

    def serialize(self):
        BleiCorpus.serialize(self.corpus_path, self, id2word=self.reviews_dictionary)

        return self


class Train:
    def __init__(self):
        pass

    @staticmethod
    def run(lda_model_path, corpus_path, num_topics, id2word):
        corpus = corpora.BleiCorpus(corpus_path)
        lda = gensim.models.LdaModel(corpus, num_topics=num_topics, id2word=id2word)
        lda.save(lda_model_path)

        return lda


def main():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    dictionary_path = "models/dictionary.dict"
    corpus_path = "models/corpus.lda-c"
    lda_model_path = "models/lda_model.lda"

    # topics = ["World", "Sport", "Business", "Technology", "Lifestyle", "Health"]
    lda_num_topics = 6

    # 连接MongoDB
    corpus_collection = MongoClient("mongodb://39.108.180.114:27017")["ennews"][
        "news"]
    reviews_cursor = corpus_collection.find(no_cursor_timeout=True)

    # 数据预处理
    PreProcess(corpus_collection, reviews_cursor).data_filter()
    # 建立字典
    dictionary = Dictionary(reviews_cursor, dictionary_path).build()
    # Corpus建模
    Corpus(reviews_cursor, dictionary, corpus_path).serialize()
    reviews_cursor.close()
    # LDA建模
    lda_model = Train.run(lda_model_path, corpus_path, lda_num_topics, dictionary)

    lda_model.print_topics()


if __name__ == '__main__':
    main()