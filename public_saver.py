# TODO:
# - handle domain alias and id
# - make arguments check
# - implement download without requests?
# - handle download size description
# - fix ZeroDivisionError O.o
# - escape folder and file names
# - transform public names to ids and use ids only

import os
import pprint
import re
import requests
import sys
import argparse


from vk_api import Vk

vk = None
SAVE_FOLDER = "stalincunt_posts"


def get_filename_from_url(url):
    filename = url.split("/")[-1]
    return filename


def download_url(url, filename="", folder="", chunk_size=1024):
    # TODO: make humanize library to display file size more readably
    if not filename:
        filename = get_filename_from_url(url)

    if folder:
        try:
            if not os.path.exists(folder):
                os.mkdir(folder)
        except FileNotFoundError:
            print("Something wrong with folder name ({})".format(folder))
            return
        filename = os.path.join(folder, filename)
    if os.path.exists(filename):
        return filename
    if not url:
        raise Exception("No url supplied.")

    headers = {'Accept-Encoding': None}
    r = requests.head(url, headers=headers)
    filesize = int(r.headers["Content-Length"])
    print("Downloading {size} MB".format(size=filesize // 1024 // 1024))
    chunks = filesize // chunk_size
    chunks_downloaded = 0
    r = requests.get(url, stream=True, headers=headers, verify=False)
    print("Trying to download file {name}.".format(name=filename))
    try:
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                try:
                    percent = int(chunks_downloaded / chunks * 100)
                except ZeroDivisionError:
                    percent = 100
                sys.stdout.write('\r [{0}] {1}%'.format('#' * int(percent / 10), percent))
                if chunk:
                    f.write(chunk)
                    f.flush()
                    chunks_downloaded += 1
                sys.stdout.flush()
            print("\tFile downloaded.")
        return filename
    except FileNotFoundError:
        print('Error opening file {filename}'.format(filename=filename))


def check_availability():
    pass


def get_id_from_name(name_str):
    """ transforms public shrtame or url into ownner_id"""
    # public_url = "http://www.vk.com/puclic41qwrqrqwr"
    public_pattern = r"(http:\/\/|https:\/\/)?(www\.)?vk\.com\/public([\d]+)"
    r = re.match(public_pattern, name_str)
    if r:
        print(r.groups()[-1])
    pass


def download_posts(group_id, posts_limit=""):
    """This method actually downloads attachments from supplied posts"""
    posts_num = posts_limit if posts_limit else get_posts_num(group_id=group_id)
    for post_list in get_posts_portion(group_id=group_id, total_posts=posts_num):
        for post in post_list:
            folder_name = post.get("text", "NoName")
            if post.get("attachments", 0):
                for url in get_attachments_urls(post["attachments"]):
                    full_path = os.path.join(group_id, folder_name)
                    # print("Downloading to {}".format(full_path))
                    download_url(url, folder=full_path)


def get_posts_num(group_id):
    """returns number of posts of the scpecified public or group"""
    return int(vk.api_method("wall.get", domain=group_id)["response"]["count"])


def get_posts_portion(group_id="", total_posts=0, post_count=100):
    """Generates portions of wall posts of the given group."""
    offset = 0
    if offset >= total_posts:
        raise StopIteration
    while offset <= total_posts:
        r = vk.api_method("wall.get", domain=group_id, offset=offset, count=post_count)
        posts = r["response"]["items"]
        offset += post_count
        yield posts


def validate_folder_name(post_text):
    return post_text


def get_attachments_urls(attachments_list, download_audio=False, download_video=False):
    """Gets attachments urls and with maximum quality photos."""
    url_list = []
    for attachment in attachments_list:
        if attachment["type"] == "photo":
            photo_keys = attachment["photo"]
            max_size_url = max([photo_key for photo_key in photo_keys
                                if re.match(r"photo_([\d])+", photo_key)],
                                key=lambda x: int(re.search(r"photo_([\d]+)", x).group(1)))
            url_list.append(photo_keys[max_size_url])
    return url_list


def main():
    # posts = get_posts()
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--group-id", type=str,
                        help="Group or public id or domain shortcut.",
                        required=True)
    parser.add_argument("-p", "--posts-num", type=int, default=0,
                        help="Limits the number of posts to be downloaded.")
    parser.add_argument("--analyze-reposts", action="store_true",
                        help="If supplied reposts will alose be analyzed and downloaded.",)
    parser.add_argument("--save-audio", action="store_true",
                        help="If supplied script will download audio attachments of the post.",)
    parser.add_argument("--save-video", action="store_true",
                        help="If supplied script will download video attachments of the post.",)
    args = parser.parse_args()
    # get_id_from_name(args.group_id)
    # exit()
    global vk
    vk = Vk.Vk()
    try:
        os.mkdir(args.group_id)
    except FileExistsError:
        pass
    # os.chdir(SAVE_FOLDER)
    # exit()
    download_posts(group_id=args.group_id, posts_limit=args.posts_num)

if __name__ == '__main__':
    main()
