from ..deepseek_api import DeepSeekClient
import json

def analyze_tb(tb):
    ds = DeepSeekClient()
    tb_json = json.dumps(tb, ensure_ascii=False)
    return ds.analyze_trial_balance(tb_json)
