from pydantic import BaseModel

class Config(BaseModel):
    # 和风天气token
    rain_forecast_token:str = ""
    # 默认开始预测时间
    rain_forecast_default_start: int = 0
    # 默认开始预测时间
    rain_forecast_default_end: int = 24
    # 默认预测间隔(小时)
    rain_forecast_default_interval: int = 1
    # 底层任务id长度
    rain_forecast_id_len:int = 5
    # 底层任务id的前缀
    rain_forecast_id_prefix:str = "rain_forecast"
    # 列出任务时，每次列出的条目数
    rain_forecast_page_size:int = 5
    # 最多有几个备份
    rain_forecast_bk_size:int = 2

    class Config:
        extra = "ignore"
        case_sensitive = False