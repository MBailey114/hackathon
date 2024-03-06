import json
import os
import re
import time

from colorama import Fore, Back, Style

import openai

clear = lambda: os.system('clear')

baseMessages = [{"role": "system",
                 "content": "can you explicitly reply YES for true or NO for false. Only replying with YES or NO to the question.", }]
hintMessages = [{"role": "system", "content": " When user asks for a hint, do not provide the answer.", }]
f = open("questions.json")
rooms = json.load(f)
rooms = rooms["rooms"]

myRoom = 0
myQuestion = 0
hintsLeft = 5
falseAnswers = 0
alive = True
new_room = True


def do_hint(question, question_answer):
    hint_messages = hintMessages.copy()
    hint_messages.extend([
        {
            "role": "assistant",
            "content": "QUESTION:" + question,
        },
        {
            "role": "user",
            "content": "ANSWER:" + question_answer
        },
        {
            "role": "user",
            "content": "Can you give me a hint please?"
        },
    ])

    return getPoodleResponse(hint_messages)


def getPoodleResponse(query_messages):
    openai.my_api_key = os.environ.get("OPENAI_API_KEY")

    #pprint(query_messages)

    chat = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125", messages=query_messages
    )

    return chat.choices[0].message.content


def print_room(room_number):
    clear()
    print(Fore.BLUE+Style.BRIGHT+f'Room {rooms[myRoom]["Room"]}')
    print(Style.NORMAL+rooms[myRoom]["Description"])
    print(Fore.CYAN+Style.BRIGHT+f"Question {(myQuestion+1)} of {(len(rooms[myRoom]['Questions']))}")
    print(Fore.LIGHTMAGENTA_EX+Style.NORMAL+f'You have {(rooms[myRoom]["Lives"] - falseAnswers)} lives left' )
    print(Back.YELLOW+Fore.LIGHTGREEN_EX+Style.BRIGHT+rooms[myRoom]["Questions"][myQuestion]["Question"])
    print(Style.RESET_ALL)

def read_input():
    print("Answer: ")
    a = []
    for line in iter(input, ''):
        a.append(line)
    return a

while alive:
    if new_room:
        print_room(myRoom)
        new_room = False

    ans = read_input()
    answer = '\n'.join(ans)

    if re.match(".*hint.*", answer, re.IGNORECASE):
        #print("doing hint")
        hintsLeft -= 1
        if hintsLeft < 0:
            print("no more hints")
            hintsLeft = 0
            continue
        else:
            hint = do_hint(rooms[myRoom]["Questions"][myQuestion]["Question"],
                           rooms[myRoom]["Questions"][myQuestion]["Answer"])
            print(hint)
            continue

    messages = baseMessages.copy()
    #print("base: " + str(messages) + "::")
    messages.extend([
        {
            "role": "assistant",
            "content": rooms[myRoom]["Questions"][myQuestion]["Question"] + ". The answer is " + rooms[myRoom]["Questions"][myQuestion]["Answer"]
        },
        {
            "role": "user",
            "content": answer
        }
    ])

    reply = getPoodleResponse(messages)
    if re.match("YES", reply, re.IGNORECASE):
        print(Fore.GREEN+"The answer is correct")
        new_room = True
        myQuestion += 1
        if myQuestion >= len(rooms[myRoom]["Questions"]):
            myQuestion = 0
            myRoom += 1
            falseAnswers = 0
            if myRoom >= len(rooms):
                alive = False
            else:
                print(f'moving to room {rooms[myRoom]["Room"]}', )
        else:
            print("Moving on to the next question")
        time.sleep(2.0)
        continue
    elif re.match("NO", reply, re.IGNORECASE):
        falseAnswers += 1
        if falseAnswers >= rooms[myRoom]["Lives"]:
            alive = False
        print(Fore.RED+Style.BRIGHT+"Sorry, that is incorrect you have " + str(rooms[myRoom]["Lives"] - falseAnswers) + " lives left")
        print(Style.RESET_ALL)
        time.sleep(2.0)
        continue
    else:
        print("Sorry unable to parse your answer ")

