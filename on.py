from wss import WebCourse
from random import choice


async def on_message(bot: WebCourse, msg: str):
    print(msg)
    if msg in ["缺席人员", "学生"]:
        await bot.all_user()
    elif msg == "抽选":
        await bot.send_msg(choice(list(bot.class_user)))
    else:
        ...


async def on_notice(bot: WebCourse, data: dict):
    now = bot.now() + "\n"
    update_list = data.get("rpt_msg_member_update_list")
    print(update_list)
    if update_list:
        add_user = [f"姓名：{i['str_nick_name']}\nQQ：{i['uint64_uin']}" for i in update_list]
        await bot.send_msg(f"{now}有同学加入课堂\n" + '\n'.join(add_user))
    else:
        await bot.send_msg(now + "有同学离开课堂！！")
