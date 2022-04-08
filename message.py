from typing import Union, List
from aiohttp import ClientSession
from pathlib import Path


class Message(list):
    save_path = Path("data/image")
    _msg_type = {
        "text": "msg_text",
        "face": "msg_face",
        "image": "msg_not_online_image"
    }

    def get(self, typeof: str):
        typeof = self._msg_type.get(typeof)
        return Message([msg for msg in self if msg.get(typeof)], False)

    def __init__(self, message: Union[List[dict], str] = None, modify=True):
        if isinstance(message, list):
            super().__init__(message)
            if modify:
                self.reset_image()
                self.pop_not18_add_user()
        else:
            if isinstance(message, str):
                self.text(message)

    def pop_not18_add_user(self):
        """移除消息中 msg_add_info"""
        for msg in self:
            if msg["uint32_elem_type"] != 18 and msg.get("msg_add_info"):
                msg.pop("msg_add_info")

    def reset_image(self):
        typeof = self._msg_type.get("image")
        for msg in self:
            if msg.get(typeof):
                if "edu_msgpic" in msg[typeof]["bytes_pic_md5"]:
                    msg[typeof]["bytes_pic_md5"] = "data:code/hex;" + msg[typeof]["bytes_pic_md5"].split("/")[-2]

    def image(self, pic_md5: str):
        """
        发送的格式
            data:code/hex;[md5]
        收到的格式
            //p.qpic.cn/edu_msgpic/0/[md5]/0
        """
        self.append({
            "msg_not_online_image": {
                "bytes_pic_md5": pic_md5
            },
            "uint32_elem_type": 3
        })
        return self

    def text(self, text: str):
        self.append({
            "msg_text": {
                "bytes_str": text
            },
            "uint32_elem_type": 1
        })
        return self

    def face(self, index: int):
        self.append({
            "msg_face": {
                "uint32_index": index
            },
            "uint32_elem_type": 2
        })
        return self

    def add_info(self, user_name: str):
        for msg in self:
            if msg["uint32_elem_type"] == 18:
                return self
        self.append({
            "msg_add_info": {
                "str_nick_name": user_name
            },
            "uint32_elem_type": 18
        })
        return self

    def raw_text(self):
        return "".join([msg["msg_text"].get("bytes_str", "") for msg in self.get("text") if msg.get("msg_text")])

    @staticmethod
    def get_md5(url) -> str:
        if "data:code" in url:
            return url.split(';')[-1]
        elif "p.qpic.cn/edu_msgpic" in url:
            return url.split("/")[-2]

    async def save_image(self, name: str = ""):
        for url in self.get("image"):
            _md5 = self.get_md5(url["msg_not_online_image"]["bytes_pic_md5"])
            url = f"https://p.qpic.cn/edu_msgpic/0/{_md5}/0"
            async with ClientSession() as session:
                async with session.get(url) as res:
                    data = await res.read()
                    if data:
                        with open(self.save_path / f"{name}{_md5}.jpg", "wb") as file:
                            file.write(data)


class MemberUpdateList(list):
    ...
