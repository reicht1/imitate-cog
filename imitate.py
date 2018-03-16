import discord
from discord.ext import commands
from discord import errors
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
        mentionRegex = r"<@![0-9]*>"
        
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
                    resultMessage = model.make_short_sentence(charsLeft)
                    
                    #clean out any mentions that may have found their way in           
                    while re.search(mentionRegex, resultMessage) is not None:
                        foundMention = re.search(mentionRegex, resultMessage).group(0)
                        #print("foundMention is" + foundMention)
                        mentionString = re.search(r"[0-9]+", foundMention).group(0)
                        #print("mentionString is" + mentionString)
                        try:
                            mentionName = await self.bot.get_user_info(mentionString)
                            mentionName = mentionName.display_name
                            resultMessage = resultMessage.replace(foundMention, mentionName)
                        except discord.errors.NotFound:
                            resultMessage = resultMessage.replace(foundMention, "[unknown user]")
                        except discord.errors.HTTPException:
                            resultMessage = resultMessage.replace(foundMention, "[unknown user]")
                    
                    if len(resultMessage) > 0:
                        await self.bot.say(resultMessage)
                        charsLeft -= len(resultMessage)
                    else:
                        continue
            except ValueError:
                print("ERROR: imitate: Could not get markov model from user JSON file!")
                await self.bot.say("ERROR: imitate: Could not get markov model from user JSON file!")
                # I guess the array didn't exist in the text file or something.
                return
            except KeyError:
                await self.bot.say("User does not have any information about them yet.")
     
    async def on_message_create(self, message):
        
        content = message.clean_content
        
        userID = message.author.id
        exclusionString = r"^[!?\\\/]" #exclude lines with commands
        
        #if we need to ignore the message...ignore it
        exclude = re.search(exclusionString, content)
        
        #if content should be ignored, or is basically nothing, ignore it
        if exclude or (content.replace(" ", "") is ""):
            return;
        
        print(message.author.name + ": " + message.content + '\n')
        
        
        #get new model
        if content is not "":
            try:
                model = markovify.NewlineText(content, retain_original=False)
            except KeyError:
                print("ERROR: Imitate: could not add message to model. It may have been blank.")
                return
        else:
            return
        
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