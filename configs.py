import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='trending topic of microblog')

    # 热搜网址
    parser.add_argument('--url', default='https://s.weibo.com/top/summary?Refer=top_hot&topnav=1&wvr=6')

    # 全部内容 or 特定内容
    """
    flag: True or False,是否爬取微博所有的内容
    index: 爬取特定热搜,例如第2个热搜内容: ***， 则index = 2,便会直接爬取该热搜信息
    str_time: 当前时间, such as 2021-01-11_1551
    """
    parser.add_argument('--flag', default=True)
    parser.add_argument('--index', default=6)
    parser.add_argument('--str_time', default='2021-01-11_1746')

    return parser.parse_args()