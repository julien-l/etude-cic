import yaml
import requests
import tempfile
from urllib.parse import urlparse
from pathlib import Path
from mutagen.mp3 import MP3
import uuid
from jinja2 import Environment, FileSystemLoader, select_autoescape


class Mp3Info:
    def __init__(self, length_bytes, duration_sec):
        self.length_bytes = length_bytes
        self.duration_sec = duration_sec


def get_mp3_info(url, tmp_path):
    print(f"Téléchargement de {url}")
    data = requests.get(url).content
    length_bytes = len(data)
    file_name = Path(urlparse(url).path).name
    dest = tmp_path / file_name
    with open(dest, "wb") as file:
        file.write(data)
    audio = MP3(dest)
    duration_sec = round(audio.info.length)
    return Mp3Info(length_bytes, duration_sec)


def generate(yaml_file, tmp_dir):
    with open(yaml_file, "r") as file:
        episodes = yaml.safe_load(file)
    episodes = sorted(episodes, key=lambda e: e["number"])
    for episode in episodes:
        episode["title"] = episode["title"].replace("’", "&apos;")
    tmp_path = Path(tmp_dir.name)
    for x in episodes:
        url = x["url"]
        info = get_mp3_info(url, tmp_path)
        yield {
            "title": x["title"],
            "link": x["link"],
            "number": x["number"],
            "enclosure": {
                "url": url,
                "length": info.length_bytes,
                "type": "audio/mpeg",
            },
            "guid": str(uuid.uuid4()),
            "duration": info.duration_sec,
        }


tmp_dir = tempfile.TemporaryDirectory()
episodes = [x for x in generate("episodes.yml", tmp_dir)]

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())
template = env.get_template("feed.xml.jinja")
feed = template.render(episodes=episodes)

with open("feed.xml", "w") as file:
    file.write(feed)
