from asyncio import ensure_future, wait, create_task, sleep
from json import loads, dumps, JSONDecodeError
from pprint import pprint
from os.path import exists
from time import time
from log import logger
from datetime import datetime
from aiohttp import ClientSession
from aiohttp.client_ws import ClientWebSocketResponse
from aiohttp.http_websocket import WSMessage
from typing import Union, Tuple, Optional

import re

import config
from message import Message


class WebCourse:
    sid: str = None
    pingTimeout: int = 0
    pingInterval: int = 0
    _seq = -1
    _event = dict()
    _connect = set()
    wss: ClientWebSocketResponse = None
    request_id = "27de2b58-33a6-4bd3-8428-28de47500333"

    @property
    def seq(self):
        self._seq += 1
        return self._seq

    @property
    def headers(self) -> dict:
        return {
            "Upgrade": "websocket",
            "Origin": "https://ke.qq.com",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "Sec-WebSocket-Key": "Hkg4X5WSjllTdC+pPXH5Pg==",
            "Cookie": self.cookie,
            "Pragma": "no-cache",
            "Sec-WebSocket-Version": "13",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/99.0.4844.51 Safari/537.36 "
        }

    @property
    def cookie(self) -> str:
        file = "_cookie.txt" if exists("_cookie.txt") else "cookie.txt"
        with open(file, "r") as file:
            cookie = file.read()
            if cookie:
                return cookie
            logger.error("缺少cookie值，请将cookie值加入到cookie.txt")

    @property
    def params(self):
        return {
            "roomId": self.room_id,
            "appId": "tencentedu",
            "version": 2,
            "type": "",
            "role": "",
            "EIO": 3,
            "transport": "websocket"
        }

    @property
    def session(self):
        if self._session is None:
            self._session = ClientSession()
        return self._session

    @staticmethod
    def code(msg):
        """提取数据中的状态码"""
        return re.search(r"^\d+", msg.data).group()

    @staticmethod
    def json(msg: WSMessage, code: str) -> Union[list, dict]:
        """转json数据"""
        return loads(msg.data.replace(code, ""))

    @staticmethod
    def now():
        return str(datetime.now()).split(".")[0]

    @staticmethod
    def time() -> int:
        return int(time())

    async def im_connect(self):
        """建立连接"""
        for i in [
            ["imconnect",
             {"cmd": "register", "appId": "tencentedu", "roomId": self.str_room_id, "seq": self.seq,
              "modId": "webclass"}],
            ["cgi", {"data": {"msg_subcmd0x2_req_get_current_speak_mode": {"uint32_course_abs_id": self.room_id},
                              "uint32_sub_cmd": 2}, "app_id": "tencentedu", "room_id": self.str_room_id,
                     "mod_id": "webclass", "request_id": self.request_id, "seq": self.seq,
                     "cmd": "0x3aa"}],
            ["cgi", {"data": {"uint32_sub_cmd": [1], "msg_subcmd0x1_req_sign_info": {"term_id": self.room_id}},
                     "app_id": "tencentedu", "room_id": self.str_room_id, "mod_id": "webclass",
                     "request_id": self.request_id, "seq": self.seq, "cmd": "OnlineClassImLogic"}],

        ]:
            await self.send(i)

    async def ping(self):
        """心跳包"""
        while True:
            await sleep(self.pingInterval)
            await self.wss.send_str("2")

    async def upload_pic(self, file_path: str):
        """图片发送到腾讯服务器，然后获得文件的md5值"""
        with open(file_path, "rb") as file:
            with self.session.post(config.upload_pic_ie, data={
                "filename": file.read(),
                "bkn": 604173287,
                "r": self.time()
            }) as res:
                fid = await res.json()
                return fid["result"]["fid"]

    async def close(self):
        await self.session.close()

    async def connect(self):
        async with self.session.ws_connect(config.WebCourseUrl, params=self.params, headers=self.headers) as wss:
            self.wss = wss
            await self.im_connect()
            ensure_future(wait(
                {create_task(self.ping())} |
                {create_task(i()) for i in self._connect}
            ))
            async for msg in wss:  # type: WSMessage
                code = self.code(msg)
                if code == "0":
                    data = self.json(msg, code)
                    self.sid = data["sid"]
                    self.pingTimeout = data["pingTimeout"]
                    self.pingInterval = data["pingInterval"]
                elif code == "42":
                    try:
                        ensure_future(self.receive(self.json(msg, code)))
                    except JSONDecodeError as err:
                        print(msg.data)
                        print(err)
                        logger.error("解析失败: " + msg.data)
                elif code in ["40", "3"]:
                    """忽略"""
                # else:
                #     print(msg)

    async def receive(self, data: list):
        """接收到消息"""
        request_type = data[0]
        logger.info("收到请求类型: " + request_type)
        event = self._event.get(request_type)
        if event:
            if not isinstance(data[1], str):
                await wait({create_task(i(data[1])) for i in event})
        if request_type == "push" and isinstance(data[1], dict):
            await self.ackPush(data[1].get("ackId"))

    def on_receive(self, request_type: str):
        """注册消息事件"""

        def addEvent(func):
            logger.info("添加注册事件: " + request_type)
            if request_type not in self._event:
                self._event[request_type] = set()
            self._event[request_type].add(func)

        return addEvent

    def on_connect(self, func):
        """注册初次连接事件"""
        self._connect.add(func)

    # ---------------------------------- 初始化 ----------------------------------
    def __init__(
            self,
            room_id: Union[str, int],
            user_id: int,
            user_name: str = None,
            *,
            session: ClientSession = None
    ):
        self.user_id = user_id
        self.user_name = user_name or config.nickname
        self.room_id = int(re.findall(r"/\d+", room_id)[-1].replace("/", "")) if isinstance(room_id, str) else room_id
        self.str_room_id = str(self.room_id)
        self._session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.connect()
        await self.close()

    # ---------------------------------- 发送 ----------------------------------

    async def send(self, data: Union[dict, list]):
        """打包发送消息"""
        if self.wss:
            await self.wss.send_str("42" + dumps(data))

    async def ackPush(self, ack: str):
        """回滚"""
        if ack:
            await self.send(["ackPush", ack])

    async def flower(self):
        """送花"""
        await self.send([
            "cgi",
            {
                "data": {
                    "uint32_item_id": 1,
                    "uint32_sub_cmd": 2,
                    "msg_set_req_body": {
                        "uint32_group_id": self.room_id,
                        "uint32_buss_type": 5,
                        "uint32_auth_type": 1,
                        "uint32_auth_key": self.room_id,
                        "uint64_dest_uin": 3017334555,
                        "str_dest_nick": "李红日",
                        "str_from_nick": self.user_name,
                        "str_from_makr": "",
                        "uint32_course_abs_id": self.room_id
                    }
                },
                "app_id": "tencentedu",
                "room_id": self.str_room_id,
                "mod_id": "webclass",
                "request_id": self.request_id,
                "seq": self.seq,
                "cmd": "0x311"
            }
        ])

    async def send_msg(
            self,
            msg: Union[Message, str],
            send_time: int = None,
            seq: int = None) -> Tuple[Optional[int], Optional[int]]:
        """发送消息"""
        if isinstance(msg, str):
            msg = Message(msg)
        msg.add_info(self.user_name)
        seq = seq or self.seq
        send_time = send_time or self.time()
        await self.send(["cgi", {
            "data": {
                "msg_body": {
                    "msg_rich_text": {
                        "msg_attr": {
                            "uint32_char_set": 0,
                            "uint32_color": 0,
                            "uint32_effect": 0,
                            "uint32_pitch_and_family": 0,
                            "uint32_time": send_time
                        },
                        "rpt_msg_elems": msg
                    }
                },
                "msg_content_head": {
                    "uint32_div_seq": send_time,
                    "uint32_pkg_index": 0,
                    "uint32_pkg_num": 1
                },
                "msg_routing_head": {
                    "msg_edu": {
                        "uint32_course_id": self.room_id
                    }
                },
                "str_remark": "@SELF-" + str(send_time),
                "uint32_label": 0,
                "uint32_msg_rand": self.room_id,
                "uint32_msg_seq": send_time,
                "uint32_uid_type": 0,
                "uint32_role": 0,
                "uint32_msg_type": 0,
                "str_reply_msg_id": "",
                "uint32_explain_type": 0
            },
            "app_id": "tencentedu",
            "room_id": self.room_id,
            "mod_id": "webclass",
            "request_id": self.request_id,
            "seq": seq,
            "cmd": "0x3a4"
        }])
        return send_time, seq

    async def all_user(self, count: int = 50):
        """发起获取直播间所以用户请求"""
        min_count = 50
        count = min_count if count < min_count else count
        await self.send(["cgi", {
            "data": {
                "msg_subcmd0x1_req_memberpage": {
                    "str_course_abs_id": self.str_room_id,
                    "uint32_page_operation": 0,
                    "uint32_page_num": count // min_count + 1,
                    "uint32_need_special_user": 1,
                    "uint32_per_page_count": count,
                    "uint32_version": 1
                }, "uint32_sub_cmd": 1},
            "app_id": "tencentedu",
            "room_id": self.str_room_id,
            "mod_id": "webclass",
            "request_id": self.request_id,
            "seq": self.seq,
            "cmd": "0x6ff_0x510"}])
        await self.req_get_info()
        await self.req_get_info()

    async def req_get_info(self):
        await self.send(
            ["cgi",
             {"data": {"msg_subcmd0x1_req_get_info": {"str_course_abs_id": self.str_room_id}, "uint32_sub_cmd": 1},
              "app_id": "tencentedu", "room_id": self.str_room_id, "mod_id": "webclass",
              "request_id": self.request_id, "seq": self.seq, "cmd": "0x6ff_0x509"}])

    async def run(self):
        await self.connect()
        await self.close()
