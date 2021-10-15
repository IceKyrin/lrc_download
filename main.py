import os
import re
import json
import time
import get_info
from pyncm import apis

music_file_types = ["mp3", "flac"]


# 读取设置文件
def read_config():
    with open("config.json", "r", encoding="utf-8") as f:
        data = json.loads(f.read())
    return data


# 写入设置文件
def write_config(json_dict):
    with open("config.json", "w+", encoding="utf-8") as f:
        f.write(json.dumps(json_dict))


# 删除括号
def delete_brackets(text):
    return re.sub(u"\\(.*?\\)|{.*?}|\\[.*?]|<.*?>|【.*?】|（.*?）|", "", str(text))


# 获取元数据
def get_info_dict(file_path):
    music_info = get_info.auto(file_path)
    info_dict = {
        "title": delete_brackets(
            music_info["title"] if re.match('[a-z]|[A-Z]', music_info["title"]) else music_info["title"].replace(" ",
                                                                                                                 "")),
        "artist": delete_brackets(music_info["artist"].split("/")[0]),
        "length": music_info["length"]
    }
    return info_dict


# 扫描目录
def get_file_info(file_path, info_dic, dir_list):
    # 获取该目录下所有的文件名称和目录名称
    dir_or_files = os.listdir(file_path)
    for dir_file in dir_or_files:
        # 获取目录或者文件的路径
        dir_file_path = os.path.join(file_path, dir_file)
        # 判断该路径为文件还是路径
        if os.path.isdir(dir_file_path):
            dir_list.append(dir_file_path)
            print("scan %s..." % dir_file_path)
            # 递归获取所有文件和目录的路径
            get_file_info(dir_file_path, info_dic, dir_list)
        else:
            name = dir_file_path.split("\\")[-1]
            m_type = name.split(".")[-1]
            if m_type in music_file_types:
                info_dic[dir_file_path] = {
                    "file_name": name,
                    "type": m_type,
                    "info": get_info_dict(dir_file_path)
                }


# 扫描lrc目录
def get_lrc_file(file_path, info_list):
    # 获取该目录下所有的文件名称和目录名称
    dir_or_files = os.listdir(file_path)
    for dir_file in dir_or_files:
        # 获取目录或者文件的路径
        dir_file_path = os.path.join(file_path, dir_file)
        # 判断该路径为文件还是路径
        if os.path.isdir(dir_file_path):
            pass
        else:
            file_name = dir_file_path.split("\\")[-1]
            info_list.append(file_name.split(".")[0] + '.lrc')


# 只保留中文、大小写字母和阿拉伯数字
def clean_str(raw_str):
    reg = "[^0-9A-Za-z\u4e00-\u9fa5]"
    return re.sub(reg, '', raw_str)


# 字符串转换为多格式
def to_list(a):
    return [a, a.lower(), a.title(), delete_brackets(a), clean_str(a)]


# 新建文件夹
def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


# 列表取交集
def comepare(a, b):
    return True if list(set(a).intersection(set(b))) else False


# 匹配元数据
def match(search_res, music_info):
    music_id = False
    # 遍历搜索结果
    for song_info in search_res:
        # 格式化本地歌曲名
        raw_titles = to_list(music_info["title"])
        ncm_titles = to_list(music_info["title"])
        if comepare(raw_titles, ncm_titles):
            ar = dict(song_info["ar"][0])
            # 格式化云端歌手名
            raw_artists = to_list(music_info["artist"])
            ncm_artists = to_list(ar["name"])
            # 获取云端文件原始信息
            ncm_artists_2 = False
            if song_info["originSongSimpleData"]:
                try:
                    ncm_artists_2 = to_list(song_info["originSongSimpleData"]["artists"][0]["name"])
                except Exception as e:
                    print(e)
                    print("no originSongSimpleData")
            if comepare(raw_artists, ncm_artists):
                music_id = song_info["id"]
            elif ncm_artists_2 and comepare(raw_artists, ncm_artists_2):
                music_id = song_info["id"]
    return music_id


# 保存lrc文件
def write_lrc(data, file_info):
    with open("./lrc/%s-%s.lrc" % (file_info["title"], file_info["artist"]), "w+", encoding="utf-8") as f:
        f.write(data)
        print("%s-%s.lrc success" % (file_info["title"], file_info["artist"]))


# 下载lrc文件
def download_lrc(file_info):
    req_search = apis.cloudsearch.GetSearchResult(file_info["title"], type=1, limit=30, offset=0)
    # print("result:%s" % req_search["result"])
    try:
        if req_search["result"]["songCount"] > 0:
            print("get search result success")
        res = match(req_search["result"]["songs"], file_info)
        if res:
            lrc = apis.track.GetTrackLyrics(res, lv=1, tv=1, rv=1)
            if lrc["code"] == 200:  # 返回成功
                if 'lrc' in lrc.keys():
                    write_lrc(lrc["lrc"]['lyric'], file_info)
                else:
                    if 'lyricUser' in lrc.keys():
                        write_lrc(lrc["lyricUser"]["lrc"]['lyric'], file_info)
            else:
                print(lrc)
        else:
            print("matched fail")
        print("waiting 8 seconds\r\n")
        time.sleep(8)
    except Exception as e:
        print("*" * 50)
        print(e)
        print(res)
        print(key, ':', value)
        print("\r\n")


input(
    "请预先配置config.json,盘符处\"X:\\\\xxx\\xxx\\xxx\"含有两个\\\r\n建议扫描小批量歌曲（目录数<10，歌曲数<200），用于常听歌单的歌词自动匹配下载，调用pyncm模块接入网易云\r\n每次搜索间隔10秒（防止频繁访问），输入回车启动")
config = read_config()
print("音乐路径:%s，lrc歌词存放路径:%s" % (config["file_path"], config["lrc_path"]))
# 根目录路径
music_path = config["file_path"]
# 路径列表
dir_list = []
# 歌曲信息字典
res_dic = {}
get_file_info(music_path, res_dic, dir_list)
# 本地lrc文件
lrc_list = []
make_dir(config["lrc_path"])
get_lrc_file(config["lrc_path"], lrc_list)

for key, value in res_dic.items():
    info = value["info"]
    if info["title"] != "None" and info["artist"] != "None" and "%s-%s.lrc" % (
            info["title"], info["artist"]) not in lrc_list:
        print("=" * 50)
        print("title:%s,artist:%s   searching..." % (info["title"], info["artist"]))
        download_lrc(info)
