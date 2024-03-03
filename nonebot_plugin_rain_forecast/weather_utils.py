from httpx import AsyncClient, Response
from nonebot.log import logger
import json
url_minute_api = "https://devapi.qweather.com/v7/minutely/5m"
class APIError(Exception):
    ...
async def get_weather_data(jd,wd,token) -> Response:
    params={"location": f"{jd},{wd}", "key": token}
    res = await _get_data(url_minute_api, params)
    _check_response(res)
    res = res.json()
    logger.debug(res)
    if('summary' not in res):
        raise APIError("No summary in response")
    summary: str = res['summary']
    
    # # 防止出现summary中说无降水但却有降水的情况
    # if summary.find('无降水') > 0 and 'minutely' in res:
    #     minutely = res['minutely']
    #     for item in minutely:
    #         if item['type'] == 'rain' and float(item['precip']) > 0.001:
    #             return f"有降水，时间为 {item['fxTime']}"
    
    if summary.find('无降水') < 0:
        return res['summary']
    return ""
    
async def _get_data( url: str, params: dict) -> Response:
    async with AsyncClient() as client:
        res = await client.get(url, params=params)
    return res

def _check_response(response: Response) -> bool:
    if response.status_code == 200:
        return True
    else:
        raise APIError(f"Response code:{response.status_code}")