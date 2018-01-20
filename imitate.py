import discord
from discord.ext import commands
import json
import markovify
import os
from os import path
from os import makedirs
from os import listdir
import re

#global variables. To be treated as constants
global dataPath 
dataPath = "./data/imitate"
global newJson
newJson = {}
global sentenceSize
sentenceSize = 140

class imitate:
    """Uses Markovify to imitate users"""
    def __init__(self, bot):
        self.bot = bot
        
    async def profileExists(self, userID):
        #make sure data path exists for user
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)
    
        #if dir for JSON file of user's profile does not exist, make it
        if os.path.exists(dataPath + '/' + userID + '.txt'):
            return True
        else:
            return False
    
    @commands.command(pass_context=True, no_pm=True)		
    async def imitate(self, ctx, *username : str):
        #get user info
        username = " ".join(username)
        currentServer = ctx.message.server
        user = currentServer.get_member_named(username)
        
        #continue only if user actually exists
        if user is None:
            print("ERROR: discordbio: [p]about @mention: This user either does not exist or is not a part of your server")
            await self.bot.say('This user "' + str(username) + '" either does not exist or is not a part of your server.')
            return
        userID = user.id
        
        #Can't use any info about a user if it doesn't exist
        if await self.profileExists(userID) is False:
            await self.bot.say("User does not have any information about them yet.")
            return
        
        with open(dataPath + '/' + userID + '.txt', 'r') as file:
            try:
                jsonData = json.load(file)
                model = markovify.NewlineText.from_json(str(jsonData))
              
                charsLeft = sentenceSize
                while charsLeft > 20:
                    #await self.bot.say(str(charsLeft) + " left")
                    resultMessage = model.make_short_sentence(charsLeft)
                    if len(resultMessage) > 0:
                        await self.bot.say(resultMessage)
                        charsLeft -= len(resultMessage)
                    else:
                        continue
                #await self.bot.say("Done!")
            except ValueError:
                print("ERROR: imitate: Could not get markov model from user JSON file!")
                await self.bot.say("ERROR: imitate: Could not get markov model from user JSON file!")
                # I guess the array didn't exist in the text file or something.
                return
            except KeyError:
                await self.bot.say("User does not have any information about them yet.")
     
    async def on_message_create(self, message):
        print(message.author.name + ": " + message.content + '\n')
        
        content = message.content
        userID = message.author.id
        exclusionString = "^.((re|un|)load )?imitate"
        
        #if we need to ignore the message...ignore it
        exclude = re.search(exclusionString, content)
        
        if exclude:
            return;
        
        #get new model
        model = markovify.NewlineText(content, retain_original=False)
        
        #make sure that the user has a profile, if they do, get info from it.
        if await self.profileExists(userID):
            with open(dataPath + '/' + userID + '.txt', 'r') as file:
                try:
                    jsonData = json.load(file)
                    oldModel = markovify.NewlineText.from_json(jsonData)
                    model = markovify.combine(models=[oldModel, model])
                except ValueError:
                    print("ERROR: imitate: Could not get markov model from user JSON file!")
                    await self.bot.say("ERROR: imitate: Could not get markov model from user JSON file!")
                    # I guess the array didn't exist in the text file or something.
                    return
            
        markovJson = model.to_json()
        with open(dataPath + '/' + userID + '.txt', 'w+') as file:
            json.dump(markovJson, file, indent=4)
        

def setup(bot):
    cogToLoad = imitate(bot)
    bot.add_listener(cogToLoad.on_message_create, "on_message")
    bot.add_cog(cogToLoad)