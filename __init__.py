from datetime import datetime
from pprint import pprint
from asyncio import run

from wss import WebCourse
from on import on_message, on_notice
import config
from message import Message

wc = WebCourse(config.room_id, config.user_id)


@wc.on_receive("imconnect")
async def _(data):
    ...
    # await wc.all_user()


@wc.on_receive("push")
async def _(data):
    # pprint(data)
    text = ""
    for i in data["list"]:
        if i["cmd"] == "msg":
            body: dict = i["data"]["body"]
            # 消息事件
            for msg in body.get("rpt_msg_entry", []):
                for m in msg["msg_body"]["msg_rich_text"]["rpt_msg_elems"]:
                    if m.get("msg_text"):
                        if m["msg_text"].get("bytes_str"):
                            text += m["msg_text"]["bytes_str"]
                await on_message(wc, text)
            # 直播间变动
            if body.get("msg_subcmd0x2_member_update_list"):
                await on_notice(wc, body.get("msg_subcmd0x2_member_update_list"))
        else:
            print(data)


@wc.on_receive("cgi")
async def _(data):
    now = wc.now()
    cmd = data.get("cmd")
    if cmd == '0x6ff_0x510':
        live_user = {i["str_nick_name"] for i in data["data"]["msg_subcmd0x1_rsp_memberpage"]["rpt_msg_role_info"]}
        select_user = wc.class_user - {j for i in live_user for j in wc.class_user if j in i}
        if select_user:
            await wc.send_msg(Message(now + "\n未加入直播间学生：\n" + "\n".join(select_user)))
        else:
            await wc.send_msg(Message(now + "\n全员到齐"))


@wc.on_receive("get")
async def _(data):
    pprint(data)


run(wc.run())
