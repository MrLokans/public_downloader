# TODO:
# [ ] handle download size description
# [+-] escape folder and file names
# [ ] handle audio, document and video download
# [ ] cover with tests
# [ ] use progressbar lib

import os
import re
import requests
import sys
import argparse


from vk_api import Vk
from vk_api.Vk import API_Error

vk = None
SAVE_FOLDER = "stalincunt_posts"
MAX_POST_PER_REQUEST = 100


def get_filename_from_url(url):
    """Returns last component of the URI that is almost
    always a filename"""
    filename = url.split("/")[-1]
    return filename


def download_from_url(url, filename="", folder="", chunk_size=1024):
    """Downloads content and saves into the specified file"""
    # TODO: make humanize library to display file size more readably
    if not filename:
        filename = get_filename_from_url(url)

    if folder:
        folder = folder[:MAX_POST_PER_REQUEST+1]
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


def get_id_from_name(name_str):
    """ transforms public alias or url into ownner_id"""
    public_id = name_str
    public_pattern = r"(http:\/\/|https:\/\/)?(www\.)?vk\.com\/public([\dA-Za-z_]+)"
    r = re.match(public_pattern, name_str)
    if r:
        public_id = r.groups()[-1]
    elif "/" in name_str:
        public_id = name_str.split("/")[-1]
    try:
        r = vk.api_method("groups.getById", group_id=public_id)
        public_id = r["response"][0]["id"]
    except API_Error:
        print("There is no such group or id {}".format(public_id))
    return public_id


def get_group_name(id):
    try:
        name = vk.api_method("groups.getById", group_id=id)["response"][0]["name"]
        return name
    except API_Error:
        print("No such group with id {}".format(id))
    return ""


def download_posts(group_id, posts_limit="", save_folder="", use_single_folder=False):
    actual_id = str(get_id_from_name(group_id))
    """This method actually downloads attachments from supplied posts"""
    posts_num = posts_limit if posts_limit else get_posts_num(group_id=actual_id)
    for post_list in get_posts_portion(group_id=actual_id, total_posts=posts_num):
        for post in post_list:
            folder_name = post.get("text", "NoName")
            if not post.get("attachments", 0):
                continue
            for url in get_attachments_urls(post["attachments"]):
                full_path = save_folder
                if not use_single_folder:
                    full_path = os.path.join(save_folder, folder_name)

                download_from_url(url, folder=full_path)


def get_posts_num(group_id):
    """returns number of posts of the scpecified public or group"""
    return int(vk.api_method("wall.get",
                             owner_id="-"+group_id)["response"]["count"])


def get_posts_portion(group_id="", total_posts=0, post_count=100):
    """Generates portions of wall posts of the given group."""
    offset = 0
    if offset >= total_posts:
        raise StopIteration
    while offset <= total_posts:
        r = vk.api_method("wall.get",
                          owner_id="-" + group_id,
                          offset=offset,
                          count=post_count)
        posts = r["response"]["items"]
        offset += post_count
        yield posts


def validate_folder_name(post_text):
    return post_text


def get_attachments_urls(attachments_list,
                         download_audio=False,
                         download_video=False):
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
    parser.add_argument("-o", "--output-folder", type=str,
                        help="Folder to download attachments. By default equal to page name.",)
    parser.add_argument("--analyze-reposts", action="store_true",
                        help="If supplied reposts will alose be analyzed and downloaded.",)
    parser.add_argument("--save-audio", action="store_true",
                        help="If supplied script will download audio attachments of the post.",)
    parser.add_argument("--save-video", action="store_true",
                        help="If supplied script will download video attachments of the post.",)
    parser.add_argument("--single-folder", action="store_true",
                        help="Whether to create subfolders. If supplied will download all media fiels in single folder.",)
    args = parser.parse_args()

    global vk
    vk = Vk.Vk()
    group_id = get_id_from_name(args.group_id)
    group_name = get_group_name(group_id)
    if not(group_id and group_name):
        print("There is something wrong with group name or id, exiting...")

    save_to = args.output_folder or group_name
    download_posts(group_id=args.group_id,
                   posts_limit=args.posts_num,
                   save_folder=save_to,
                   use_single_folder=args.single_folder)

if __name__ == '__main__':
    main()
