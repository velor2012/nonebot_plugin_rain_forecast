import random
import string
from nonebot.plugin import on_regex
from nonebot.params import ArgPlainText
from nonebot.rule import to_me
from nonebot.params import Matcher, RegexGroup
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot import require, get_driver, get_bot
from nonebot.adapters import Event, Bot
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from .config import Config
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from nonebot.adapters import MessageTemplate
from .data_utils import get_datas, save_datas, clear_datas, item2string
from .weather_utils import get_weather_data
require("nonebot_plugin_saa")
from nonebot_plugin_saa import Text, MessageFactory, \
SaaTarget, PlatformTarget, TargetQQGroup, TargetQQPrivate, MessageSegmentFactory, \
Mention, Reply
__version__ = "0.1.1"

__plugin_meta__ = PluginMetadata(
    name="降雨预测",
    description="主要预测指定坐标的降雨情况",
    usage='''
    降雨预测 → 设置降雨提醒 \n
    降雨预测列表 [page] → 列出设置的降雨提醒\n
    清空/清除降雨预测 → 清空所有降雨提醒 \n
    降雨预测jobs [page]  → 列出底层任务情况 \n
    执行/删除/开启/关闭降雨预测 [id] → 执行/删除/开启/关闭指定id的降雨提醒
    更新/修改降雨预测 [id] → 修改降雨预测任务的一些设置
    ''',

    type="application",
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。

    homepage="https://github.com/velor2012/nonebot_plugin_rain_forecast",
    # 发布必填。

    config=Config,
    # 插件配置项类，如无需配置可不填写。

    supported_adapters={"~onebot.v11"},
    # 支持的适配器集合，其中 `~` 在此处代表前缀 `nonebot.adapters.`，其余适配器亦按此格式填写。
    # 若插件可以保证兼容所有适配器（即仅使用基本适配器功能）可不填写，否则应该列出插件支持的适配器。
)
driver = get_driver()
plugin_config = Config.parse_obj(driver.config)
CONFIG = get_datas()

try:
    scheduler = require("nonebot_plugin_apscheduler").scheduler
except Exception:
    scheduler = None

logger.opt(colors=True).info(
    "已检测到软依赖<y>nonebot_plugin_apscheduler</y>, <g>开启降雨预测任务功能</g>"
    if scheduler
    else "未检测到软依赖<y>nonebot_plugin_apscheduler</y>，<r>禁用降雨预测任务功能</r>"
)
# ^(?:(?:\@.*))* 用于兼容一些插件，群聊时被@,没有去掉@的那一部分
remainer_matcher = on_regex(r"^(?:(?:\@.*))*降雨预测[\s]*$", priority=999, rule=to_me())
list_matcher = on_regex(r"^(?:(?:\@.*))*降雨预测列表[\s]*(\d+)?", priority=999, rule=to_me())
list_apsjob_matcher = on_regex(r"^(?:(?:\@.*))*降雨预测jobs$", priority=999,rule=to_me())
clear_matcher = on_regex(r"^(?:(?:\@.*))*清(空|除)降雨预测$", priority=999,rule=to_me())
turn_matcher = on_regex(rf"^(?:(?:\@.*))*(查看|开启|关闭|删除|执行)降雨预测[\s]*({plugin_config.rain_forecast_id_prefix + '_'}[a-zA-Z0-9]+)$", priority=999, permission=SUPERUSER,rule=to_me())
update_matcher = on_regex(rf"^(?:(?:\@.*))*(修改|更新)降雨预测[\s]*({plugin_config.rain_forecast_id_prefix + '_'}[a-zA-Z0-9]+)$", priority=999, permission=SUPERUSER,rule=to_me())

lock = asyncio.Lock()

targetTypes: Dict[str, str] = {
    "qqGroup": TargetQQGroup(group_id=123456789).platform_type,
    "qqPrivate": TargetQQPrivate(user_id=100101).platform_type,
}

@remainer_matcher.got("position", prompt="输入需要预测的地点的经纬度:\n格式为[经度/纬度],如[114.055036/22.521530]")
@remainer_matcher.got("predTimes", prompt="选择预测的起止时间段\n格式为[开始时间/结束时间],如[8/21]，默认起止时间为8-21点")
@remainer_matcher.got("interval", prompt="请输入预测的间隔\n格式为[整数]，默认为1，单位小时")
async def remainer_handler(
    matcher: Matcher,
    event: Event,
    target: SaaTarget,
    bot: Bot,
    position: str = ArgPlainText(),
    predTimes: str = ArgPlainText(),
    interval: str = ArgPlainText(),
):
    userId = event.get_user_id()
    logger.opt(colors=True).debug(
        f"<y> token: {plugin_config.rain_forecast_token} predTimes: {predTimes} position: {position}, interval: {interval}</y>"
    )
    latitude = ''
    longitude = ''
    if position == "" or position == None:
        await sendReply("输入的经纬度格式错误", target)
        return
    if position != "" and position != None:
        position = position.split("/")
        if len(position) != 2:
            await sendReply("输入的经纬度格式错误", target)
            return
        latitude = position[0]
        longitude = position[1]
    
    predTimes = predTimes if predTimes else f'{plugin_config.rain_forecast_default_start}/{plugin_config.rain_forecast_default_end}'
    start_time, end_time = predTimes.split("/")
    if int(interval) < 1 or int(interval) > 24:
        await sendReply("输入的时间间隔格式错误，需要大于0小于24的整数", target)

    if not bot:
        sendReply(f"当前用户:{bot.self_id} 不是bot")
    try:
        res = await addScheduler(bot.self_id, target,  latitude, longitude, start_time, end_time, interval)
        logger.opt(colors=True).debug(
            f"addScheduler.res: {res}"
        )
        if res is not None and res != "" and res["code"] != 0:
            msg = Text(res['msg'])
        else:
            msg = Text("设置成功")
    except Exception as e:
        logger.exception(e)
        msg = Text("设置失败")
    
    await sendReply(msg, target)


@update_matcher.got("mtype", prompt="请输入需要修改的地方： 1. 时间段 2.经纬度 3.间隔 4.私聊对象 5.群组")
async def update_handler(
    bot: Bot,
    event: Event,
    target: SaaTarget,
    matcher: Matcher,
    state: T_State,
    args: Tuple[Optional[str], ...] = RegexGroup(),
    mtype: str = ArgPlainText()
):
    typeMap = {"1": "predTimes", "2": "position", "3": "interval", "4": "userId", "5": "groupId"}
    if not scheduler:
        await sendReply("未安装软依赖nonebot_plugin_apscheduler，不能使用降雨预测发送功能", target)
    if args[1] is None:
        await sendReply("请输入具体的id", target)
    schId = args[1]
 
    jobItem = findJobFromJSONById(schId)
    if jobItem is None:
        await sendReply("未找到该id的降雨预测提醒", target)
    
    oldValue = ""
    if mtype in ["4", "5"]:
        toTarget = buildTarget(jobItem["target"])
        logger.opt(colors=True).debug(
            f"修改发送目标 toTarget: {toTarget}"
        )
        oldValue = jobItem["target"]
    elif mtype == "1":
        oldValue = f"{jobItem['start_time']}/{jobItem['end_time']}"
    elif mtype == "2":
        oldValue = f"{jobItem['latitude']}/{jobItem['longitude']}"
    else:
        oldValue = jobItem[typeMap[mtype]]
    
    state["rain_forecast_update_old_value"] = oldValue
    state["rain_forecast_update_type"] = mtype
    state["rain_forecast_update_jobItem"] = jobItem

@update_matcher.got("newValue", prompt=MessageTemplate("请输入更新后的值，当前为: {rain_forecast_update_old_value}"))
async def update_handler2(
    bot: Bot,
    event: Event,
    target: SaaTarget,
    matcher: Matcher,
    state: T_State,
    newValue: str = ArgPlainText(),
):
    item = state["rain_forecast_update_jobItem"]
    if item is None:
        sendReply("未找到降雨预测提醒", target)
    typeMap = {"1": "predTimes", "2": "position", "3": "interval", "4": "userId", "5": "groupId"}
    mtype = state["rain_forecast_update_type"]
    if mtype in ["4", "5"]:
        if mtype == "4":
            toTarget = TargetQQPrivate(user_id=int(newValue))
        else:
            toTarget = TargetQQGroup(group_id=int(newValue))
        logger.opt(colors=True).debug(
            f"修改发送目标 toTarget: {toTarget}"
        )
        item["target"] = toTarget.dict()
    elif mtype == "1":
        times = newValue.split("/")
        if len(times) != 2:
            await sendReply("输入的经纬度格式错误", target)
            return
        start_time = times[0]
        end_time = times[1]
        item['start_time'] = start_time
        item['end_time'] = end_time
    elif mtype == "2":
        position = newValue.split("/")
        if len(position) != 2:
            await sendReply("输入的经纬度格式错误", target)
            return
        latitude = position[0]
        longitude = position[1]
        item['latitude'] = latitude
        item['longitude'] = longitude
    else:
        item[typeMap[mtype]] = newValue
    
    msg = Text("")
    res = await updateScheduler(item)
    if res is not None and res != "":
        if res["code"] != 0:
            msg += res
        else:
            msg += f"设置成功, 最新信息如下\n {item2string(item)}"
    else:
        msg += "设置成功"
    await sendReply(msg, target)

@list_matcher.handle()
async def list_matcher_handle(
    target: SaaTarget,
    args: Tuple[Optional[int], ...] = RegexGroup(),
):
    page = args[0] if len(args) > 0 and args[0] else 1
    page = int(page)
    pageSize = plugin_config.rain_forecast_page_size
    startIdx = (page - 1) * pageSize
    msg = ""
    # logger.opt(colors=True).info(
    #     f"CONFIG: {CONFIG}"
    # )
    msg += f"共计{len(CONFIG)}个降雨预测提醒 \n\
-------------------------\n"
    
    # 分页返回
    items = list(CONFIG.values())
    logger.opt(colors=True).info(
        f"<y>args:{args} startIdx: {startIdx}, len(items):{len(items)}, pageSize:{pageSize}, page:{page}</y>"
    )
    for idx in range(startIdx, len(items)):
        if idx < (page - 1) * pageSize or idx >= page * pageSize:
            break
        item = items[idx]
        
        msg += item2string(item)

    if(str(msg) == ""):
        msg += "没有降雨预测提醒"
    
    await sendReply(msg, target)

@list_apsjob_matcher.handle()
async def list_apsjob_matcher_handle(
    target: SaaTarget,
):
    msg = None
    if not scheduler:
        msg = Text("未安装软依赖nonebot_plugin_apscheduler，不能使用此功能")
    else:
        msg = Text(get_jobs_info())
    
    await sendReply(msg, target)

@clear_matcher.got("confirm", prompt="确定清除降雨预测(y|n)")
async def clear_matcher_handle(
    bot: Bot,
    event: Event,
    matcher: Matcher,
    target: SaaTarget,
    confirm: str = ArgPlainText(),
):
    # 去掉前后的空白字符
    confirm = confirm.strip().lower()
    if(confirm != "y"):
        await sendReply("取消操作",target)
        return
    
    global CONFIG
    await clearScheduler()
    CONFIG = clear_datas(CONFIG=CONFIG)
    await save_datas(CONFIG=CONFIG)
    logger.opt(colors=True).info(
        f"保存配置: {CONFIG}"
    )
    CONFIG = get_datas()
    await sendReply("已清空所有降雨预测提醒",target)

@turn_matcher.handle()
async def _(
    bot: Bot,
    target: SaaTarget,
    event: Event,
    matcher: Matcher,
    args: Tuple[Optional[str], ...] = RegexGroup(),
):
    if not scheduler:
        await sendReply("未安装软依赖nonebot_plugin_apscheduler，不能使用降雨预测发送功能", target)
    mode = args[0]
    schId = args[1] if args[1] else None
    if(not schId):
        await sendReply("请输入具体的id", target)
    
    item = findJobFromJSONById(schId)
    if item is None:
        await sendReply("未找到该id的降雨预测提醒",target)
        
    if mode == "开启":
        if item["status"] == 1:
            await sendReply("该降雨预测提醒已开启，无需重复开启",target)
        else:
            item["status"] = 1
    elif mode == "关闭":
        item["status"] = 0
        setScheduler(schId, 0)
    elif mode == "删除":
        CONFIG.pop(schId, {})
        await removeScheduler(schId)
    elif mode == "查看":
        await sendReply(item2string(item),target)
    elif mode == "执行":
        job = scheduler.get_job(schId)
        if job:
            # 添加一个job并立即执行
            current_time = datetime.now()

            # 加上 10 秒
            new_time = current_time + timedelta(seconds=10)
            job.modify(next_run_time=new_time)
            await sendReply(f"正在执行{schId}的降雨预测提醒",target)
            # new_job = scheduler.run_job(job, 'date', next_run_time=datetime.now())
                   
    await save_datas(CONFIG=CONFIG)

    # await sendReply(f"已成功{mode}{schId}的降雨预测提醒",target)

async def post_scheduler(botId: str, target_dict: Dict, latitude:str, longitude:str):
    msg = ""
    bot = None
    token = plugin_config.rain_forecast_token
    if token == "":
        logger.opt(colors=True).error(
            f"和风天气token为空"
        )
        return
    msg = await get_weather_data(latitude, longitude, token)
    try:
        bot = get_bot(self_id=botId)
    except:
        logger.opt(colors=True).error(
            f"botId: {botId} 未找到bot"
        )
        return
    
    if msg == "":
        logger.opt(colors=True).debug(
            f"执行降雨预测任务完成，两小时内无降雨"
        )
        return

    logger.opt(colors=True).debug(
        f"执行降雨预测任务完成，有降雨！发送给<y>target:{target_dict}</y>"
    )
    target = buildTarget(target_dict)
        
    await sendToReply(msg= msg, bot = bot, target=target)


async def addScheduler(botId: str, target: SaaTarget, latitude:str, longitude:str, start_time: str, end_time: str, interval: int = 1, id=None):
    if scheduler:
        logger.opt(colors=True).debug(
            f"<y>target: {target} start_time:{start_time} end_time:{end_time}</y>"
        )
        job = None
        plans = CONFIG

        useId = id if id else generateRandomId()
        target_dict = target.dict()
        times = f"{start_time}-{end_time}"
        if start_time == '0' and end_time == '24':
            times = "*"
        times = times + f"/{interval}"
            
        # 每天或工作日
        job = scheduler.add_job(
            post_scheduler, "cron", hour=times, id=useId, replace_existing=True, args=[botId, target_dict, latitude, longitude]
        )
        
        if job is not None:
            plans[job.id] = {"id": job.id, "bot":botId, "latitude":latitude, "longitude": longitude, 
                            "start_time": start_time, "end_time": end_time, \
                            "interval": interval, "target":target_dict, "status": 1}
            await save_datas(CONFIG=CONFIG)
            return {"code": 0, "msg": job.id}
            
async def setScheduler(id: str, status: int = 1):
    if scheduler and isVaildId(id):
        if(status == 0):
            scheduler.pause_job(id)
        else:
            scheduler.reschedule_job(id)
            
async def removeScheduler(id: str):
    logger.opt(colors=True).info(
        f"<g>删除降雨预测{id}</g>"
    )
    if scheduler and isVaildId(id):
        try:
            scheduler.remove_job(id)
        except Exception as e:
            logger.opt(colors=True).debug(
                f"删除降雨预测任务出错，error: {e}"
            )
async def clearScheduler():
    if scheduler:
        jobs = scheduler.get_jobs()
        if not jobs or len(jobs) == 0:
            return False
        for job in jobs:
            if isVaildId(job.id):
                scheduler.remove_job(job.id)

async def updateScheduler(item: Any):
    id = item["id"]
    botId = item["bot"]
    target = buildTarget(item["target"])
    return await addScheduler(botId, target, item["latitude"], item["longitude"], item["start_time"], item["end_time"],  item["interval"], id= id)
    
def buildTarget(target_dict: Dict):
    return PlatformTarget.deserialize(target_dict);
def generateRandomId():
    characters = string.ascii_lowercase + string.digits
    random_id = plugin_config.rain_forecast_id_prefix + '_' + ''.join(random.choices(characters, k=plugin_config.rain_forecast_id_len))
    while checkIdExit(random_id):
        random_id = plugin_config.rain_forecast_id_prefix + '_' + ''.join(random.choices(characters, k=plugin_config.rain_forecast_id_len))
    return random_id

def checkIdExit(needCheckedId: str):
    jobs = scheduler.get_jobs()
    if not jobs or len(jobs) == 0:
        return False
    for job in jobs:
        if job.id.lower() == needCheckedId.lower():
            return True
    return False
    

def findJobFromJSONById(id: str):
    if id in CONFIG:
        return CONFIG[id]
    return None

def isVaildId(id: str):
    if id is None or id == "":
        return False
    return id.lower().startswith(plugin_config.rain_forecast_id_prefix.lower())


@driver.on_startup
async def recoverFromJson():
    if CONFIG is None or len(CONFIG) < 1:
        return
    jobs = scheduler.get_jobs()
    # 判断是否已经存在计划任务，存在则说明已经初始化过了
    for job in jobs:
        if isVaildId(job.id):
            logger.opt(colors=True).info(
                f"已经初始化过了，不需要再次初始化，退出初始化任务"
            )
            return
    
    logger.opt(colors=True).info(
        f"初始化降雨预测任务，尝试从json中恢复降雨预测任务"
    )
    try:
        for key in CONFIG:    
            item = CONFIG[key]
            res = await updateScheduler(item)
            if res is not None and res != "":
                continue
            else:
                raise Exception("回复降雨预测任务：设置失败")
        logger.opt(colors=True).info(
            f"<y>初始化降雨预测任务完成</y>"
        )
        scheduler.print_jobs()
    except Exception as e:
        logger.error(f"尝试从json中恢复降雨预测任务失败，error: {e}")
        raise e

def get_jobs_info(page: int = 1):
    if scheduler:
        jobs = scheduler.get_jobs()
        pageSize = plugin_config.rain_forecast_page_size
        startIdx = (page - 1) * pageSize
        msg = f"共计{len(jobs)}个降雨预测任务\n"
        for idx in range(startIdx, len(jobs)):
            job = jobs[idx]
            if idx < (page - 1) * pageSize or idx >= page * pageSize:
                break
            if isVaildId(job.id):
                msg += "(本插件任务)"
            else:
                msg += "(非本插件任务)"
            msg += f"jobId: {job.id} \n\
trigger:{job.trigger} \n\
下次运行时间: {job.next_run_time}\n"
        return msg

async def sendReply(msg: MessageSegmentFactory, target: PlatformTarget):
    if(isinstance(msg, str)):
        msg = Text(msg) 
    if target and target.platform_type == targetTypes.get("qqGroup"):
        await msg.send(reply=True, at_sender=True)
    else:
        await msg.send()
async def sendToReply(msg: MessageSegmentFactory, bot: Bot, target: PlatformTarget, useId: str = None, messageId: str = None):
    if(isinstance(msg, str)):
        msg = Text(msg)
    if(useId is not None):
        mention = Mention(user_id=useId)
        msg = MessageFactory([msg, mention])
    if messageId is not None:
        msg = MessageFactory([msg, Reply(message_id=messageId)])
    await msg.send_to(bot=bot, target=target)