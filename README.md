# VK public page attachments downloader
Python script that downloads attachments from VK public pages.

# Prerequisites
Run following commands to install requests and vk_api library:
```
pip install requests
git clone https://github.com/MrLokans/vk_api
cd vk_api
python setup.py install
```

## Usage
run 
`python public_saver -g "public name or link"`

## Arguments:
```
   optional arguments:
  -g GROUP_ID, --group-id GROUP_ID
                        Group or public id or domain shortcut.
  -p POSTS_NUM, --posts-num POSTS_NUM
                        Limits the number of posts to be downloaded.
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Folder to download attachments. By default equal to
                        page name.

  --single-folder       Whether to create subfolders. If supplied will
                        download all media fiels in single folder.

```

Currently it downoads only pictures from vk groups and publics that are specialised on paintings or pictures. In future the download of any attached content will be added.