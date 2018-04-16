# -*- coding:utf-8 -*-
"""
用途：评估分类器的精度
传入参数：数据库连接corpus_collection，数据库游标reviews_cursor，主题数目lda_num_topics，主题字典topics
         topics = {"World":0,"Sport":1,"Business":2,"Technology":3,"Lifestyle":4,"Health":5}
输出：各主题f1的均值
用法：average_evaluation = Evaluate(corpus_collection, reviews_cursor, lda_num_topics, topics).calculate()
"""
from pymongo import MongoClient
import logging


class Evaluate(object):
    def __init__(self, corpus_collection, reviews_cursor, lda_num_topics, topics):
        self.collection = corpus_collection
        self.cursor = reviews_cursor
        self.topics_num = lda_num_topics
        self.topics = topics

    def confusion_matrix(self):
        matrix = [[0] * self.topics_num for i in range(self.topics_num)]
        self.cursor.rewind()
        for review in self.cursor:
            if review.get("categories") and review.get("topic"):
                matrix[review.get("categories")][self.topics[review.get("topic")]] += 1.0

        print("混淆矩阵：")
        print(str(matrix))

        return matrix

    def calculate(self):
        matrix = self.confusion_matrix()
        evaluation = {}
        total_f1 = 0
        for i in range(self.topics_num):
            precision = matrix[i][i] / sum(matrix[i])
            recall = matrix[i][i] / sum(matrix[n][i] for n in range(self.topics_num))
            f1 = (2 * precision * recall) / (precision + recall)

            total_f1 = total_f1 + f1
            evaluation[i] = {"precision": precision, "recall": recall, "f1": f1}

        print("各主题的精确率，召回率和f1：")
        print str(evaluation)

        average_evaluation = total_f1 / self.topics_num
        print("该分类器的精度：" + str(average_evaluation))

        return average_evaluation


def main():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    # 主题
    lda_num_topics = 6
    topics = {"World": 1, "Sport": 4, "Business": 0, "Technology": 5, "Lifestyle": 2, "Health": 3}

    # 连接MongoDB
    corpus_collection = MongoClient("mongodb://39.108.180.114:27017")["ennews"][
        "testing"]
    reviews_cursor = corpus_collection.find(no_cursor_timeout=True)

    evaluate = Evaluate(corpus_collection, reviews_cursor, lda_num_topics, topics).calculate()
    reviews_cursor.close()


if __name__ == "__main__":
    main()
