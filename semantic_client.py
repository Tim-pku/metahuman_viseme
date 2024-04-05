import requests
import json
import multiprocessing


def samantic(input):
    # 构建post请求参数

    try:
        response = requests.post('http://127.0.0.1:8010/semantic/{}'.format(input))
        print(response.json())
        
        if response.status_code == 200:
           
            return response.json() 
        else:
            return "Failed to get a valid response."
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    input="今天的电影全程无聊"
    samantic(input)
