from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from fastapi import FastAPI
from pydantic import BaseModel

semantic_cls = pipeline(Tasks.text_classification, './nlp_structbert_emotion-classification_chinese-large', model_revision='v1.0.0')

app=FastAPI()

"""

Emotion_dict =
{
 "恐惧": [4,10],
 "愤怒": [5,6],
 "厌恶": [3,6],
 "喜好": [0,10],
 "悲伤": [1,10],
 "高兴": [6,4],
 "惊讶": [7,10]
}


   "Neutral": 0,12
      "Sad": 1,12
      "Normal": 2,12
      "Disgust": 3,12
      "Fear": 4,12
      "Anger": 5,8
      "Happy": 6,6
      "Surprise": 7,12 

      
"""
Emotion_dict ={
 "恐惧": [4,10],
 "愤怒": [5,6],
 "厌恶": [3,6],
 "喜好": [0,10],
 "悲伤": [1,10],
 "高兴": [6,6],
 "惊讶": [7,10]
}
class Item_emo(BaseModel):
    text: str
    name: str

@app.post('/semantic/')
def semantic_class(item: Item_emo):
    input = item.text
    res = semantic_cls(input)
    # num=res.index(max(res['scores']))
    emotion_num = res['scores'].index(max(res['scores']))
    emotion = res['labels'][emotion_num]
    print(emotion)

    style_id,style_value = Emotion_dict[emotion]
    print(style_id)
    print(style_value)

    return style_id,style_value

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010) 