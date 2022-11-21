import json
import os


async def flush(path, data: dict):
    with open(path, "w") as write_file:
        json.dump(data, write_file)


async def load(path):
    if os.path.exists(path):
        with open(path) as read_file:
            return json.load(read_file)
    else:
        f = open(path, "x")
        f.close()
        return {}

def is_english_alphanum(s:str):
    return s.isalnum() and s.isascii()


def sanitized_file_name(prompt, requestor):
    dirty_filename = f"{prompt[:20]}{requestor}"
    dirty_filename = ''.join(filter(is_english_alphanum, dirty_filename))
    dirty_filename = dirty_filename.replace(" ", "_")
    return dirty_filename + ".png"