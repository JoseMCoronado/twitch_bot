from datetime import datetime
import threading
import random
import re
import sys
import irc.bot
import requests
import sqlite3
import musicpd
from flask import Flask, render_template, jsonify

app = Flask(__name__, static_folder='./static')

DATABASE = "bot.db"


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self):
        #TODO: Should we login into the first user?
        user_channel = "gfpsolutions"
        conn = connect_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('select client_id, client_secret, client_user, irc_token from user where client_user = ?', [user_channel])
        users = [dict(client_id=row[0], client_secret=row[1], client_user=row[2], irc_token=row[3]) for row in cur.fetchall()]
        conn.close()
        if not users:
            print(
                "Credentials for %s were not found in the database. Please restart and try again."
                % (user_channel)
            )
            sys.exit(1)
        credentials = users[0]

        client_user = user_channel
        self.client_secret = credentials["client_secret"]
        self.client_id = credentials["client_id"]
        self.token = credentials["irc_token"]
        self.channel = "#" + client_user

        print("Getting Access Token...")
        body = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        r = requests.post("https://id.twitch.tv/oauth2/token", body)
        keys = r.json()
        self.access_token = keys["access_token"]

        print("Getting Channel ID...")
        headers = {
            "Client-ID": self.client_id,
            "Authorization": "Bearer " + keys["access_token"],
        }
        user = requests.get(
            "https://api.twitch.tv/helix/users?login=" + client_user, headers=headers
        )
        user = user.json()
        self.channel_id = user["data"][0]["id"]

        print("Logging into IRC...")
        server = "irc.chat.twitch.tv"
        port = 6667
        irc.bot.SingleServerIRCBot.__init__(
            self, [(server, port, self.token)], client_user, client_user
        )
        print("Logging Successful!")

    def dict_from_row(self, row):
        return dict(zip(row.keys(), row))

    def on_welcome(self, c, e):
        print("Joining " + self.channel)

        # You must request specific capabilities before you can use them
        c.cap("REQ", ":twitch.tv/membership")
        c.cap("REQ", ":twitch.tv/tags")
        c.cap("REQ", ":twitch.tv/commands")
        c.join(self.channel)

    def on_pubmsg(self, c, e):
        # If a chat message starts with an exclamation point, try to run it as a command
        if e.arguments[0][:1] == "!":
            cmd = e.arguments[0].split(" ")[0][1:]
            print("Received command: " + cmd)
            self.do_command(e, cmd)
        return

    def typing_user(self, e):
        type_user = list(filter(lambda tag: tag["key"] == "display-name", e.tags))[0][
            "value"
        ]
        return type_user

    def is_privaleged_user(self, e):
        type_user = list(filter(lambda tag: tag["key"] == "user-type", e.tags))[0][
            "value"
        ]
        entry_user = self.typing_user(e)
        if type_user == "mod" or entry_user == "GFPSolutions" or entry_user == "Prosolis":
            return True
        return False

    def strip_users(self, e):
        list_users = e.arguments[0].split(" ")
        list_users = [l if "@" in l else None for l in list_users]
        list_users.remove(None)
        return list_users

    def get_channel_info(self):
        url = "https://api.twitch.tv/kraken/channels/" + self.channel_id
        headers = {
            "Client-ID": self.client_id,
            "Accept": "application/vnd.twitchtv.v5+json",
        }
        r = requests.get(url, headers=headers).json()
        return r
    
    def stop():
        print("WHAHKJSHDKJASHDJKS")
        print("WHAHKJSHDKJASHDJKS")
        print("WHAHKJSHDKJASHDJKS")
        print("WHAHKJSHDKJASHDJKS")
        print("WHAHKJSHDKJASHDJKS")
        print("WHAHKJSHDKJASHDJKS")

    def do_command(self, e, cmd):
        try:
            c = self.connection

            """ START MPD COMMANDS """
            if cmd ==  "play":
                if self.is_privaleged_user(e):
                    mpdcli = mpd_connect()
                    mpdcli.play()
                    mpdcli.disconnect()
            if cmd ==  "stop":
                if self.is_privaleged_user(e):
                    mpdcli = mpd_connect()
                    mpdcli.stop()
                    mpdcli.disconnect()
            if cmd ==  "delete":
                if self.is_privaleged_user(e):
                    parsed_message = e.arguments[0].split(" ")
                    if len(parsed_message) < 2:
                        c.privmsg(
                            self.channel,
                            "Usage: `!delete [song id]",
                        )
                        return True
                    mpdcli = mpd_connect()
                    mpdcli.deleteid(parsed_message[1])
                    mpdcli.disconnect()
            if cmd ==  "shuffle":
                if self.is_privaleged_user(e):
                    mpdcli = mpd_connect()
                    mpdcli.shuffle()
                    mpdcli.disconnect()
            if cmd ==  "pause":
                if self.is_privaleged_user(e):
                    mpdcli = mpd_connect()
                    mpdcli.pause()
                    mpdcli.disconnect()
            if cmd ==  "next":
                if self.is_privaleged_user(e):
                    mpdcli = mpd_connect()
                    mpdcli.next()
                    mpdcli.play()
                    mpdcli.disconnect()
            if cmd ==  "playlist":
                if self.is_privaleged_user(e):
                    mpdcli = mpd_connect()
                    mpdcli.iterate = True
                    songlist_message = ""
                    for song in mpdcli.playlistinfo():
                        songlist_message += "| id(%s) pos(%s) title(%s)" % (song['id'],int(song['pos']), song['title'])
                    c.privmsg(self.channel, songlist_message)
                    mpdcli.disconnect()
            if cmd ==  "searchadd":
                mpdcli = mpd_connect()
                parsed_message = e.arguments[0].split(" ")
                if len(parsed_message) < 3:
                    c.privmsg(
                        self.channel,
                        "Usage: `!searchadd [type: any|Artist|Album|AlbumArtist|Title|Track|Name|Genre|Date|Composer|Performer|Comment|Disc] [string]",
                    )
                    return True
                search_type = parsed_message[1]
                search_string = parsed_message[2]
                search_list = mpdcli.searchadd(search_type,search_string)
                message = "Song added..."
                c.privmsg(self.channel, message)

            if cmd ==  "search":
                mpdcli = mpd_connect()
                parsed_message = e.arguments[0].split(" ")
                if len(parsed_message) < 3:
                    c.privmsg(
                        self.channel,
                        "Usage: `!search [type: any|Artist|Album|AlbumArtist|Title|Track|Name|Genre|Date|Composer|Performer|Comment|Disc] [string]",
                    )
                    return True
                search_type = parsed_message[1]
                search_string = parsed_message[2]
                search_list = mpdcli.search(search_type,search_string)
                if search_list:
                    message = str(search_list)
                else:
                    message = "No song found..."
                c.privmsg(self.channel, message)
            if cmd ==  "searchplaylist":
                mpdcli = mpd_connect()
                parsed_message = e.arguments[0].split(" ")
                if len(parsed_message) < 3:
                    c.privmsg(
                        self.channel,
                        "Usage: `!searchplaylist [type: any|Artist|Album|AlbumArtist|Title|Track|Name|Genre|Date|Composer|Performer|Comment|Disc] [string]",
                    )
                    return True
                search_type = parsed_message[1]
                search_string = parsed_message[2]
                search_list = mpdcli.playlistsearch(search_type,search_string)
                if search_list:
                    next_song = search_list[0]
                    message = "Position: %s | %s | %s | ~ %s min| ID: %s" % (next_song['pos'],next_song['title'],next_song['genre'],round(float(next_song['time'])/60,2),next_song['id'])
                else:
                    message = "No song found..."
                c.privmsg(self.channel, message)
            if cmd ==  "nextsong":
                mpdcli = mpd_connect()
                current_dict = mpdcli.currentsong()
                current_song_pos = int(current_dict['pos'])
                mpdcli.iterate = True
                playlist = list(mpdcli.playlistinfo())
                playlist_count = len(playlist) - 1
                if current_song_pos >= playlist_count:
                    next_song_pos = '0'
                else:
                    next_song_pos = str(current_song_pos + 1)
                next_song = list(filter(lambda b: b['pos'] == next_song_pos, playlist))[0]
                if len(next_song) >= 1:
                    next_song_message = "%s | %s | ~ %s min" % (next_song['title'],next_song['genre'],round(float(next_song['time'])/60,2))
                    c.privmsg(self.channel, next_song_message)
                else:
                    c.privmsg(self.channel, "There isn't a next song...")
                mpdcli.disconnect()

            if cmd ==  "currentsong":
                mpdcli = mpd_connect()
                current_dict = mpdcli.currentsong()
                curr_song_message = "%s | %s | ~ %s min" % (current_dict['title'],current_dict['genre'],round(float(current_dict['time'])/60,2))
                c.privmsg(self.channel, curr_song_message)
                mpdcli.disconnect()
            """ END MPD COMMANDS """
            # Provide List of commands
            if cmd == "commands" or cmd == "command":
                command_message = "Mod Commands: !so | !newcounter | !updatecounter |"
                c.privmsg(self.channel, command_message)
                command_message = "User Commands: !dance | !counter | !listcounters | !lurk | !unlurk | !quote | !dice | !game | !title |"
                c.privmsg(self.channel, command_message)

            # Pyramid
            elif cmd == "realpyramid":
                type_user = list(filter(lambda tag: tag["key"] == "display-name", e.tags))[
                    0
                ]["value"]
                print(type_user)
                parsed_message = e.arguments[0].split(" ")
                content_size = 3
                if len(parsed_message) >= 3:
                    try:
                        content_size = abs(int(parsed_message[2]))
                        if content_size > 5 and type_user != "GFPSolutions":
                            content_size = 5
                    except Exception as e:
                        print(e)
                if len(parsed_message) >= 2:
                    content = parsed_message[1]
                else:
                    content = "SquirtleJam"
                index_max = content_size
                decline = False
                index = 0
                while content_size > 0:
                    index += 1
                    message_content = ""
                    if not decline:
                        for i in range(index):
                            message_content += " " + content
                    else:
                        content_size -= 1
                        message_content = ""
                        for i in range(content_size):
                            message_content += " " + content
                    c.privmsg(self.channel,message_content)
                    if index == index_max:
                        decline = True
                    #print(message_content)
        
            # Blame prosolis
            elif cmd == "blameprosolis":
                type_user = self.typing_user(e)
                c.privmsg(
                    self.channel,
                    'Did something break? Did something go wrong? Or are you just having a bad day? This channel recommends that you just blame Prosolis! "Why?", you ask. The better question is: "Why not Prosolis?"'
                )
            # Blame prosolis
            elif cmd == "blameradmuddy":
                type_user = self.typing_user(e)
                c.privmsg(
                    self.channel,
                    'Were you so close to beating the final boss of the video game to just get rekt at the very end due to a redeem? Then...just blame Radmuddy...she will redeem 10 minutes of reverse reverse and no glasses to guarantee your loss!'
                )
            # Blame prosolis
            elif cmd == "blameray":
                type_user = self.typing_user(e)
                c.privmsg(
                    self.channel,
                    'Did a twitch fight start because some emote was removed from the people and made exclusive to some? Then...just blame Ray for making the Oobaby T2 emote!'
                )
            # Create Counter
            elif cmd == "newcounter":
                if self.is_privaleged_user(e):
                    parsed_message = e.arguments[0].split(" ")
                    if len(parsed_message) < 3:
                        c.privmsg(
                            self.channel,
                            "Usage: `!newcounter [counter name] [counter type]",
                        )
                        return True

                    counter_name = parsed_message[1]
                    counter_type = parsed_message[2]
                    r = self.get_channel_info()
                    counter_vals = {
                        "name": counter_name,
                        "game": r["game"],
                        "count": 0,
                        "count_type": counter_type,
                    }
                    Counter.create(counter_vals)
                    search_vals = {
                        "name": counter_name,
                        "count_type": counter_type,
                    }
                    record = Counter.get(search_vals)
                    c.privmsg(
                        self.channel,
                        "New Counter Created for %s: %s %s"
                        % (record["game"], record["name"], record["count_type"]),
                    )

            # Update Counter
            elif cmd == "updatecounter":
                # if True:
                #if self.is_privaleged_user(e):
                if True:
                    parsed_message = e.arguments[0].split(" ")
                    if len(parsed_message) < 2:
                        c.privmsg(
                            self.channel,
                            "Usage: `!updatecounter [counter name] [optional: integer]`",
                        )
                        return True

                    counter_name = parsed_message[1]
                    try:
                        increase = int(parsed_message[2])
                    except Exception:
                        increase = 1

                    r = self.get_channel_info()
                    search_vals = {
                        "name": counter_name,
                        "game": r["game"],
                    }
                    record = Counter.get(search_vals)
                    if not record:
                        c.privmsg(
                            self.channel,
                            "Counter: counter %s does not exist for %s."
                            % (counter_name, r["game"]),
                        )
                        return True
                    past_value = record["count"]
                    current_value = record["count"] + increase

                    update_vals = {
                        "count": current_value,
                    }
                    Counter.write(search_vals, update_vals)

                    search_vals = {
                        "game": r["game"],
                        "name": counter_name,
                    }
                    record = Counter.get(search_vals)
                    c.privmsg(
                        self.channel,
                        "Counter %s Updated for %s: %s --> %s"
                        % (record["name"], record["game"], past_value, record["count"]),
                    )

            # Shout Out
            elif cmd == "so":
                if self.is_privaleged_user(e):
                    list_users = self.strip_users(e)
                    for user_so in list_users:
                        user_so = user_so.strip("@")
                        headers = {
                            "Client-ID": self.client_id,
                            "Authorization": "Bearer " + self.access_token,
                        }
                        user = requests.get(
                            "https://api.twitch.tv/helix/users?login=" + user_so,
                            headers=headers,
                        )
                        user = user.json()
                        c.privmsg(
                            self.channel,
                            "You guys should checkout @%s: %s"
                            % (
                                user["data"][0]["display_name"],
                                user["data"][0]["description"],
                            ),
                        )

            # Get Counter Count
            elif cmd == "counter":
                parsed_message = e.arguments[0].split(" ")
                if len(parsed_message) < 2:
                    c.privmsg(
                        self.channel, "Usage: `!counter [counter name]",
                    )
                    return True
                counter_name = re.sub("[^A-Za-z0-9]+", "", parsed_message[1])
                r = self.get_channel_info()
                search_vals = {
                    "name": counter_name,
                    "game": r["game"],
                }
                record = Counter.get(search_vals)
                if not record:
                    c.privmsg(
                        self.channel,
                        "Counter: counter %s does not exist for %s."
                        % (counter_name, r["game"]),
                    )
                    return True

                c.privmsg(
                    self.channel,
                    "Counter %s for %s: %s" % (counter_name, r["game"], record["count"]),
                )
            elif cmd == "listcounters":
                r = self.get_channel_info()
                search_vals = {
                    "game": r["game"],
                }
                records = Counter.get(search_vals, all=True)
                if not records:
                    c.privmsg(
                        self.channel,
                        "Counter: %s does not have any counters available at the moment."
                        % (r["game"]),
                    )
                    return True

                counter_string = ""
                for counter_record in records:
                    counter_string += "%s (%s), " % (
                        counter_record["name"],
                        counter_record["count"],
                    )
                c.privmsg(
                    self.channel, "Counter for %s: %s" % (r["game"], counter_string),
                )

            # Dance
            elif cmd == "dance":
                type_user = list(filter(lambda tag: tag["key"] == "display-name", e.tags))[
                    0
                ]["value"]
                list_users = self.strip_users(e)
                selected_dance = random.randrange(1, 4, 1)
                if len(list_users) > 1:
                    list_users.append(type_user)
                    user_text = ", ".join(list_users)
                    dance_dictionary = {
                        1: "Its officially a dance party!!!! Squid1 Squid3 Squid4 GivePLZ TakeNRG GivePLZ TakeNRG Squid1 Squid3 Squid4 %s"
                        % (user_text),
                        2: "Its officially a dance party!!!! Squid1 Squid3 Squid4 GivePLZ TakeNRG GivePLZ TakeNRG Squid1 Squid3 Squid4 %s"
                        % (user_text),
                        3: "Its officially a dance party!!!! Squid1 Squid3 Squid4 GivePLZ TakeNRG GivePLZ TakeNRG Squid1 Squid3 Squid4 %s"
                        % (user_text),
                    }
                elif len(list_users) == 1:
                    dance_dictionary = {
                        1: "%s is dancing with %s, see them go! GivePLZ TakeNRG"
                        % (type_user, list_users[0]),
                        2: "Awww %s and %s are having so much fun dancing! mwaldenPiperhi mwaldenMilohi"
                        % (type_user, list_users[0]),
                        3: "Look at %s and %s's moves! Squid1 Squid3 Squid4 Squid1 Squid3 Squid4 "
                        % (type_user, list_users[0]),
                    }
                else:
                    dance_dictionary = {
                        1: "%s is dancing away Squid1 Squid2 Squid3 Squid2 Squid4"
                        % type_user,
                        2: "%s got the moves! GivePLZ" % type_user,
                        3: "%s is waddling around! mcd00dWaddle mcd00dDuck mcd00dWaddle "
                        % type_user,
                    }
                message = dance_dictionary[selected_dance]
                c.privmsg(self.channel, message)

            # Poll the Quote API to get some quotes
            elif cmd == "quote":
                list_users = e.arguments[0].split(" ")
                quote_count = 1
                if len(list_users) > 1:
                    if list_users[1] == "geico":
                        c.privmsg(
                            self.channel,
                            "Gecko Says 'You will save 15% or more on your home/auto insurance, only if you subscribe'%s",
                        )
                        return True
                    try:
                        quote_count = int(list_users[1])
                    except Exception:
                        quote_count = 1
                    if quote_count > 3:
                        quote_count = 3
                url = (
                    "https://goquotes-api.herokuapp.com/api/v1/random?count=%s"
                    % quote_count
                )
                r = requests.get(url).json()
                for quote in r["quotes"]:
                    c.privmsg(
                        self.channel,
                        "'%s' - %s (%s)" % (quote["text"], quote["author"], quote["tag"]),
                    )

            # Poll the API to get current game.
            elif cmd == "game":
                r = self.get_channel_info()
                c.privmsg(
                    self.channel, r["display_name"] + " is currently playing " + r["game"]
                )

            # Roll Dice
            elif cmd == "dice":
                type_user = self.typing_user(e)
                dice_roll = random.randrange(1, 7, 1)
                c.privmsg(self.channel, "%s rolls a %s!" % (type_user, dice_roll))

            # Lurk
            elif cmd == "lurk":
                type_user = self.typing_user(e)
                c.privmsg(
                    self.channel,
                    "Thanks for the lurk %s! Enjoy the stream in the background! HypeSneak"
                    % (type_user),
                )

            # Unlurk
            elif cmd == "unlurk":
                type_user = self.typing_user(e)
                c.privmsg(
                    self.channel,
                    "welcome back to the stream %s! mwaldenPiperhi" % (type_user),
                )

            # Poll the API the get the current status of the stream
            elif cmd == "title":
                url = "https://api.twitch.tv/kraken/channels/" + self.channel_id
                headers = {
                    "Client-ID": self.client_id,
                    "Accept": "application/vnd.twitchtv.v5+json",
                }
                r = requests.get(url, headers=headers).json()
                c.privmsg(
                    self.channel,
                    r["display_name"] + " channel title is currently " + r["status"],
                )

            # The command was not recognized
            else:
                pass
                #c.privmsg(self.channel, "Did not understand command: " + cmd)
        except Exception as e:
            print("Something went wrong: %s" % e)


@app.route('/')
def home():
   return render_template('index.html')

@app.route('/restart')
def restart():
    irc_online = False
    for id, thread in threading._active.items():
        if thread.name is "irc":
            irc_online = True
    if not irc_online:
        t2 = threading.Thread(target=init_irc)
        t2.setDaemon(True)
        t2.setName("flask")
        t2.start()
    else:
        print("IRC is already online...")
    return render_template('index.html')


@app.route('/users')
def list_users():
    conn = connect_db()
    c = conn.cursor()
    conn.row_factory = sqlite3.Row
   
    cur = conn.cursor()
    cur.execute("select * from user")
   
    rows = cur.fetchall();
    #TODO: Need to process raw output and pass only some values to the template
    conn.close()
    return render_template("users.html",rows = rows)

@app.route('/playlist')
def playlist():
    mpdcli = mpd_connect()
    rows = mpdcli.playlistinfo()
    mpdcli.disconnect()
    return render_template("playlist.html",rows = rows)

@app.route('/playlist_table')
def playlist_table():
    mpdcli = mpd_connect()
    rows = mpdcli.playlistinfo()
    mpdcli.disconnect()
    return jsonify(rows)

@app.route('/currentsong')
def current_song():
    mpdcli = mpd_connect()
    rows = mpdcli.currentsong()
    if rows and "id" in rows:
        current_song_id = int(rows['id'])
        top_song_id = int(list(mpdcli.playlistinfo())[0]['id'])
        if current_song_id != top_song_id:
            mpdcli.deleteid(top_song_id)
    mpdcli.disconnect()
    return jsonify(rows)

@app.route('/time')
def give_time():
   return jsonify(datetime.now())


def mpd_connect():
    mpdcli = musicpd.MPDClient()
    mpdcli.connect()
    return mpdcli

def connect_db():
    return sqlite3.connect(DATABASE, check_same_thread=False)

def init_db():
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute('CREATE TABLE IF NOT EXISTS user (id int, client_id text, client_secret text, client_user text, irc_token text)')
    except sqlite3.OperationalError as e:
        assert 'Something went wrong while initializing the db' in str(e)
    conn.commit()
    conn.close()

def init_irc():
    bot = TwitchBot()
    bot.start()

def runFlaskApp():
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

def main():
    t1 = threading.Thread(target=runFlaskApp)
    t2 = threading.Thread(target=init_irc)
    t2.setDaemon(True)
    t2.setName("flask")
    t2.setName("irc")
    t1.start()
    t2.start()

if __name__ == "__main__":
    main()
