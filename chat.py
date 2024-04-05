from asyncio import QueueEmpty
import numpy as np
from faulthandler import cancel_dump_traceback_later

import threading
import queue

from inflect import Word
from pyparsing import Empty
import requests
import re

from openai import OpenAI
from sympy import Max
from infer import infer, get_net_g, get_net_Viseme
from config import config
from tools.translate import translate
from motion import const_map
from motion import live_link
from common.log import logger



sentence_queue = queue.Queue()

fps = 86.1328125
delay_ms = 110
extra_bat = 'extra.bat'
add_blink = False
can_play = False
reply_id = 1


"""    Openai    """

origin_model_conversation = [
                                {"role": "system", "content": "你是用户user的好朋友，能够和user进行愉快的交谈，你的名字叫Tim."}
                            ]

def chat_with_origin_model(text):
        openai_api_key = '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'
        openai = OpenAI(api_key=openai_api_key)

        text = text.replace('\n', ' ').replace('\r', '').strip()
        if len(text) == 0:
            return
        print(f'chatGPT Q:{text}')
        origin_model_conversation.append({"role": "user", "content": text})
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            # model="gpt-4",
            messages=origin_model_conversation,
            max_tokens=512,
            temperature=0.7,
            stream= True
        )
        global reply_id
        reply =''
        ass_reply= ''
        for chunk in response:
            word = str(chunk.choices[0].delta.get('content'))
            ass_reply += word
            match = re.findall(r'。', word)
            if match == list('。'):
                word_ends = word.split("。")
                reply =reply + str(word_ends[0]) + '。'
                # queue_data = [reply_id,reply]
                sentence_queue.put((reply_id,reply))
                print(f'sentence_queue:{(reply_id,reply)}')
                reply =''
            else:
                reply += word
        
        origin_model_conversation.append({"role": "assistant", "content": ass_reply})
    
        # reply = response.choices[0].message.content
        # self.origin_model_conversation.append({"role": "assistant", "content": reply})
        # return reply


"""   sparkapi      """
from spark_chat import SparkChat
#以下密钥信息从控制台获取
appid = "3e721689"     #填写控制台中获取的 APPID 信息
api_secret = "NTBlNjNkNzgzZTgwZjk0OWE5OTFmMzIx"   #填写控制台中获取的 APISecret 信息
api_key ="9696bebc63a45edb02dec6872e6b218f"    #填写控制台中获取的 APIKey 信息

#用于配置大模型版本，默认“general/generalv2”
# domain = "generalv3.5"   # v3.5版本
domain = "generalv2"    # v2.0版本
#云端环境的服务地址
# Spark_url = "ws://spark-api.xf-yun.com/v3.5/chat"  # v3.5环境的地址
Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址

lyw_spark = SparkChat(appid,api_key,api_secret,Spark_url,domain)



def getText(role,content):
    text = []
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text

def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    while (getlength(text) > 8000):
        del text[0]
    return text

def chat_with_spark(text):
    
    origin_model_conversation = []
    
    # text = text.replace('\n', ' ').replace('\r', '').strip()
    if len(text) == 0:
        return
    print(f'chatGPT Q:{text}')
    # origin_model_conversation.append({"role": "user", "content": text})
    question = checklen(getText("user", text))
    responses = lyw_spark.chatCompletionStream(question, temperature= 0.7, max_tokens=512)

    global reply_id
    reply = ''
    ass_reply = ''
    for chunk in responses:
        # data_str = json.loads(chunk)
        # word = data_str['choices'][0]['delta']['content']
        word = chunk
        word = word.replace('\n', ' ').replace('\r', '').strip()
        ass_reply += word
        # print((word))
        # if word is None:
        #     time_ver = datetime.datetime.now() + datetime.timedelta(seconds=5)
        # if time_ver <datetime.datetime.now():
        match = re.findall(r'。', word)
        if match == list('。'):
            word_ends = word.split("。")
            
            reply = reply + str(word_ends[0]) + "。"
            sentence_queue.put((reply_id,reply))
            print(f'prod:{(reply_id,reply)}')
            reply = ''
            reply_id +=1
            reply += str(word_ends[1])
        else:
            reply += word
    reply_id = 1
    # origin_model_conversation.append({"role": "assistant", "content": ass_reply})

    # reply = response.choices[0].message.content
    # self.origin_model_conversation.append({"role": "assistant", "content": reply})
    # return reply




"""     chatGLM3    """

from openai import OpenAI

base_url = "http://127.0.0.1:8080/v1/"
client = OpenAI(api_key="EMPTY", base_url=base_url)


def chat_with_GLM3(text):
    origin_model_conversation = [
        {
            "role": "system",
            "content": "你是一个微表情机器人，是由李孟伟人工智能团队开发的实验平台。 "
                       "可以使用特殊的语气和表情驱动机器人做动作",
        }
    ]
    if len(text) == 0:
        return
    print(f'chatGLM3 Q:{text}')
    origin_model_conversation.append({"role": "user", "content": text})

    use_stream=True
    reply = ''
    ass_reply = ''
    global reply_id
    reply_id = 1
    responses = client.chat.completions.create(
        model="chatglm3-6b",
        messages=origin_model_conversation,
        stream=use_stream,
        max_tokens=512,
        temperature=0.6,
        presence_penalty=1.1,
        top_p=0.8)
    if responses:
        if use_stream:
            for chunk in responses:
                # print(chunk.choices[0].delta.content)
                word = chunk.choices[0].delta.content
                word = word.replace('\n', ' ').replace('\r', '').strip()
                ass_reply += word
                match = re.findall(r'。', word)
                if match == list('。'):
                    word_ends = word.split("。")
                    reply = reply + str(word_ends[0]) + "。"
                    sentence_queue.put((reply_id,reply))
                    print(f'prod:{(reply_id,reply)}')
                    reply = ''
                    reply_id +=1
                    reply += str(word_ends[1])
                else:
                    reply += word
            reply_id = 1
                               
        else:
            content = responses.choices[0].message.content
            print(content)
    else:
        print("Error:", responses.status_code)
    # origin_model_conversation.append({"role": "assistant", "content": ass_reply})
    # print(origin_model_conversation)


"""   Baidu   

执行如下命令，快速安装Python语言的最新版本ERNIE Bot SDK（推荐Python >= 3.8)。

pip install --upgrade erniebot
如果希望自源码安装，可以执行如下命令：

git clone https://github.com/PaddlePaddle/ERNIE-Bot-SDK
cd ERNIE-Bot-SDK
pip install .


"""
import erniebot


def chat_with_baidu(text):
    erniebot.api_type = "aistudio"
    erniebot.access_token = "2dbea1783e549b5c0f900eda1c43d8cfcdb454fc"

    stream = True
    response = erniebot.ChatCompletion.create(
        model="ernie-3.5",
        messages=[{
            "role": "user",
            "content": text
        }],
        top_p=0.95,
        stream=stream)

    result = ""
    reply = ''
    ass_reply = ''
    global reply_id
    if stream:
        for res in response:
            # print(res)
            word = res.result
            word = word.replace('\n',' ').replace('\r', '').strip()
            result += res.result
            
            match = re.findall(r'。', word)
            if match == list('。'):
                word_ends = word.split("。")
                reply = reply + str(word_ends[0]) + "。"  #reply total sentenc for queue
                # match = re.findall(r'，', reply)
                # if match == list('，'):
                #     word_dot = reply.split(" ，")
                #     reply = str(word_dot[0]) + ","

                sentence_queue.put((reply_id,reply))
                print(f'prod:{(reply_id,reply)}')
                reply = ''
                reply_id +=1
                reply += str(word_ends[1])
                # else:
                #     sentence_queue.put((reply_id,reply))
                #     print(f'prod:{(reply_id,reply)}')
                #     reply = ''
                #     reply_id +=1
                #     reply += str(word_ends[1]) 
            else:
                reply += word         
            
    else:
        result = response.result

    print("ERNIEBOT: ", result)


"""     viseme cli   """
import time
def gen_sound(text):
    payload = {'id': 0, 'text': text}
    response = requests.post('http://127.0.0.1:8000/viseme/',json=payload)
    if response.status_code == 200:
        print("gen_viseme:", 0)
        global can_play
        can_play = True
        print(can_play)

gen_vis_queue = queue.Queue()

def gen_viseme():
    # 构建post请求参数

    while True:
        text_id, text = sentence_queue.get()
        payload = {'id': text_id, 'text': text}
        response = requests.post(f'http://127.0.0.1:8000/viseme/', json=payload)
        # print(response.json())
        # wav_data, bs_vis = response.json()
        if response.status_code == 200:
            print("gen_viseme:", text_id)
            global can_play
            can_play = True
            print(can_play)
            # return wav_data, bs_vis
            # gen_vis_queue.put((id, wav_data, bs_vis))
        else:
            return "Failed to get a valid response."
        if sentence_queue.empty():
            break
      

"""     Qwen1.5    """

from openai import OpenAI

client_qwen = OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama',  # required but ignored
)


def chat_with_QWEN(text):
    origin_model_conversation = [
        {
            "role": "system",
            "content": "你是一个微表情机器人，是由李孟伟人工智能团队开发的实验平台。 "
                       "可以使用特殊的语气和表情驱动机器人做动作",
        }
    ]
    if len(text) == 0:
        return
    print(f'Qwen Q:{text}')
    origin_model_conversation.append({"role": "user", "content": text})

    use_stream=True
    reply = ''
    ass_reply = ''
    global reply_id
    reply_id = 1
    responses = client_qwen.chat.completions.create(
        model="qwen:0.5b",
        messages=origin_model_conversation,
        stream=use_stream,
        # max_tokens=512,
        # temperature=0.8,
        # presence_penalty=1.1,
        # top_p=0.8
        )
    if responses:
        if use_stream:
            for chunk in responses:
                # print(chunk.choices[0].delta.content)
                word = str(chunk.choices[0].delta.content)
                word = word.replace('None', '').replace('\n', ' ').replace('\r', '').strip()
                ass_reply += word
                match = re.findall(r'。', word)
                if match == list('。'):
                    word_ends = word.split("。")
                    reply = reply + str(word_ends[0]) + "。"
                    sentence_queue.put((reply_id,reply))
                    print(f'prod:{(reply_id,reply)}')
                    reply = ''
                    reply_id +=1
                    reply += str(word_ends[1])
                else:
                    reply += word
            reply_id = 1
                               
        else:
            content = responses.choices[0].message.content
            sentence_queue.put((reply_id,content))
            print(content)
    else:
        print("Error:", responses.status_code)
    # origin_model_conversation.append({"role": "assistant", "content": ass_reply})
    # print(origin_model_conversation)               

# gen_vis_queue_dual = queue.Queue()
# def gen_viseme1():
#     # 构建post请求参数

#     while True:
#         try:
#             text_id, text = sentence_queue_dual.get(block= True,timeout=5)
#             payload = {'id': text_id, 'text': text}
#             response = requests.post(f'http://127.0.0.1:8001/viseme/', json= payload)
#             # print(response.json())
#             # wav_data, bs_vis = response.json()
#             if response.status_code == 200:
#                 print("gen_viseme1:", text_id)
#                 global can_play
#                 can_play = True
#                 print(can_play) 
#                 # return wav_data, bs_vis
#                 # gen_vis_queue.put((id, wav_data, bs_vis))
#             else:
#                 return "Failed to get a valid response."
#         except QueueEmpty:
#             break


# gen_vis_queue2 = queue.Queue()
# def gen_viseme2(consume_data):
#     # 构建post请求参数
    
#     response = requests.post('http://127.0.0.1:8002/viseme/{}'.format(consume_data))
#     print(response.json())
#     consume_id, wav_data, bs_vis = response.json()
#     if response.status_code == 200:
#         gen_vis_queue2.put((consume_id, wav_data, bs_vis))
#     else:
#         return "Failed to get a valid response."
       


# """ sent wav&viseme """
# udp_sender = live_link.UdpSender([[
# 				"192.168.0.17",
# 				11111
# 			]])# Local
# udp_sender1 = live_link.UdpSender([[
# 				"192.168.1.14",
# 				11111
# 			]])# home

# udp_sender2 = live_link.UdpSender([[
# 				"192.168.0.242",
# 				9998
# 			]])


# def play_wav_binary(data):
#     # 将二进制数据转换为文件对象
#     f = io.BytesIO(data)
#     # 用wave模块打开文件对象
#     wf = wave.open(f, 'rb')
#     # 创建pyaudio对象
#     p = pyaudio.PyAudio()
#     # 打开音频流
#     stream = p.open(
#         format=p.get_format_from_width(wf.getsampwidth()),
#         channels=wf.getnchannels(),
#         rate=wf.getframerate(),
#         output=True
#     )
#     # 读取数据并播放
#     chunk = 1024
#     data = wf.readframes(chunk)
#     while data:
#         stream.write(data)
#         data = wf.readframes(chunk)
#     # 关闭音频流和pyaudio对象
#     stream.stop_stream()
#     stream.close()
#     p.terminate()


# # fps: frames per second
# def send_frames(udp_sender, visemes, fps = 86.1328125):
#     import time
#     # get current time in ms
#     start_time = int(time.time() * 1000) + delay_ms
#     # for ever loop
#     send_count = 0
#     while True:
#         time_should_send = int(start_time + send_count * 1000 / fps)
#         time_now = int(time.time() * 1000)
#         if time_now < time_should_send:
#             time.sleep((time_should_send - time_now) / 1000)
#             continue
#         if send_count % 100 == 0:
#             print('send frame', send_count)
#         udp_sender.send(visemes[send_count])
#         if send_count >= len(visemes) - 1:
#             print('send last frame')
#             udp_sender.send(visemes[send_count])
#             break
#         send_count += 1


# def start_send_frames(udp_sender, visemes, fps):
#     # new thread
#     import threading
#     t = threading.Thread(target=send_frames, args=(udp_sender, visemes, fps))
#     # t1 = threading.Thread(target=send_frames, args=(udp_sender1, visemes, fps))
#     # t2 = threading.Thread(target=send_frames, args=(udp_sender2, visemes, fps))
#     t.daemon = True
#     # t1.daemon = True
#     # t2.daemon = True
#     t.start()
#     # t1.start()
#     # t2.start()
#     return t


# def play_and_send(udp_sender, bs_npy_file, wav_file, fps):
#     # read bs_value_1114_3_16.npy file
#     bs = np.load(bs_npy_file, allow_pickle=True)
#     # bs: (1200, 61)
#     print('bs.shape', bs.shape, 'fps', fps)
#     bs_arkit = const_map.map_arkit_values(bs, add_blink, fps)
#     # print('remap done')

#     # read file_path to binary buffer
#     print('send & playing wav', wav_file)
#     with open(wav_file, 'rb') as f:
#         data = f.read()
#         # t1 = start_extra(extra_bat, 500)
#         t2 = start_send_frames(udp_sender, bs_arkit, fps)

#         play_wav_binary(data)

#         #wait t1 t2
#         # t1.join()
#         t2.join()

# def thread_play_vis():
#     global can_play
#     global reply_id

#     i =0
#     while True:
    
#         file_name = 'temp'+ str(i+1)
#         if os.path.isfile(f'{file_name}.npy'):
#             play_and_send(udp_sender,f'{file_name}.npy',f'{file_name}.wav',fps=fps)
#             os.remove(f'{file_name}.npy')
#             os.remove(f'{file_name}.wav')
#             i +=1
#         # can_play = False
#         # print(can_play)



def thread_gen_viseme(text):
    # prod_thread = threading.Thread(target= chat_with_origin_model,args=(text,))
    # prod_thread = threading.Thread(target= chat_with_spark,args=(text,))
    # prod_thread = threading.Thread(target= chat_with_GLM3,args=(text,))
    # prod_thread = threading.Thread(target= chat_with_QWEN,args=(text,))
    prod_thread = threading.Thread(target= chat_with_baidu,args=(text,))
    # prod_thread.daemon = True
    prod_thread.start()

    consu_thread = threading.Thread(target= gen_viseme,args=())
    # consu_thread.daemon = True
    consu_thread.start()

    # consu_thread1 = threading.Thread(target= gen_viseme1,args=())
    # # consu_thread1.daemon = True
    # consu_thread1.start()
    
    # play_thread = threading.Thread(target= thread_play_vis,args=())
    # # play_thread.daemon = True
    # play_thread.start()

    prod_thread.join()
    consu_thread.join()


 
    

if __name__ == '__main__':
    text = "讲一个神话故事"
    thread_gen_viseme(text)
    # text = "一条长长的鼻子，一双大大的耳朵。我喜欢吃草，喝水，洗澡。你喜欢大象吗？"
    # gen_sound(text)






        
