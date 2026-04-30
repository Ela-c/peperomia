import os
import telebot
from dotenv import load_dotenv
from agents import Expert, Plant
import threading
import time
import openai
import serial
from arduino import *

load_dotenv()
bot_api_key = os.environ['BOT_API_KEY']
openai_api_key = os.environ['OPENAI_API_KEY']
bot = telebot.TeleBot(bot_api_key)
openai.api_key = openai_api_key
chat_id = None
myPlant: Plant = None

# then the server should have a function to ask chatgpt if 
# what the user just wrote can be interpreted as a how are you?
# if the function returns true, then the server should send a signal
# to the arduino and the arduino should 

# START
@bot.message_handler(commands=["start"])
def greet(message):
    # Greet the user
    global chat_id
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Hey {message.from_user.first_name}! Welcome to your plant manager!")
    bot.send_message(chat_id, "Here you will be able to communicate with your plant and know how your plant feels!")

    #asking the name of the plant type
    sent_message = bot.send_message(chat_id, "What is the type of your plant?")
    bot.register_next_step_handler(sent_message, handle_plant_type)

# PLANT SET UP
def handle_plant_type(message):
    constraints = Expert.get_plant_constraints(message.text)
    if None in constraints.values():
        bot.reply_to(message, "Invalid plant type")
        return
    optimal_temp = (constraints["max-temperature"], constraints["min-temperature"])
    optimal_hum = (constraints["max-humidity"],constraints["min-humidity"])
    optimal_moisture = (constraints["max-moisture"], constraints["min-moisture"])

    bot.reply_to(message, "Thanks for sharing the plant type!")

    global myPlant
    myPlant = Plant(message.text, optimal_temp, optimal_hum, optimal_moisture)

    bot.send_message(chat_id, "Now you can communicate with your plant. Try asking 'how are you?'")

#RUN CONVERSATION
@bot.message_handler(func=lambda message: True)
def send_plant_status(message):
    if myPlant == None:
        return
    response = ''
    if(message.text.lower() == "how are you?"):
        response = myPlant.generate_status()
    else:
        response = myPlant.run_conversation(message.text)
    bot.send_message(chat_id, response)

#run in another thread
def update_plant():
    global myPlant
    arduino_port = find_arduino(get_ports())   # serial port of arduino
    baud_rate = 9600
    ser = serial.Serial(arduino_port, baud_rate, timeout=0.010)
    try:
        while True:
            time.sleep(1)
            if myPlant != None:
                data = serial_read(ser)
                print("Received data:", data)
                if "," in data:
                    try:
                        myPlant.update_values(data)
                    except Exception as e:
                        print("NO se pudo")
                        print(e)
                        continue
    except Exception as e:
        print("closing")
        print(e)
        ser.close()
            
threading.Thread(target=update_plant, daemon=True).start()

if __name__ == "__main__":
    #run bot
    bot.polling()
