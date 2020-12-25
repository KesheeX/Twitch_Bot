import discord
import requests
import json
import os
import asyncio


def read_token():
    with open("token.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip()

def get_help():
    with open("Commands.txt", "r") as f:
        lines = f.read()
        return lines.strip()
    
def read_id():
    with open("twitch_id.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip()
    
token = read_token()
help = get_help()
twitch_id  = read_id()

client = discord.Client()


def verify_user(name): #verifies if an account exist. Used in add_sub()

    headers = {
        'Accept': 'application/vnd.twitchtv.v5+json',
        'Client-ID': twitch_id,
    }

    params = (
        ('login', name),
    )

    response = requests.get('https://api.twitch.tv/kraken/users', headers=headers, params=params)
    data = json.loads(json.dumps(response.json()))

    try:
        user_id = data['users'][0]['_id']
        verified = True

    except IndexError:
        verified = False

    return verified

def check_status(name): #check live status of a single channel
    headers = {
        'Accept': 'application/vnd.twitchtv.v5+json',
        'Client-ID': twitch_id,
    }

    params = (
        ('login', name),
    )

    response = requests.get('https://api.twitch.tv/kraken/users', headers=headers, params=params)
    data = json.loads(json.dumps(response.json()))

    try:
        user_id = data['users'][0]['_id']

    except IndexError:
        print('omg')

    headers = {
        'Accept': 'application/vnd.twitchtv.v5+json',
        'Client-ID': twitch_id,
    }

    streamCheck = requests.get('https://api.twitch.tv/kraken/streams/' + user_id, headers=headers)


    status = json.loads(json.dumps(streamCheck.json()))
    online = False
    print(status)
    if status['stream'] == None:
        online = False

    else:
        online = True

    return online

async def sub_check(id,cid): #checks the status of server's every subscribed channel
    try:
        server = client.get_guild(id)
        channel = server.get_channel(cid)
        filename = str(id) + "subs.txt"
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                data = json.load(f)

            f.close()

            check = True
            n = 0
            while (check):
                try:
                    name = data['subs'][n]['name']
                    if check_status(name):
                        if data['subs'][n]['mentioned'] == 'false':
                            await channel.send(
                                'Hey @everyone check it out! https://www.twitch.tv/' + name + ' is streaming now!')

                            data['subs'][n]['mentioned'] = 'true'
                    else:
                        data['subs'][n]['mentioned'] = 'false'
                except IndexError:
                    check = False
                n += 1

            try:
                with open(filename, 'w') as f:
                    json.dump(data, f)
            except PermissionError:
                pass  ####
    except Exception as e:
        print(e)

async def trigger_check(): #triggers sub_check for every server(guild) the bot is on
    await client.wait_until_ready()
    while not client.is_closed():
        with open('servers.txt', 'r') as f:
            data = json.load(f)

        check = True
        n = 0
        while (check):
            try:
                sid = data['servers'][n]['sid']
                cid = data['servers'][n]['def_channel']

                await sub_check(sid, cid)


            except IndexError:
                check = False
            n += 1

        await asyncio.sleep(60)

async def add_sub(name,channel): #adds a twitch channel to subscriptions file assigned to a specific server(guild)
    if verify_user(name):
        if not check_for(name, channel.guild.id):
            filename = str(channel.guild.id) + 'subs.txt'
            user = {
                'name': name,
                'mentioned': 'false'
            }
            if os.path.isfile(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)

                data['subs'].append(user)

                with open(filename, 'w')as file:
                    json.dump(data, file)
            else:
                dicc = {}
                dicc['subs'] = []
                dicc['subs'].append(user)
                with open(filename, 'w+')as f:

                    json.dump(dicc,f)
            await channel.send('Succesfully added ' + name)
        else:
            await channel.send("User is already in your subscriptions")
    else:
        await channel.send("Invalid user. Prove me wrong by subscribing with the name provided in the twitch link.")

async def remove_sub(name,channel): #Removes a twitch channel from a subscriptions file assigned to a specific server
    check = True
    n = 0
    sid = channel.guild.id
    found = False
    filename = str(sid) + "subs.txt"
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        f.close()

        while(check):
            try:
                if data['subs'][n]['name'] == name:
                    data['subs'].remove(data['subs'][n])
                    found = True
            except IndexError:
                check = False

            n += 1

        with open(filename,'w')as file:
            try:
                json.dump(data, file)
            except PermissionError:
                pass
        if not found:
            await channel.send("You are not subscribed to that user :(")
        else:
            await channel.send("Succesfully removed " + name)
    else:
        await channel.send("Can't remove a subscription if there are none.")

async def show_subs(channel): #Sends a list of server's subscribed channels to a before mentioned server
    filename = str(channel.guild.id) + 'subs.txt'

    if os.path.isfile(filename):

        with open(filename, 'r') as f:
            data = json.load(f)


        check = True
        n = 0
        msg = "Here are your subscriptions: \n"

        while(check):
            try:
                msg += data['subs'][n]['name'] + '\n'
            except IndexError:
                check = False
                if n == 0:
                    await channel.send("You are not subscribed to anyone :( ")
                else:
                    await channel.send(msg)
            n += 1


    else:
        await channel.send("You are not subscribed to anyone :(")

def check_for(name,id): #checks if a channel is already subscribed by a specific server. Prevent users from adding the same channel more than one time
    filename = str(id) + 'subs.txt'
    found = False
    if os.path.isfile(filename):
        with open(filename,'r') as f:
            data = json.load(f)
        f.close()

        check =  True

        n = 0
        while(check):
            try:
                if data['subs'][n]['name'] == name:
                    found = True
            except IndexError:
                check = False
            n +=1
    return found

async def change_def(sid,channel): #Changes the 'def_channel' variable in 'servers.txt'. Changes the channel twitch alerts are sent to.
    cid = channel.id
    with open('servers.txt','r') as f:
        data = json.load(f)

    check = True
    n = 0
    while(check):
        try:
            if data['servers'][n]['sid'] == sid:
                data['servers'][n]['def_channel'] = cid
        except IndexError:
            check = False
        n +=1
    try:
        with open('servers.txt', 'w') as file:
            json.dump(data,file)
            await channel.send("This is now the default channel for twitch alerts.")
    except PermissionError:
        pass

@client.event

async def on_message(message):

    if not message.author.bot:
        if message.content[0] == "*":
            if message.content.find("*change_alert_channel") != -1:
                if message.author == message.channel.guild.owner:
                    await change_def(message.channel.guild.id, message.channel)
                else:
                    await message.channel.send("You are not allowed to use this command")
            if message.content.find("*add") != -1:
                content = message.content
                c2 = content.replace("*add", "")
                c3 = c2.replace(" ","")

                await add_sub(c3,message.channel)
            if message.content.find("*remove") != -1:
                content = message.content
                c2 = content.replace("*remove", "")
                c3 = c2.replace(" ","")

                await remove_sub(c3,message.channel)
            if message.content.find("*showsubs") != -1:
                await show_subs(message.channel)
            if message.content.find("*help") != -1:
                await message.channel.send(help)

@client.event
async def on_guild_join(server):
    channel = server.text_channels[0]

    if os.path.isfile('servers.txt'):
        with open('servers.txt', 'r') as file:
            data = json.load(file)
            serv = {
                'sid': server.id,
                'def_channel': channel.id
            }
            data['servers'].append(serv)
        with open('servers.txt','w') as f:
            json.dump(data,f)

    else:
        with open('servers.txt', 'w+') as file:
            servers_list = {}
            servers_list['servers'] = []
            serv = {
                'sid' : server.id,
                'def_channel' : channel.id
            }
            servers_list['servers'].append(serv)
            json.dump(servers_list,file)
    filename = str(server.id) + 'subs.txt'
    dicc = {}
    dicc['subs'] = []

    with open(filename, 'w+')as f:
        json.dump(dicc, f)

@client.event
async def on_guild_remove(server):
    sid = server.id
    with open('servers.txt','r+') as file:
        data = json.load(file)
        check = True
        id = 0
        while(check):
            try:
                if data['servers'][id]['sid'] == sid:
                    dicks = data['servers'][id]
                    data['servers'].remove(dicks)
                id +=1
            except IndexError:
                check = False
    with open('servers.txt', 'w+') as f:
        json.dump(data,f)
        filename = str(server.id) + 'subs.txt'
    if os.path.isfile(filename):
        os.remove(filename)



client.loop.create_task(trigger_check())
client.run(token)
