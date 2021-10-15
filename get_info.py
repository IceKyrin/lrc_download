from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3


def s2m(length):
    length = int(length)
    return length / 60, str(length % 60).zfill(2)


def auto(path):
    m_type = str(path).split(".")[-1]
    if m_type == 'mp3':
        return mp3(path)
    elif m_type == 'flac':
        return flac(path)
    else:
        return {'title': 'None', 'artist': 'None'}


def mp3(path):
    info = {}
    id3info = MP3(path, ID3=EasyID3)
    info["title"] = id3info['title'][0] if "title" in id3info else "None"
    info["artist"] = id3info['artist'][0] if "artist" in id3info else "None"
    info["length"] = "%d:%s" % s2m(MP3(path).info.length)
    return info


def flac(path):
    info = {}
    audio = FLAC(path)
    info["title"] = audio['title'][0] if "title" in audio else "None"
    info["artist"] = audio['artist'][0] if "artist" in audio else "None"
    info["length"] = "%d:%s" % s2m(audio.info.length)
    return info
