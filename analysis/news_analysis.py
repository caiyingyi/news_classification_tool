# -*- coding:utf-8 -*-

from pymongo import MongoClient
import time
import datetime
import pandas as pd


class NewsAnalysis(object):
    def __init__(self, cursor, line_chart_path, pie_chart_path, bar_chart_path):
        self.cursor = cursor
        self.line_chart_path = line_chart_path
        self.pie_chart_path = pie_chart_path
        self.bar_chart_path = bar_chart_path
        self.topic_dic = {"World": 1, "Sport": 4, "Business": 0, "Technology": 5, "Lifestyle": 2, "Health": 3}

    def run(self):
        line_chart = [[0] * 7 for i in range(7)]
        pie_chart = [[0] * 2 for i in range(6)]
        bar_chart = [[0] * 2 for i in range(6)]

        # 导出line_chart
        date_dic = {}
        for i in range(6, -1, -1):
            ago = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            line_chart[6 - i][6] = ago
            date_dic[ago] = 6 - i

        self.cursor.rewind()
        for review in self.cursor:
            try:
                published_at = time.strftime("%Y-%m-%d", time.localtime(review.get("published_at")))
                topic = review.get("topic")
                line_chart[date_dic[published_at]][self.topic_dic[topic]] += 1
            except:
                continue

        print(str(line_chart))
        topic_name = ["Business", "World", "Lifestyle", "Health", "Sport", "Technology", "Date"]
        pd.DataFrame(columns=topic_name, data=line_chart).to_csv(self.line_chart_path)

        # 导出pie_chart
        total = list(zip(*line_chart))
        for index, value in enumerate(total):
            if index < 6:
                pie_chart[index][1] = sum(value)
                pie_chart[index][0] = topic_name[index]

        print(str(pie_chart))
        name = ["topic", "total"]
        pd.DataFrame(columns=name, data=pie_chart).to_csv(self.pie_chart_path)

        # 导出bar_chart
        for index, value in enumerate(line_chart[6]):
            if index < 6:
                bar_chart[index][1] = value
                bar_chart[index][0] = topic_name[index]
        print(str(bar_chart))
        name = ["topic", "today"]
        pd.DataFrame(columns=name, data=bar_chart).to_csv(self.bar_chart_path)


def main():
    line_chart_path = "charts/line_chart.csv"
    pie_chart_path = "charts/pie_chart.csv"
    bar_chart_path = "charts/bar_chart.csv"

    # 连接MongoDB
    corpus_collection = MongoClient("mongodb://39.108.180.114:27017")["ennews"][
        "news"]
    reviews_cursor = corpus_collection.find(no_cursor_timeout=True)

    NewsAnalysis(reviews_cursor, line_chart_path, pie_chart_path, bar_chart_path).run()

    reviews_cursor.close()


if __name__ == '__main__':
    main()
