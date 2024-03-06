import os
import json
import asyncio
from openai import AsyncOpenAI
from colorama import init, Fore, Back, Style

init()  # Initialize colorama for colored terminal output

client = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # Initialize the OpenAI client with your API key
)

def load_rooms(filename: str) -> list:
    """
    Loads room data from a JSON file.

    Parameters:
    - filename (str): The path to the JSON file containing room data.

    Returns:
    - list: A list of dictionaries, each representing a room's data.
    """
    with open(filename, 'r') as file:
        data = json.load(file)
    return data['rooms']

async def ask_question(room_number: int, question_number: int, question: str, expected_answer: str, hint_count: int, max_hints: int, previous_hints: list, lives: int) -> (bool, int, list):
    """
    Asynchronously asks a question, processes the user's answer or hint request, and validates the answer.

    Parameters:
    - room_number (int): The current room number.
    - question_number (int): The current question number within the room.
    - question (str): The question to be asked.
    - expected_answer (str): The correct answer to the question.
    - hint_count (int): The current count of hints provided for this question.
    - max_hints (int): The maximum number of hints allowed for this question.
    - previous_hints (list): A list of hints that have already been provided for this question.
    - lives (int): The current number of lives the user has.

    Returns:
    - tuple: A tuple containing a boolean indicating whether the answer was correct, the updated hint count, and the updated list of previous hints.
    """
    # Display the question
    print(Back.BLUE + Fore.WHITE + Style.BRIGHT + f"\n📚 QUESTION {question_number} in Room {room_number}: {question} 📚\n" + Style.RESET_ALL + "\n" * 2)

    while True:
        user_answer = input(Style.BRIGHT + "Your answer (or type 'HINT' for a hint): " + Style.RESET_ALL)

        if user_answer.strip().lower() == 'hint':
            if hint_count >= max_hints:
                print(Back.WHITE + Fore.RED + Style.BRIGHT + "⚠️ Error: Maximum hint limit reached for this room. ⚠️" + Style.RESET_ALL + "\n" * 2)
                continue  # Allow the user to answer the question if max hints reached
            hint_count += 1  # Increment hint count

            try:
                # Prepare the messages for the OpenAI API call, including previous hints to avoid repetition
                messages = [
                    {
                        "role": "system",
                        "content": "Provide a hint for the question without revealing the answer directly. Make sure no hint is the same.",
                    },
                    {
                        "role": "assistant",
                        "content": f"QUESTION: {question}",
                    },
                    {
                        "role": "assistant",
                        "content": f"CORRECT ANSWER: {expected_answer}",
                    }
                ]
                # Add previous hints to the messages
                for hint in previous_hints:
                    messages.append({
                        "role": "assistant",
                        "content": f"HINT: {hint}",
                    })
                messages.append({
                    "role": "user",
                    "content": "Give me a hint",
                })
                
                # Request a hint from the OpenAI API
                hint_completion = await client.chat.completions.create(
                    messages=messages,
                    model="gpt-3.5-turbo-0125",
                )
                hint_content = hint_completion.choices[0].message.content
                previous_hints.append(hint_content)  # Remember this hint
                # Display the hint
                print(Back.YELLOW + Fore.BLACK + Style.BRIGHT + f"💡 HINT {hint_count}: {hint_content} 💡" + Style.RESET_ALL + "\n" * 2)
            except Exception as e:
                print(Fore.RED + f"An error occurred while generating a hint: {e}" + Style.RESET_ALL)
        else:
            break  # Exit the loop if the user provides an answer instead of requesting a hint

    try:
        # Validate the user's answer using the OpenAI API
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "This is a question and answer validation system. Reply YES if the user's answer is correct, otherwise reply NO.",
                },
                {
                    "role": "assistant",
                    "content": f"QUESTION: {question}",
                },
                {
                    "role": "assistant",
                    "content": f"CORRECT ANSWER: {expected_answer}",
                },
                {
                    "role": "user",
                    "content": user_answer,
                },
            ],
            model="gpt-3.5-turbo-0125",
        )
        completion_content = chat_completion.choices[0].message.content
        if "YES" in completion_content:
            # If the answer is correct, congratulate the user
            print("\n" + Back.BLACK + Fore.GREEN + Style.BRIGHT + "✨ Correct! Well done! ✨\n" + Style.RESET_ALL + "\n" * 3)
            return True, hint_count, previous_hints
        else:
            # If the answer is incorrect, prompt the user to try again if they have lives remaining
            if lives > 1:
                print(Fore.RED + "Incorrect! Please try again." + Style.RESET_ALL + "\n" * 2)
            return False, hint_count, previous_hints
    except Exception as e:
        print(Fore.RED + f"An error occurred while validating the answer: {e}" + Style.RESET_ALL)
        return False, hint_count, previous_hints

async def run_quiz(rooms: list):
    """
    Asynchronously runs the quiz by iterating through each room and its questions.

    Parameters:
    - rooms (list): A list of room dictionaries loaded from the JSON file.

    This function does not return anything but prints the quiz progress, results, and final messages to the console.
    """
    for room_index, room in enumerate(rooms, start=1):
        print(Back.MAGENTA + Fore.YELLOW + Style.BRIGHT + f"\n🚪 Entering Room {room_index}: {room['Description']} 🚪\n" + Style.RESET_ALL + "\n" * 2)

        lives = room["Lives"]
        max_hints = room["HintsAllowed"]
        previous_hints = []  # Reset previous hints for each room

        for question_index, question_info in enumerate(room["Questions"], start=1):
            hint_count = 0
            correct = False
            while not correct and lives > 0:
                question = question_info["Question"]
                answer = question_info["Answer"]

                # Call ask_question with all necessary parameters, including the current room and question numbers
                correct, hint_count, previous_hints = await ask_question(room_index, question_index, question, answer, hint_count, max_hints, previous_hints, lives)

                if not correct:
                    lives -= 1
                    if lives <= 0:
                        # If the user runs out of lives, print the game over message
                        print(Back.RED + Fore.WHITE + Style.BRIGHT + "\n💀 Game Over! You've run out of lives. 💀\n" + Style.RESET_ALL)
                        return
                    else:
                        # If the user has lives remaining, print the number of lives left
                        print(Back.BLACK + Fore.RED + Style.BRIGHT + f"❌ Lives remaining: {lives} ❌" + Style.RESET_ALL + "\n" * 2)

    # If the user completes all rooms, print a congratulatory message
    print(Back.GREEN + Fore.BLACK + Style.BRIGHT + "\n🎉 Congratulations! You've completed all the challenges. 🎉\n" + Style.RESET_ALL)

rooms = load_rooms('rooms.json')  # Load the room data from the JSON file

async def main():
    await run_quiz(rooms)  # Start the quiz

asyncio.run(main())  # Run the main function to start the asyncio event loop and execute the quiz
