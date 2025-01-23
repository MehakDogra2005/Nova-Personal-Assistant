import datetime
import os
import pickle
import pyttsx3
import speech_recognition as sr
import wikipedia
import pyjokes
import requests
import random
import pyautogui
import time
import subprocess
import pywhatkit as pwk
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re
from plyer import notification
import pygetwindow as gw
import base64
import google.auth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
import mtranslate
import openai_request as ai
import math
from sympy import symbols, diff, integrate
import user_config
import smtplib



# Initialize pyttsx3 for text to speech
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Choose the voice (0 for male, 1 for female)
engine.setProperty('rate', 170) 

# Initialize the speech recognizer
listener = sr.Recognizer()

# Function to talk (Text-to-speech)
def talk(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen to commands
def listen_for_commands():
    with sr.Microphone() as source:
        print("Listening for a command...")
        listener.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        voice = listener.listen(source)
        try:
            command = listener.recognize_google(voice, language="en-US")
            command = command.lower()
            return command
        except sr.UnknownValueError:
            talk("Sorry, I didn't catch that. Could you please repeat?")
            return None
        except sr.RequestError:
            talk("Sorry, I'm having trouble connecting to the speech recognition service.")
            return None


# Function to play a song 
def play_song(command) :
    song = command.replace('play', '')
    talk('playing'+song)
    pwk.playonyt(song)




# Function to tell the time
def tell_time():
    time_now = datetime.datetime.now().strftime('%I:%M %p')
    talk(f"The current time is {time_now}.")

# Function to give information from wikipedia
def give_information(command):
    element = command.replace('give information about', '').strip()
    try:
        info = wikipedia.summary(element, 1)
        talk(info)
    except wikipedia.exceptions.DisambiguationError as e:
        talk(f"There are multiple results for {element}. Please be more specific.")
    except wikipedia.exceptions.HTTPTimeoutError:
        talk("Sorry, I couldn't fetch the information at the moment. Please try again later.")
    except wikipedia.exceptions.PageError:
        talk("Sorry, I couldn't find any information on that topic.")

# Function to tell a joke
def tell_joke():
    joke = pyjokes.get_joke()
    talk(joke)

# Function to provide weather updates
def get_weather():
    talk("Please tell me the city you want the weather for.")
    city = listen_for_commands()
    
    if city:
        city = city.lower()
        api_key = user_config.weather_api_key
        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        response = requests.get(base_url)
        data = response.json()

        if data['cod'] == 200:
            weather_description = data['weather'][0]['description']
            temperature = data['main']['temp'] - 273.15  # Convert from Kelvin to Celsius
            talk(f"The current weather in {city} is {weather_description} with a temperature of {temperature:.2f}°C.")
        else:
            talk(f"Sorry, I couldn't fetch the weather information for {city}. Please check the city name.")
    else:
        talk("I couldn't hear a city name. Please try again.")

# Function to get a random children's story
def tell_story():
    # URL of the API that provides random short stories
    api_url = "https://shortstories-api.onrender.com"  

    try:
        # Make a GET request to fetch a random story
        response = requests.get(api_url)
        if response.status_code == 200:
            story_data = response.json()  # Parse the JSON response

            # Extract story details from the response (assuming the API returns a dictionary with 'title', 'author', 'story', and 'moral')
            title = story_data.get('title', 'Unknown Title')
            author = story_data.get('author', 'Unknown Author')
            story_content = story_data.get('story', 'No content available')
            moral = story_data.get('moral', 'No moral provided')

            # Format the story
            story = f"Title: {title}\nAuthor: {author}\n\n{story_content}\n\nMoral: {moral}"
            talk(story)
        else:
            talk("Sorry, I couldn't fetch a story at the moment. Please try again later.")
    except requests.exceptions.RequestException as e:
        talk(f"Sorry, there was an error fetching the story. Please try again later. Error: {e}")


# Function to get news based on user-selected category
def get_news():
    # Ask the user for the news category
    talk("What category of news would you like? You can choose from sports, technology, business, health, entertainment, etc.")
    category = listen_for_commands()

    if category:
        category = category.lower()
        # dictionary with available categories for validation
        categories = ["sports", "technology", "business", "health", "entertainment", "science", "general"]

        # Check if the category provided by the user is valid
        if category not in categories:
            talk("Sorry, I didn't understand that category. Please choose from sports, technology, business, health, entertainment, or science.")
            return

        # Use NewsAPI to fetch the latest news based on the selected category
        api_key = user_config.news_api_key
        url = f"https://newsapi.org/v2/top-headlines?category={category}&apiKey={api_key}"

        try:
            response = requests.get(url)
            news = response.json()

            # Check if the response status is OK
            if news["status"] == "ok":
                articles = news["articles"]
                if len(articles) > 0:
                    talk(f"Here are the top news updates in {category}:")
                    for article in articles[:3]:  # Get top 3 latest news
                        title = article["title"]
                        description = article["description"]
                        talk(f"Title: {title}. Description: {description}")
                else:
                    talk(f"Sorry, I couldn't find any news in the {category} category at the moment.")
            else:
                talk("Sorry, I couldn't fetch the news right now. Please try again later.")
        except requests.exceptions.RequestException as e:
            talk("Sorry, there was an error fetching the news. Please try again later.")
            print(f"Error: {e}")

# Function to convert 12-hour format to 24-hour format
def convert_to_24hr_format(time_str):
    try:
        # Standardize the case to avoid issues with "p.m." or "a.m."
        time_str = time_str.lower().replace('p.m.', 'PM').replace('a.m.', 'AM')
        print(f"Normalized time string: {time_str}")  # Debug print
        
        # Matching time like "10 PM", "10:00 PM", "6 PM", or "6:00 PM"
        time_match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM)', time_str.strip())
        if not time_match:
            print("Time format not recognized.")  # Debug print
            return None
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        period = time_match.group(3).upper()

        print(f"Parsed time - Hour: {hour}, Minute: {minute}, Period: {period}")  # Debug print

        # Convert to 24-hour format
        if period == "PM" and hour != 12:
            hour += 12  # Convert PM hours to 24-hour format
        elif period == "AM" and hour == 12:
            hour = 0  # Convert 12 AM to 00:00 hours

        # Return time in 24-hour format (HH:MM)
        return datetime.time(hour, minute)
    except Exception as e:
        print(f"Error converting time: {e}")
        return None


# Function to set the alarm
def set_alarm():
    talk("What time would you like to set the alarm for?")
    command = listen_for_commands()

    if command and 'set alarm for' in command:
        alarm_time_str = command.replace('set alarm for', '').strip()
        print(f"Time extracted from command: {alarm_time_str}")  # Debug print
        
        if alarm_time_str:
            # Check and confirm the time with the user
            talk(f"You said, {alarm_time_str}. Is that correct?")
            confirmation = listen_for_commands()
            
            if confirmation and 'yes' in confirmation:
                alarm_time = convert_to_24hr_format(alarm_time_str)
                
                if alarm_time:
                    talk(f"Your alarm is set for {alarm_time_str}. I'll remind you when it's time!")
                    # Here you would set the alarm, for now, we simulate checking the time
                    while True:
                        current_time = datetime.datetime.now().time()
                        print(f"Current time: {current_time}")  # Debug print
                        if current_time >= alarm_time:
                            talk("It's time! Your alarm is going off.")
                            break
                        time.sleep(60)  # Check every minute
                else:
                    talk("Sorry, I couldn't understand the time format. Please try again.")
            else:
                talk("Okay, let's try again later.")
        else:
            talk("Sorry, I didn't hear a time. Could you please repeat?")
    else:
        talk("Sorry, I didn't understand. Please try to set the alarm again.")

# Function to search for recipes
def search_recipe():
    talk("What recipe are you looking for?")
    recipe = listen_for_commands()

    if recipe:
        talk(f"Searching for a {recipe} recipe...")
        
        # Spoonacular recipe search endpoint
        search_url = f"https://api.spoonacular.com/recipes/complexSearch?query={recipe}&number=1&apiKey=f7f9d69d76754439b1496bba3dfbc667"
        try:
            response = requests.get(search_url)
            data = response.json()

            if data['results']:
                recipe_info = data['results'][0]
                recipe_id = recipe_info['id']
                recipe_name = recipe_info['title']
                recipe_url = f"https://spoonacular.com/recipes/{recipe_name.replace(' ', '-')}-{recipe_id}"
                talk(f"So, the recipe is {recipe_name}.")

                # Fetch detailed information about the recipe
                detail_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={user_config.recipe_api_key}"
                detail_response = requests.get(detail_url)
                detail_data = detail_response.json()

                # Read out recipe details
                if 'title' in detail_data:
                    talk(f"Recipe Name: {detail_data['title']}")
                if 'readyInMinutes' in detail_data:
                    talk(f"Ready in {detail_data['readyInMinutes']} minutes.")
                if 'servings' in detail_data:
                    talk(f"This recipe serves {detail_data['servings']} people.")
                if 'extendedIngredients' in detail_data:
                    talk("Here are the ingredients you'll need:")
                    for ingredient in detail_data['extendedIngredients']:
                        talk(f"{ingredient['original']}")
                if 'instructions' in detail_data:
                    talk("And here are the instructions:")
                    talk(detail_data['instructions'])

                talk(f"You can also view this recipe online here: {recipe_url}")
                print(recipe_url)
            else:
                talk(f"Sorry, I couldn't find a recipe for {recipe}.")
        except requests.exceptions.RequestException as e:
            talk(f"Sorry, there was an error fetching the recipe. Please try again later. Error: {e}")


def set_timer():
    talk("How many hours, minutes, or seconds would you like to set the timer for?")
    
    # Start a loop to keep asking for time until it is understood
    while True:
        time_input = listen_for_commands()

        if time_input:
            try:
                # Check if the input contains 'hour', 'minute', or 'second'
                if "hour" in time_input:
                    # Extract number of hours and set the timer
                    hours = int(time_input.replace("hours", "").replace("hour", "").strip())
                    if hours <= 0:
                        talk("Please provide a positive number for the timer.")
                    else:
                        talk(f"Setting a timer for {hours} hours.")
                        time.sleep(hours * 3600) 
                        talk(f"Your {hours}-hour timer is up!")
                        break 

                elif "minute" in time_input:
                    # Extract number of minutes and set the timer
                    minutes = int(time_input.replace("minutes", "").replace("minute", "").strip())
                    if minutes <= 0:
                        talk("Please provide a positive number for the timer.")
                    else:
                        talk(f"Setting a timer for {minutes} minutes.")
                        time.sleep(minutes * 60) 
                        talk(f"Your {minutes}-minute timer is up!")
                        break 

                elif "second" in time_input:
                    # Extract number of seconds and set the timer
                    seconds = int(time_input.replace("seconds", "").replace("second", "").strip())
                    if seconds <= 0:
                        talk("Please provide a positive number for the timer.")
                    else:
                        talk(f"Setting a timer for {seconds} seconds.")
                        time.sleep(seconds) 
                        talk(f"Your {seconds}-second timer is up!")
                        break  

                else:
                    talk("Sorry, I couldn't understand the time unit. Please mention either hours, minutes, or seconds.")

            except ValueError:
                talk("Sorry, I didn't understand the time. Please try again.")
        
        else:
            talk("I couldn't hear the time. Please say the number of hours, minutes, or seconds again.")

def load_tasks():
    try:
        with open("todo_list.txt", "r") as file:
            tasks = file.readlines()
            return [task.strip() for task in tasks]  # Remove newline characters
    except FileNotFoundError:
        return []  

def save_tasks():
    with open("todo_list.txt", "w") as file:
        for task in todo_list:
            file.write(task + "\n") 

def show_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=5  # Notification duration in seconds
    )

def add_task():
    talk("What task would you like to add to your to-do list?")
    task_input = listen_for_commands()
    if task_input:
        # Split multiple tasks if they are separated by 'and' or commas
        tasks = [task.strip() for task in task_input.split("and") if task.strip()]
        tasks = [task.strip() for subtask in tasks for task in subtask.split(",") if task.strip()]
        
        todo_list.extend(tasks) 
        save_tasks()  
        for task in tasks:
            talk(f"I've added the task: {task}.")
        show_notification("Task Added", f"{len(tasks)} task(s) added to your to-do list.")
    else:
        talk("I couldn't hear the task. Please try again.")

def view_tasks():
    if todo_list:
        talk("Here are the tasks in your to-do list.")
        for idx, task in enumerate(todo_list, start=1):
            talk(f"Task {idx}: {task}")
        show_notification("To-Do List", "Displayed all tasks in your to-do list.")
    else:
        talk("Your to-do list is empty.")
        show_notification("To-Do List", "Your to-do list is empty.")

def delete_task():
    if os.path.exists("todo_list.txt") and os.path.getsize("todo_list.txt") > 0:
        while True:  
            with open("todo_list.txt", "r") as file:
                tasks = [task.strip() for task in file.readlines()]  
            
            if not tasks:
                talk("Your to-do list is empty.")
                show_notification("To-Do List", "Your to-do list is empty.")
                return

            talk("Here are your current tasks:")
            for idx, task in enumerate(tasks, start=1):
                talk(f"Task {idx}: {task}")

            talk("Which task number would you like to remove? Say the task number.")
            task_number = listen_for_commands() 

            # Debugging Logs (Remove in production)
            print(f"Tasks: {tasks}")
            print(f"Received task number: {task_number}")

            if task_number and task_number.isdigit():
                task_number = int(task_number)
                if 1 <= task_number <= len(tasks):
                    removed_task = tasks.pop(task_number - 1)
                    with open("todo_list.txt", "w") as file:
                        file.writelines([task + "\n" for task in tasks]) 
                    talk(f"I've removed the task: {removed_task}.")
                    show_notification("Task Removed", f"Task removed: {removed_task}")
                    break  
                    talk("Invalid task number. Please provide a valid number.")
            else:
                talk("I couldn't understand the task number. Please try again.")
    else:
        talk("Your to-do list is empty.")
        show_notification("To-Do List", "Your to-do list is empty.")




todo_list = load_tasks()

def open_application_with_pyautogui(app_name):
    try:
        # Simulate pressing the Windows key
        pyautogui.press('win')
        time.sleep(1)  # Wait for the start menu to open
        
        # Type the application name
        pyautogui.write(app_name, interval=0.1)
        time.sleep(1)  
        
        # Press Enter to open the application
        pyautogui.press('enter')
        print(f"Opened {app_name} successfully!")
    except Exception as e:
        print(f"Failed to open {app_name}: {e}")

def open_youtube_in_chrome(topic):
    try:
        talk(f"Searching for {topic} on YouTube in Google Chrome...")

        # Path to the Chrome browser executable 
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"  
        search_url = f"https://www.youtube.com/results?search_query={topic}"
        
        # Register Chrome browser and open the URL
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
        webbrowser.get('chrome').open(search_url)
        
        time.sleep(3)  # Wait for the page to load
        talk(f"Here are the results for {topic} on YouTube in Google Chrome.")
    except Exception as e:
        talk(f"Sorry, I couldn't search for {topic} on YouTube in Google Chrome.")
        print(f"Error: {e}")

def search_google(topic):
    try:
        talk(f"Searching for {topic} on Google...")

        # Construct the Google search URL
        search_url = f"https://www.google.com/search?q={topic}"

        # Open the URL in the default browser
        webbrowser.open(search_url)

        time.sleep(3)  # Wait for the page to load
        talk(f"Here are the search results for {topic} on Google.")
    except Exception as e:
        talk(f"Sorry, I couldn't search for {topic} on Google.")
        print(f"Error: {e}")

import pywhatkit as kit

def send_whatsapp_message():
    try:

        talk(f"Please enter the contact name")
        contact_name = input(f"Enter the contact number : ").strip()
        # Ask the user for the contact number
        talk(f"Please enter the contact number for {contact_name}, with the country code (e.g., +1234567890).")
        contact_number = input(f"Enter the contact number for {contact_name} (with country code): ").strip()

        # Ask the user for the message
        talk(f"What message would you like to send to {contact_name}?")
        message = input(f"Enter the message for {contact_name}: ").strip()

        # Ask the user for the time (hour and minute)
        talk("At what hour do you want to send the message? Please enter the hour in 24-hour format.")
        hour = int(input("Enter the hour to send the message (24-hour format): ").strip())
        
        talk("At what minute do you want to send the message?")
        minute = int(input("Enter the minute to send the message: ").strip())

        # Send the message using pywhatkit
        pwk.sendwhatmsg(contact_number, message, hour, minute)

        talk(f"Message sent to {contact_name} at {contact_number}: {message}")

    except Exception as e:
        talk(f"An error occurred while sending the message: {e}")


def send_email():
    # Ask the user for email details using voice feedback
    talk("Please provide your email address.")
    user_email = input("Enter your email address: ").strip()

    talk("Please provide your email password.")
    user_password = input("Enter your email password: ").strip()  # Be cautious about storing passwords securely

    talk("Please enter the subject of the email.")
    subject = input("Enter the subject of the email: ").strip()

    talk("What is the message you want to send?")
    message = input("Enter the message you want to send: ").strip()

    talk("Who is the recipient of the email?")
    email_receiver = input("Enter the recipient's email address: ").strip()

    # Create a MIMEText object to represent the email
    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['To'] = email_receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    # Setup the SMTP server and send the email
    try:
        # Connect to the SMTP server (Gmail in this case)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user_email, user_password)  
        text = msg.as_string()
        server.sendmail(user_email, email_receiver, text)
        server.quit() 

        talk("Email sent successfully!")
    except Exception as e:
        talk(f"An error occurred: {e}")
 

def basic_calculator(operation, numbers):
    if operation == 'add':
        return sum(numbers)
    elif operation == 'subtract':
        if(numbers[0] > numbers[1]):
            return numbers[0] - numbers[1]
        else:
            talk("minus")
            return abs(numbers[1] - numbers[0])
    elif operation == 'multiply':
        result = 1
        for num in numbers:
            result *= num
        return result
    elif operation == 'divide':
        if numbers[1] == 0:
            return "Cannot divide by zero."
        return numbers[0] / numbers[1]
    elif operation == 'power':
        return numbers[0] ** numbers[1]
    elif operation == 'log':
        return math.log(numbers[0], numbers[1])  # Logarithm of numbers[0] with base numbers[1]
    elif operation == 'exponent':
        return math.exp(numbers[0])
    else:
        return "Unknown operation."

# Function to handle advanced math (symbolic calculations)
def advanced_calculator(operation, expr, variable):
    x = symbols(variable)
    if operation == 'differentiate':
        return diff(expr, x)
    elif operation == 'integrate':
        return integrate(expr, x)
    else:
        return "Unknown operation."

# Main function to run the assistant
def run_assistant():
    talk("Hello, I'm Nova! How can I assist you today?")
    nova_chat = []
    
    while True:
        command = listen_for_commands()
        if command:
            print(f"Received command: {command}")

            if 'play' in command:
                play_song(command)

            elif 'time' in command and 'set timer' not in command:
                tell_time()

            elif 'give information about' in command:
                give_information(command)

            elif 'joke' in command:
                tell_joke()

            elif 'weather' in command:
                get_weather()

            elif 'story' in command:
                tell_story()

            elif 'news' in command:
                get_news()

            elif 'set alarm' in command:
                set_alarm()

            elif 'recipe' in command:
                search_recipe()

            elif 'set timer' in command:
                set_timer()

            elif 'add task' in command:
                add_task()

            elif 'view tasks' in command or 'show tasks' in command:
                view_tasks()

            elif 'delete task' in command or 'remove task' in command:
                delete_task()

            elif 'send email' in command:  # Send email
                talk("Sure! Let's send an email.")
                send_email()

            elif 'open' in command:  # Open application
                app_name = command.replace('open', '').strip()
                if app_name:
                    open_application_with_pyautogui(app_name)
                else:
                    talk("I didn't catch the application name. Please specify the application you want to open.")

            elif 'search on youtube' in command:  # Search YouTube
                topic = command.replace('search youtube', '').strip()
                if topic:
                    open_youtube_in_chrome(topic)
                else:
                    talk("Please specify the topic you want to search for on YouTube.")

            elif 'search on google' in command:  # Search Google
                topic = command.replace('search google', '').strip()
                if topic:
                    search_google(topic)
                else:
                    talk("Please specify the topic you want to search for on Google.")

            elif 'send message' in command:  # Send WhatsApp message
                parts = command.replace('send message to', '').strip().split(' ', 1)
                send_whatsapp_message()
        

            elif 'ask ai' in command:
                user_query = command.replace('ask ai', '').strip()
                if 'clear chat' in command:
                    nova_chat = []
                    talk("Chat Cleared")
                elif not user_query:
                    talk("Please provide a query for AI.")
                else:
                    nova_chat.append({"role": "user", "content": user_query})
                    try:
                        response = ai.send_request(nova_chat)
                        nova_chat.append({"role": "assistant", "content": response})
                        talk(response)
                    except Exception as e:
                        talk(f"An error occurred while processing your query: {str(e)}")

            elif 'calculate' in command: #calculate <operation> <expression> <variable>
                try:
                    parts = command.split(' ')
                    operation = parts[1]

                # Handle basic operations
                    if operation in ['add', 'subtract', 'multiply', 'divide', 'power', 'log', 'exponent']:
                        numbers = list(map(float, parts[2:]))
                        result = basic_calculator(operation, numbers)
                        talk(f"The result is: {result}")

                # Handle advanced operations
                    elif operation in ['differentiate', 'integrate']:
                        expr = parts[2]
                        variable = parts[3]
                        result = advanced_calculator(operation, expr, variable)
                        talk(f"The result is: {result}")

                    else:
                        talk("Sorry, I can't perform that operation.")

                except Exception as e:
                    talk(f"An error occurred: {e}")

            elif 'stop' in command or 'bye' in command:
                talk("Goodbye! Have a nice day!")
                break

            else:
                talk("Sorry, I didn't understand that. Could you please repeat?")


# Run the assistant
if __name__ == "__main__":
    run_assistant() 