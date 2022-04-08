from ManagementSystem import ManagementSystem
from wss import WebCourse, Message, pprint
from random import choice
ms = ManagementSystem()
command = {
    "show_user": False
}


async def on_message(bot: WebCourse, msg: Message, nickname: str):
    text = msg.raw_text()
    print(text)
    name = ms.class_student_name(nickname)
    ms.to_speak(name, text)
    await bot.all_user()
    await msg.save_image(name)
    if text in ["缺席人员", "学生"]:
        command["show_user"] = True
    elif text == "打卡":
        ...
    elif text == "抽选":
        await bot.send_msg(choice(list(ms.class_student)))
    else:
        ...


async def on_notice(bot: WebCourse, data: dict):
    now = bot.now() + "\n"
    for user in data.get("rpt_msg_member_update_list", []):
        await bot.send_msg(f"{now}有同学加入课堂\n{user['str_nick_name']}")
        break
    else:
        await bot.all_user(ms.student_length)
        await bot.send_msg(now + "有同学离开课堂！！")
