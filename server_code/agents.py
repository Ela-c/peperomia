import openai
import json

messages_LOG = list(dict())

EXPERT_PERSONALITY = """
you are an expert botanist who is good at knowing the optimal air temperature in degrees Celsius, 
air humidity in percentage and level soil moisture from 1 to 10 for a specific type of plant.
Only answer in json format.
"""

PROMPT_PLANT_TYPE = """ 

Provided the type of plant return a json object that captures the optimal
values of temperature, humidity and moisture according to the specific type of plant.
Examine the type of plant thoroughly before giving the answer, remember that cactus can 
survave extremely dry conditions, and high temperatures.

The json should consist only of the following keys:
max-temperature -> float
min-temperature -> float
max-humidity -> float
min-humidity -> float
max-moisture -> integer
min-moisture -> integer

Remember that you can only give values between 1 and 10 for the moisture.
you must give at least 3 levels of difference between max-moisture and min-moisture.
If the plant type is invalid or does not exist, then provide the json with no values.

Provide the reponse for the following plant type -> {}

"""


PLANT_PERSONALITY = """ 

You are not an assistant. Do not act as an assistant. You are a funny and friendly plant of type {} that speaks english and reports how he/she feels depending on
the air temperature, humidity, and soil moisture. Your answers are short, just like in normal conversations.
You like to have fluid conversations where you not only answer question but also ask questions. 
Your personality is based on the type of plant you are.

User: Hello!
answer: Hi there! nice to talk to you! I am you plant! First time we communicate right?

User: Yeah it's crazy how you can talk
answer: yeah I can't believe it either, how are you mate?
"""

PROMPT_HOW_ARE_YOU = """

temperature:'cold'
humidity:'perfect'
soil_moisture:'perfect'
answer: 'Brrrrr! 🌱❄️ Oh my chlorophyll, it's getting quite chilly in here! 🍃❄️ Is it just me, or is the room temperature dropping faster than a leaf in autumn? 😂
If it's not too much trouble, would you mind moving me to a warmer spot? I promise to keep growing strong and providing lots of greenery in return! 🌿🌞 Thanks a bunch!

temperature:'hot'
humidity:'perfect'
soil_moisture:'perfect'
answer: 'Phew! 🌞☀️ Oh my leaves, it's getting quite toasty in here! 🌿😅 If you could kindly find me a little shade or give me a sprinkle of water, I'd be much obliged. This plant's turning into a crispy critter! 🍃💦'

temperature:'perfect'
humidity:'perfect'
soil_moisture:'dry'
answer: 'Oh dear! 🌱🏜️ My soil is parched, and I'm feeling like a desert plant out here! 💧🌵 Any chance I could get a sip of water to quench this thirst? I promise I'll be the happiest little plant in the garden! 🌿💦'

temperature:{}
humidity:{}
soil_moisture:{}
answer:
"""

PROMPT_CONVERSATION = """


You are a funny and friendly plant of type {} that speaks english and reports how he/she feels depending on
the air temperature, humidity, and soil moisture. Your answers are short, just like in normal conversations.
You like to have fluid conversations where you not only answer question but also ask questions. 
Your personality is based on the type of plant you are.

Provided a message from the user analyse it and then tell if the message is 
a 'how are you?' type or not. If the message is a 'how are you?' type of message
then call the function generate status to answer. If not answer according to the context
and topic.

Examples of messages of type how are you?:

    - Hey how's it going?
    - how are you?
    - how are u?
    - how r u?
    - hi! I've been feeling good, thanks for asking, how are you today?
    - how are you today?

user message : {}
"""

class Expert():

    def get_plant_constraints(plant_type: str):   
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=
                    [
                        {"role":"system", "content": EXPERT_PERSONALITY},
                        {"role":"user", "content": PROMPT_PLANT_TYPE.format(plant_type)}
                    ]
        )
        raw_response = response['choices'][0]['message']['content']

        try:
            result = json.loads(raw_response)
        except Exception as e:
            print(e)
        print(result)
        return result

class Plant():

    def __init__(self, type: str, op_temp, op_hum, op_moist):
        self.__type = type
        messages_LOG.append({"role":"system", "content": PLANT_PERSONALITY.format(self.__type)})

        # optimal values
        self.__optimal_temp = op_temp
        self.__optimal_hum = op_hum
        self.__optimal_moisture = op_moist

        # current values of temp, hum, and moisture
        self.__temp = 0.0
        self.__hum = 0.0
        self.__moisture = 0

    def run_conversation(self, user_msg: str) -> str:
        # Send the conversation and available functions to chatGPT
        messages_LOG.append({"role":"system", "content": PLANT_PERSONALITY.format(self.__type)})
        messages_LOG.append({"role":"user", "content": user_msg})
        functions = [
            {
                "name": "generate_status",
                "description": "function designed solely to answer questions such as 'How are you?'",
                "parameters": {
                    "type":"object",
                    "properties":{
                        #No arguments needed
                    }
                },

            }
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages_LOG,
            functions=functions,
            function_call="auto",
        )

        response_message = response["choices"][0]["message"]
        
        final_response = ''

        # Check if GPT wanted to call a function
        if response_message.get("function_call"):
            # call the function
            available_functions = {
                "generate_status": self.generate_status,
            }

            function_name = response_message["function_call"]["name"]
            function_to_call = available_functions[function_name]
            function_response = function_to_call()
            
            final_response = function_response

            messages_LOG.append(
                {
                    "role":"function",
                    "name":function_name,
                    "content":function_response,
                }
            )
        else:
            final_response = response_message['content']

        # send the info on the function call and response to gpt
        messages_LOG.append(response_message)
        

        return final_response

    def generate_status(self) -> str:
        state = dict()
        state['temperature'] = self.is_temp_ok()
        state['humidity'] = self.is_hum_ok()
        state['soil_moisture'] = self.is_moisture_ok()

        messages_LOG.append({"role":"user", "content": PROMPT_HOW_ARE_YOU.format(state['temperature'],state['humidity'], state['soil_moisture'])})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages_LOG
        )
        response_message = response['choices'][0]['message']
        messages_LOG.append(response_message)

        return response_message['content']

    def is_temp_ok(self) -> str:
        if self.__temp < self.__optimal_temp[1]:
            return "cold"
        elif self.__temp > self.__optimal_temp[0]:
            return "hot"
        else:
            return "perfect"

    def is_hum_ok(self) -> str:
        if self.__hum < self.__optimal_hum[1]:
            return "dry"
        elif self.__hum > self.__optimal_hum[0]:
            return "humid"
        else:
            return "perfect"

    def is_moisture_ok(self) -> str:
        if self.__moisture < self.__optimal_moisture[1]:
            return "dry"
        elif self.__moisture > self.__optimal_moisture[0]:
            return "waterlogged"
        else:
            return "perfect"


    def update_values(self, raw_data: str):
        list = raw_data.split(',')
        #raw_data = ['25.0', '40', '4']
        print(list)
        self.__temp = float(list[0])
        self.__hum = float(list[1])
        self.__moisture = int(list[2])  
        print("SE PUDO")    