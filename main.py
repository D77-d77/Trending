import configs

from MicroBlog import MicroBlog

def main(args):
    # 使用实例，输入热搜网址，所有信息都会存储在文件information中
    url = args.url
    flag = args.flag
    index = args.index
    str_time = args.str_time

    # 调用MicroBlog类，创建微博实例MB
    MB = MicroBlog(url, flag, index, str_time)

    # 爬取微博热搜
    MB.start()

if __name__ == '__main__':
    args = configs.parse_args()
    main(args)