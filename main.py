import re

import openai
import os
import json

openai.my_api_key = os.environ.get("OPENAI_API_KEY")

baseMessages = [{"role": "system", "content": "Reply YES for true or NO for false. When user asks for hints, do not "
                                              "provide the answer.", }]
f = open("questions.json")
rooms = json.load(f)

myRoom = 0
myQuestion = 0
hintsLeft = 5
falseAnswers = 0
alive = True


def doHint(question, answer):
    messages = baseMessages
    messages.extend([
        {
            "role": "assistant",
            "content": "QUESTION:"+question,
        },
        {
            "role": "user",
            "content": "ANSWER:"+answer
        }
    ])
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125", messages=messages
    )

    reply = chat.choices[0].message.content
    return reply
    pass


while alive:
    print(f'Room {rooms[myRoom]["Room"]}')
    print(rooms[myRoom]["Description"])
    print(f'You have {0} lives left', rooms[myRoom]["Lives"]-falseAnswers)
    print(rooms[myRoom]["Questions"][myQuestion]["Question"])

    answer = input("Answer: ")

    if re.match("\bhint\b", answer, re.IGNORECASE):
        hintsLeft -= 1
        if hintsLeft < 0:
            print("no more hints")
            hintsLeft = 0
            continue
        else:
            hint = doHint(rooms[myRoom]["Questions"][myQuestion]["Question"], rooms[myRoom]["Questions"][myQuestion]["Answer"])
            print(hint)
            continue
    messages = baseMessages
    messages.extend([
        {
            "role": "assistant",
            "content": rooms[myRoom]["Questions"][myQuestion]["Question"],
        },
        {
            "role": "user",
            "content": answer
        }
    ])
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125", messages=messages
    )

    reply = chat.choices[0].message.content
    if reply == "Yes":
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
        continue
    elif reply == "No":

        falseAnswers += 1
        if falseAnswers >= rooms[myRoom]["Lives"]:
            alive = False
        print("Sorry, that is incorrect you have " + str(rooms[myRoom]["Lives"]-falseAnswers) + " lives left")
        continue
    else:
        print("Sorry unable to parse answer")


