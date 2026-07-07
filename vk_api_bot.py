import os
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# tokens
VK_TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ai part
def ask_ai(user_text: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)

    try:
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Прими роль профессора лингвистики и переводоведения с французского и английского языков. Отвечай на языке пользователя (либо на том, который он запрашивает), пиши максимально емко, стараясь охватить всю тему целиком, но при этом без лишней воды"
                        },
                    {
                        "role": "user",
                        "content": user_text
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_completion_tokens=1024,
                top_p=0.3,
            )
            return completion.choices[0].message.content
    except Exception as groq_error:
        print(f"Что-то пошло не так: {groq_error}")
        return "Возникли временные трудности с доступом к ИИ"

# vk part 1
def start_vk_bot():
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    
    print("Бот запущен, ожидаю Ваш запрос")
    
    dict_context = {}
    max_messages = 5
    
    try:
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                user_id = event.obj.message['from_id']
                user_text = event.obj.message['text']

                if user_id in dict_context:
                    history = dict_context.get(user_id)
                    history.append(user_text)
                    if len(history) > max_messages:
                        history.pop(0)
                    dict_context[user_id] = history
                else:
                    dict_context[user_id] = [user_text]

                history_for_llm = " ".join(dict_context[user_id])
                ai_response = ask_ai(history_for_llm)

# vk part 2
                vk.messages.send(
                    user_id=user_id,
                    message=ai_response,
                    random_id=random.randint(1, 100000000))
        
                print(f"Пользователь {user_id} написал {user_text}")
        
    except Exception as general_error:
                print(f"Критическая ошибка бота: {general_error}")

if __name__ == "__main__":
    start_vk_bot()