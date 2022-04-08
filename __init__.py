from datetime import datetime
from pprint import pprint
from asyncio import get_event_loop

from wss import WebCourse, logger
from on import on_message, on_notice, ms, command
import config
from message import Message

wc = WebCourse(config.room_id, config.user_id)


def user_list(data: dict):
    return [i["str_nick_name"] for i in data["rpt_msg_role_info"]]

# @wc.on_receive("imconnect")
# async def _(data):
#     ...
    # await wc.all_user()


@wc.on_receive("push")
async def _(data):
    # pprint(data)
    for i in data["list"]:
        if i["cmd"] == "msg":
            body: dict = i["data"]["body"]
            # 消息事件
            for msg in body.get("rpt_msg_entry", []):
                await on_message(
                    wc,
                    Message(msg["msg_body"]["msg_rich_text"]["rpt_msg_elems"]),
                    msg["msg_msg_head"]["str_nick_name"]
                )
            # 直播间变动
            if body.get("msg_subcmd0x2_member_update_list"):
                await on_notice(wc, body["msg_subcmd0x2_member_update_list"])
        else:
            print(data)


@wc.on_receive("cgi")
async def _(data):
    now = wc.now()
    cmd = data.get("cmd")
    if cmd == '0x6ff_0x510':
        member = data["data"]["msg_subcmd0x1_rsp_memberpage"]
        if command["show_user"]:
            command["show_user"] = False
            member_list = user_list(member)
            if member["uint32_totalcount"] != len(member_list):
                return await wc.all_user(member["uint32_totalcount"])
            empty_studio = ms.search(member_list)
            if empty_studio:
                await wc.send_msg(now + "\n未加入直播间学生：\n" + "\n".join(empty_studio))
            else:
                await wc.send_msg(now + "\n全员到齐")


@wc.on_receive("get")
async def _(data):
    pprint(data)


try:
    get_event_loop().run_until_complete(wc.run())
except (Exception, KeyboardInterrupt) as err:
    print(err)
finally:
    ms.save_speak()

