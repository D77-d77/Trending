import os
import re
import sys
import random
import requests
import traceback

from tqdm import tqdm
from time import sleep
from lxml import etree
from collections import OrderedDict
from datetime import datetime, timedelta

"""
start(): 执行爬虫
all_MicroBlog_content(): 爬取所有热搜的内容
one_Microblog_content(): 爬取一个热搜的内容
rank_list(): 获取热搜排行榜
hot_search_url(): 热搜网址
head(): 获取热搜话题、阅读量、讨论量、导语
get_one_page(): 获取一页的内容
is_original(): 判断是否为原创微博
original_content(): 获取原创微博的内容
retweet_content(): 获取转发微博的内容
write_txt(): 将爬取的信息写入txt文件
deal_html(): 处理html
deal_garbled(): 处理乱码
"""
class MicroBlog(object):
    def __init__(self, url, flag, index, str_time):
        """
        :param url: 热搜网址
        :param topic: 话题
        :param urls_list: 热搜话题的网址
        :param MicroBlog: 热搜微博内容
        :param time: 当前时间
        :param index: 爬取特定热搜,例如第2个热搜内容: ***， 则index = 2,便会直接爬取该热搜信息
        :param flag: True or False,是否爬取微博所有的内容
        :param str_time: 当前时间, 2021-01-07_1600
        :param txt_name: txt文件名称, 20新能源
        """
        self.url = url
        self.topic = {}
        self.urls_list = list()
        self.MicroBlog = dict()
        self.time = ''
        self.index = index
        self.flag = flag
        self.str_time = str_time
        self.txt_name = []

    def start(self):
        # 爬取所有热搜的信息内容
        if self.flag:
            self.all_MicroBlog_content(self.url)
        # 爬取某个热搜的内容
        else:
            # 文件的路径
            dir = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'information' + os.sep + self.str_time + os.sep + 'topic.txt'
            if not dir:
                sys.exit(u'该文件不存在！')
            else:
                file = open(dir, 'rb')
                # 因为第一行是时间，因此直接跳过
                line = file.readline()
                line = file.readline()
                while line:
                    if b'https' in line:
                        self.urls_list.append(line)
                    line = file.readline()

                # 获取txt文件名
                file_dir = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'information'
                for root, dirs, files in os.walk(file_dir):
                    if self.str_time in root:
                        self.txt_name = files

                # 爬取第index页的微博内容
                self.MicroBlog = self.one_Microblog_content(self.urls_list[self.index])

                # 存储第index页的内容
                if self.index == 0:
                    tmp_dir = file_dir + os.sep + self.str_time + os.sep + self.txt_name[-2]
                else:
                    tmp_dir = file_dir + os.sep + self.str_time + os.sep + self.txt_name[self.index - 1]
                with open(tmp_dir, 'ab') as f:
                    f.write((u'话题: ' + self.MicroBlog['title'] + '\n' +
                             u'阅读量: ' + self.MicroBlog['read'] + '\n' +
                             u'讨论量: ' + self.MicroBlog['discussion'] + '\n').encode(sys.stdout.encoding))
                    f.write(('*' * 150).encode(sys.stdout.encoding))

                    content = self.MicroBlog['content']
                    for i in range(len(content)):
                        f.write(('\n' + u'用户名: ' + content[i]['name'] + '\n' +
                                 u'微博内容: ' + content[i]['content'] + '\n' +
                                 u'发布时间: ' + content[i]['publish_time'] + '\n' + '-' * 150).encode(sys.stdout.encoding))
                    f.write(('-' * 150 + '\n').encode(sys.stdout.encoding))
                f.close()

    def all_MicroBlog_content(self, url):
        try:
            flag = True
            # 当前时间
            self.time = datetime.now().strftime('%Y-%m-%d_%H%M')

            # 获取热搜标题
            self.topic = self.rank_list(url)

            # 获取热搜网址
            self.urls_list = self.hot_search_url(url)
            # print(self.urls_list)

            # 将热搜话题写入文件
            self.write_txt('topic', flag, 0)

            # 按照话题进行信息的爬取
            index, random_index = 0, random.randint(1, 5)
            for i in tqdm(range(len(self.urls_list)), desc=u'进度'):
                self.MicroBlog = self.one_Microblog_content(self.urls_list[i])
                print("-" * 150)

                # 每爬取一个话题写入一次文件
                if i == 0:
                    self.write_txt('top', flag, i)
                else:
                    self.write_txt('content', flag, i)

                # 随机等待避免被限制
                if i - index == random_index - 1:
                    sleep(random.randint(6, 10))
                    index = i
                    random_index = random.randint(1, 5)

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def one_Microblog_content(self, url):
        try:
            """
            MicroBlog: 存储微博热搜的内容
            MicroBlog['title']: 微博热搜标题, 例如: 美国将要求英国入境旅客持新冠阴性证明
            MicroBlog['read']: 话题阅读量, 例如: 阅读量: 阅读4715.6万 
            MicroBlog['discussion']: 话题讨论量, 例如: 讨论1509
            Microblog['topic']: 话题导语, 例如: 美国疾控中心（CDC）当日发表声明称，美国将开始要求来自英国的旅客提交新冠病毒检测阴性证明。
            Microblog['content']: 微博热搜内容。包括(用户名 + 内容 + 时间)
            """
            selector = self.deal_html(url)

            Microblog = OrderedDict()
            head_content = self.head(selector)
            Microblog['title'] = head_content['title']
            Microblog['read'] = head_content['read']
            Microblog['discussion'] = head_content['discussion']
            Microblog['topic'] = head_content['topic']
            Microblog['content'] = self.get_one_page(selector)

            return Microblog
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def rank_list(self, url):
        try:
            """
            rank: 热搜标号 1, 2, 3, ..., 50
            affair: 热搜标题 中国新冠病毒疫苗上市, 于正向琼瑶道歉...
            view: 浏览数量 5360426, 3642172...
            """
            html = self.deal_html(url)
            rank = html.xpath('//td[@class="td-01 ranktop"]/text()')
            affair = html.xpath('//td[@class="td-02"]/a/text()')
            view = html.xpath('//td[@class="td-02"]/span/text()')
            print('*' * 150)
            print('top:  {}'.format(affair[0]))
            for i in range(len(rank)):
                print('{}: '.format(i + 1).rjust(5), affair[i + 1].ljust(5), view[i])

            self.topic['affair'] = affair
            self.topic['view'] = view
            print('*' * 150)
            return self.topic
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def hot_search_url(self, url):
        try:
            html = self.deal_html(url)
            link = html.xpath("//td[@class='td-02']/a")
            for i in range(len(link)):
                tmp = link[i].attrib['href']
                if tmp == 'javascript:void(0);':
                    tmp = link[i].attrib['href_to']
                tmp = 'https://s.weibo.com' + tmp
                self.urls_list.append(tmp)
                # print(urls)
            return self.urls_list
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def head(self, selector):
        try:
            head = dict()
            # 话题: 美国将要求英国入境旅客持新冠阴性证明
            title = selector.xpath("//div[@class='search-input']/input")[0]
            title = title.attrib['value']
            # print(title)
            head['title'] = title
            print('热搜话题: {}'.format(title))

            # 阅读量、讨论量: 阅读4715.6万 讨论1509
            total = selector.xpath("//div[@class='total']/span/text()")
            n = len(total)
            if not n:
                read, discussion = 0, 0
            elif n == 1:
                read, discussion = total[0], 0
            else:
                read = total[0]
                discussion = total[1]
            # print(read, discussion)
            head['read'] = str(read)
            head['discussion'] = str(discussion)
            print('阅读量: {}'.format(read), '讨论量: {}'.format(discussion))

            # 话题导语: 美国疾控中心（CDC）当日发表声明称，美国将开始要求来自英国的旅客提交新冠病毒检测阴性证明。
            topic = selector.xpath("//div[@class='card card-topic-lead s-pg16']/p/strong")
            if not topic:
                topic = '无'
            else:
                topic = topic[0].tail
            # print(topic)
            head['topic'] = topic
            print('导语: {}'.format(topic))
            return head
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_one_page(self, selector):
        try:
            info = selector.xpath("//div[@class='content']")
            n = len(info)
            Microblog = []

            for i in range(n):
                information = dict()
                microblog = info[i]

                if not microblog.xpath("div[@class='info']"):
                    continue

                # 用户名 nickname
                name = microblog.xpath("div[@class='info']//a[@class='name']")
                if not name:
                    name = 'None'
                else:
                    name = name[0].text
                information['name'] = name
                print('用户: {}'.format(name))

                # 微博内容: 原创微博/转发微博
                content = self.original_content(microblog) if self.is_original(microblog) else self.retweet_content(microblog)
                information['content'] = content
                print('微博内容: {}'.format(content))

                # 发布时间
                time = microblog.xpath("p[@class='from']")[0]
                time = self.deal_garbled(time)
                time = time.split(u'来自')[0]
                time = time.strip()
                # print(time)

                if u'刚刚' in time or u'秒' in time:
                    publish_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                elif u'分钟' in time:
                    minute = time[: time.find(u'分钟')]
                    minute = timedelta(minutes=int(minute))
                    publish_time = (datetime.now() - minute).strftime('%Y-%m-%d %H:%M')
                elif u'今天' in time:
                    time, _, min = time.partition(' ')
                    # print('----time:' + time)
                    # print('----min:' + min)
                    today = datetime.now().strftime('%Y-%m-%d')
                    if not min:
                        time = time[2:]
                    else:
                        time = min
                    publish_time = today + ' ' + time
                elif u'月' in time:
                    time, _, min = time.partition(' ')
                    year = datetime.now().strftime('%Y')
                    month = time[0: 2]
                    day = time[3: 5]
                    time = min if min else time[7: 12]
                    publish_time = year + '-' + month + '-' + day + ' ' + time
                else:
                    publish_time = time[:16]
                print('发布时间: {}'.format(publish_time))
                information['publish_time'] = publish_time
                Microblog.append(information)
            return Microblog
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def is_original(self, info):
        try:
            is_original = info.xpath("div[@class='card-comment']")
            if not is_original:
                return True    # 原创微博
            else:
                return False   # 转发微博
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def original_content(self, info):
        try:
            # 判断是否为长微博
            is_long = info.xpath("p/a/text()")
            if u'展开全文' in is_long:
                # 长微博内容
                a_href = info.xpath("p[@class='txt']")[1]
                content = self.deal_garbled(a_href)
                content = content[re.search(r'\S', content).start(): content.rfind(u'收起全文')]
                return content
            else:
                # 短微博内容
                a_href = info.xpath("p[@class='txt']")[0]
                content = self.deal_garbled(a_href)
                content = content[re.search(r'\S', content).start(): -1]
                return content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def retweet_content(self, info):
        try:
            # 判断是否为长微博
            is_long = info.xpath("p/a/text()")
            if u'展开全文' in is_long:
                # 长微博内容
                a_href = info.xpath("p[@class='txt']")[0]
                # 转发理由
                reason = self.deal_garbled(a_href)
                reason = reason[re.search(r'\S', reason).start():]

                retweet_info = info.xpath("div[@class='card-comment']/div[@class='con']")[1]
                retweet_info = self.deal_garbled(retweet_info)
                retweet_info = retweet_info.strip()
                # 转发用户的用户名
                retweet_user, _, after = retweet_info.partition(' ')  # retweet_user: @帝吧官微
                retweet_user = retweet_user[1:]  # retweet_user: 帝吧官微

                # 转发内容
                after = after.strip()
                content = after[re.search(r'\S', after).start(): after.rfind(u'收起全文')]

                retweet_content = '转发理由: {}'.format(reason) + '\n' + '来自: {}:'.format(retweet_user) + '\n' + '原文内容: {}'.format(
                    content)
                # print(retweet_content)
                return retweet_content
            else:
                # 短微博内容
                a_href = info.xpath("p[@class='txt']")[0]
                # 转发理由
                reason = self.deal_garbled(a_href)
                reason = '无' if not reason else reason[re.search(r'\S', reason).start():]

                retweet_info = info.xpath("div[@class='card-comment']/div[@class='con']")[0]
                retweet_info = self.deal_garbled(retweet_info)
                retweet_info = retweet_info.strip()
                # 转发用户的用户名
                retweet_user, _, after = retweet_info.partition(' ')  # retweet_user: @帝吧官微
                retweet_user = retweet_user[1:]  # retweet_user: 帝吧官微

                # 转发内容
                after = after.strip()
                content, _, _ = after.partition(' ')

                retweet_content = '转发理由: {}'.format(reason) + '\n' + '来自: {}:'.format(retweet_user) + '\n' + '原文内容: {}'.format(content)
                # print(retweet_content)
                return retweet_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def write_txt(self, type, flag, i):
        try:
            """
            文件结构
            --- information
                --- 2021-01-04(当前时间) 
                    --- topic(txt/csv)
                    --- content_top(txt/csv)
                    --- content_1(txt/csv)
                    --- content_2(txt/csv)
                    ...
                    --- content_50(txt/csv)
                --- 2021-01-04(当前时间) 
                    --- topic(txt/csv)
                    --- content_top(txt/csv)
                    --- content_1(txt/csv)
                    --- content_2(txt/csv)
                    ...
                    --- content_50(txt/csv) 
            """
            # 信息存储位置: 'E:\\py_project\\weibo_analysis\\information\\2021-01-04 17:29:05'
            file_dir = os.path.split(os.path.realpath(__file__))[0]
            # time = datetime.now().strftime('%Y-%m-%d_%H%M')
            file_dir = file_dir + os.sep + 'information' + os.sep + self.time

            if not os.path.exists(file_dir) and flag:
                os.makedirs(file_dir)
                flag = False

            # 存储话题
            if type == 'topic':
                topic_dir = file_dir + os.sep + type + '.txt'

                with open(topic_dir, 'ab') as f:
                    f.write((self.time + '\n').encode(sys.stdout.encoding))
                    for i in range(len(self.topic['affair'])):
                        if i == 0:
                            f.write(('top:  {}'.format(self.topic['affair'][0]) + '\n' +
                                     self.urls_list[i] + '\n').encode(sys.stdout.encoding))
                        else:
                            f.write(('{}: '.format(i).rjust(5) + self.topic['affair'][i].ljust(5) +
                                     self.topic['view'][i - 1] + '\n' +
                                     self.urls_list[i] + '\n').encode(sys.stdout.encoding))
                    f.write(('\n').encode(sys.stdout.encoding))
                f.close()

            # 存储内容
            if type == 'top':
                top_dir = file_dir + os.sep + type + '.txt'

                with open(top_dir, 'ab') as f:
                    f.write((u'话题: ' + self.MicroBlog['title'] + '\n' +
                             u'阅读量: ' + self.MicroBlog['read'] + '\n' +
                             u'讨论量: ' + self.MicroBlog['discussion'] + '\n' +
                             u'导语: ' + self.MicroBlog['topic'] + '\n').encode(sys.stdout.encoding))
                    f.write(('*' * 150).encode(sys.stdout.encoding))

                    content = self.MicroBlog['content']
                    for i in range(len(content)):
                        f.write(('\n' + u'用户名: ' + content[i]['name'] + '\n' +
                                 u'微博内容: ' + content[i]['content'] + '\n' +
                                 u'发布时间: ' + content[i]['publish_time'] + '\n' + '-' * 150).encode(sys.stdout.encoding))
                    f.write(('-' * 150 + '\n').encode(sys.stdout.encoding))
                f.close()

            if type == 'content':
                tmp = str(0) + str(i) + '_' if i < 10 else str(i) + '_'
                content_dir = file_dir + os.sep + tmp + self.MicroBlog['title'] + '.txt'

                with open(content_dir, 'ab') as f:
                    f.write((u'话题: ' + self.MicroBlog['title'] + '\n' +
                             u'阅读量: ' + self.MicroBlog['read'] + '\n' +
                             u'讨论量: ' + self.MicroBlog['discussion'] + '\n').encode(sys.stdout.encoding))
                    f.write(('*' * 150).encode(sys.stdout.encoding))

                    content = self.MicroBlog['content']
                    for i in range(len(content)):
                        f.write(('\n' + u'用户名: ' + content[i]['name'] + '\n' +
                                 u'微博内容: ' + content[i]['content'] + '\n' +
                                 u'发布时间: ' + content[i]['publish_time'] + '\n' + '-' * 150).encode(sys.stdout.encoding))
                    f.write(('-' * 150 + '\n').encode(sys.stdout.encoding))
                f.close()

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def deal_html(self, url):
        try:
            """ 处理html """
            response = requests.get(url)
            html = response.content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def deal_garbled(self, info):
        try:
            """ 处理乱码 """
            info = (info.xpath('string(.)').replace(u'\u200b', '').encode(
                sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
            return info
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()


