import re
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
        model="qwen:4b",
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
                word = str(chunk.choices[0].delta.content)
                word = word.replace('None', '').replace('\n', ' ').replace('\r', '').strip()
                ass_reply += word
                match = re.findall(r'。', word)
                if match == list('。'):
                    word_ends = word.split("。")
                    reply = reply + str(word_ends[0]) + "。"
                    # sentence_queue.put((reply_id,reply))
                    print(f'prod:{(reply_id,reply)}')
                    reply = ''
                    reply_id +=1
                    reply += str(word_ends[1])
                else:
                    reply += word
            reply_id = 1
                               
        else:
            content = responses.choices[0].message.content
            # sentence_queue.put((reply_id,content))
            print(content)
    else:
        print("Error:", responses.status_code)
    origin_model_conversation.append({"role": "assistant", "content": ass_reply})
    # print(origin_model_conversation)   

if __name__ == '__main__':
    text = "你有什么特长？"
    # thread_gen_viseme(text)
    chat_with_QWEN(text)
