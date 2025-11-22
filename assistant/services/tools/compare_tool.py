from ..deepseek_api import DeepSeekClient
import json

def compare_two_tbs(tb1, tb2):
    ds = DeepSeekClient()
    tb1_json = json.dumps(tb1, ensure_ascii=False)
    tb2_json = json.dumps(tb2, ensure_ascii=False)
    return ds.compare_two_tbs(tb1_json, tb2_json)
