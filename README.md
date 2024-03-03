<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-rain-forecast

_✨ NoneBot 插件简单描述 ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/velor2012/nonebot-plugin-rain-forecast.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-rain-forecast">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-rain-forecast.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

这是一个 nonebot2 插件库, 主要用来预测指定位置是否有降雨，提醒大家平日带伞之类的，依赖于nonebot-plugin-send-anything-anywhere，理论上支持大部分平台，但目前只测试过onebot.v11。


## 指令

- `降雨预测`设置降雨提醒
- `降雨预测列表 [page]`: 列出设置的降雨提醒
- `清空/清除降雨预测 `: 清空所有降雨提醒
- `查看/删除/开启/关闭/执行降雨预测 [id]` : 查看/删除/开启/关闭指定id的降雨预测任务
- `降雨预测jobs [page]`: 列出底层任务情况(debug使用)
- `更新/修改降雨预测 [id]`: 修改降雨预测任务的一些设置

## 配置项

配置方式：直接在 NoneBot 全局配置文件中按需添加以下配置项即可。

NoneBot 配置相关教程详见 [配置 | NoneBot](https://v2.nonebot.dev/docs/tutorial/configuration)


### rain_forecast_token
- 类型: str
- 说明：和风天气api的token请在此处获取：https://dev.qweather.com/
- 默认: ""
>```python
>RAIN_FORCAST_TOKEN=""
>```

### rain_forecast_default_start
- 类型: int
- 说明：需要预测降雨的时间段的开始时间
- 默认: 0
>```python
>RAIN_FORCAST_DEFAULT_START=0
>```

### rain_forecast_default_end
- 类型: int
- 说明：需要预测降雨的时间段的结束时间
- 默认: 24
>```python
>RAIN_FORCAST_DEFAULT_END=24
>```

### rain_forecast_default_interval
- 类型: int
- 说明：需要预测降雨的时间间隔，默认每小时调用一次接口来预测
- 默认: 1
>```python
>RAIN_FORCAST_DEFAULT_INTERVAL=1
>```

### rain_forecast_id_len
- 类型: int
- 说明：底层任务id的长度（不包括前缀）
- 默认: 5
>```python
>RAIN_FORCAST_ID_LEN=5
>```

### rain_forecast_id_prefix
- 类型: int
- 说明：底层任务id的前缀
- 默认: "rain_forecast"
>```python
>RAIN_FORCAST_ID_PREFIX="rain_forecast"
>```

### rain_forecast_page_size
- 类型: str
- 说明：列出任务时，每次列出的条目数
- 默认: 0
>```python
>RAIN_FORCAST_PAGE_SIZE=5
>```

### rain_forecast_bk_size
- 类型: str
- 说明：最多有几个备份
- 默认: 0
>```python
>RAIN_FORCAST_BK__SIZE=5
>```

## 依赖
- [`nonebot-plugin-apscheduler`](https://github.com/nonebot/plugin-apscheduler): 使用定时发送功能
- [`nonebot-plugin-localstore`](https://github.com/nonebot/plugin-localstore): 使用存储功能
- [`nonebot-plugin-send-anything-anywhere`](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere): 使用跨平台发送消息功能
## 致谢

代码基于 [nonebot-plugin-everyday-en](https://github.com/MelodyYuuka/nonebot_plugin_everyday_en)，感谢原作者的开源精神！

## 其他
修改定时的时候，私聊对象和群组只能二选一。

## 开源许可

- 本插件使用 `MIT` 许可证开源