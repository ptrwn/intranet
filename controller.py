import os
import logging
import datetime as dt
import requests
import random
from requests.exceptions import RequestException, Timeout
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler
from main import Engineers, config, TrustedChats, Session
from googleapiclient.discovery import build
import random


os.makedirs("tmp/cat/", exist_ok=True)
os.makedirs("tmp/dog/", exist_ok=True)


logger = logging.getLogger()
handler = logging.FileHandler('main.log')
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)

if config['MAIN']['Debug'] == 'True':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
else:
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

TOKEN = config['TELEGRAM']['Token']


def is_trusted(tchatid):
    session = Session()
    q = session.query(TrustedChats).filter(
        TrustedChats.chat_id == str(tchatid)
    )
    session.close()
    if q.count():
        return True
    return False


updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher


def start(bot, update):
    if is_trusted(update.message.chat_id):
        bot.send_message(chat_id=update.message.chat_id, text="I trust you, \
        go on")
    else:
        logger.info('Request \'Start\' from: '+str(update.message.chat_id))
        bot.send_message(chat_id=update.message.chat_id, text="You are not \
        trusted, give this id to @KirillShirolapov to be added: {}".format(
            update.message.chat_id))


def whoshere(bot, update):
    result = False
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    if is_trusted(update.message.chat_id):
        res = '<b>These engineers are on shift now:</b>\n\n'
        engs = Engineers()
        eng_l = engs.get_engineer_now()
        for item in eng_l:
            res += item[0]
            for spec in item[1]:
                res += ' ' + '<b>' + spec + '</b>,'
            if res[-1] == ',':
                res = res[:-1]
            res += '\n'

        result = True
        bot.send_message(chat_id=update.message.chat_id, text=res,
                         parse_mode=ParseMode.HTML)
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You are not \
            authorised to perform this action")
    logger.info('Unauth request who is here from: '+str(
        update.message.chat_id)+' Result: '+str(result))


def whostl(bot, update):
    result = False
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    if is_trusted(update.message.chat_id):
        res = '<b>Shared TLs IP phone: 70777. These TLs are on shift now:</b>\n\n'
        engs = Engineers()
        eng_l = engs.get_tl_now()
        for item in eng_l:
            res += item[0]
            res += ', '+'IP phone: '+str(item[1])+','
            for spec in item[2]:
                res += ' ' + '<b>' + spec + '</b>,'
            if res[-1] == ',':
                res = res[:-1]
            res += '\n'

        result = True
        bot.send_message(chat_id=update.message.chat_id, text=res,
                         parse_mode=ParseMode.HTML)
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You are not \
            authorised to perform this action")
    logger.info('Unauth request  who TL from: '+str(update.message.chat_id) +
                ' Result: '+str(result))


def whossme(bot, update):
    result = False
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    if is_trusted(update.message.chat_id):
        res = '<b>These SMEs are on shift now:</b>\n\n'
        engs = Engineers()
        eng_l = engs.get_sme_now()
        for item in eng_l:
            res += item[0]
            for spec in item[1]:
                res += ' ' + '<b>' + spec + '</b>,'
            if res[-1] == ',':
                res = res[:-1]
            res += '\n'
        result = True
        bot.send_message(chat_id=update.message.chat_id, text=res,
                         parse_mode=ParseMode.HTML)
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You are not \
            authorised to perform this action")
    logger.info('Unauth request who SME from: '+str(
        update.message.chat_id)+' Result: '+str(result))


def cat(bot, update):
    result = False
    if is_trusted(update.message.chat_id):
        result = True
        try:
            contents = requests.get('http://aws.random.cat/meow', timeout=5).json()
            url = contents['file']
            file_name = url.split('/')[-1]
            logging.debug("All ok")
        except Timeout:
            logging.error("Time out while request cat")
            list_cat = os.listdir("tmp/cat/")
            if len(list_cat) > 0:
                file_name = random.choice(list_cat)
            else:
                logging.error("No cats in tmp dir")
                return
        except RequestException:
            logging.error("Many error while request cat")
            return
        exp_url = file_name[-4:]
        if not os.path.isfile('tmp/cat/'+file_name):
            r = requests.get(url, allow_redirects=True)
            open('tmp/cat/'+file_name, 'wb').write(r.content)
        if exp_url == '.mp4':
            bot.send_chat_action(chat_id=update.message.chat_id,
                                 action='upload_video')
            bot.send_video(chat_id=update.message.chat_id,
                           video=open('tmp/cat/'+file_name, 'rb'))
        elif exp_url == '.gif':
            bot.send_chat_action(chat_id=update.message.chat_id,
                                 action='upload_video')
            bot.send_document(chat_id=update.message.chat_id,
                              document=open('tmp/cat/'+file_name, 'rb'))
        else:
            bot.send_chat_action(chat_id=update.message.chat_id,
                                 action='upload_photo')
            bot.send_photo(chat_id=update.message.chat_id,
                           photo=open('tmp/cat/'+file_name, 'rb'))
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Prepare Uranus")
    logger.info('Unauth request Cat from: '+str(
        update.message.chat_id)+' Result: '+str(result))


def dog(bot, update):
    result = False
    if is_trusted(update.message.chat_id):
        result = True
        contents = requests.get('https://random.dog/woof.json').json()
        url = contents['url']
        exp_url = url[-4:]
        file_name = url.split('/')[-1]
        if not os.path.isfile('tmp/dog/'+file_name):
            r = requests.get(url, allow_redirects=True)
            open('tmp/dog/'+file_name, 'wb').write(r.content)
        if exp_url == '.mp4':
            bot.send_video(chat_id=update.message.chat_id,
                           video=open('tmp/dog/'+file_name, 'rb'))
        elif exp_url == '.gif':
            bot.send_document(chat_id=update.message.chat_id,
                              document=open('tmp/dog/'+file_name, 'rb'))
        else:
            bot.send_photo(chat_id=update.message.chat_id,
                           photo=open('tmp/dog/'+file_name, 'rb'))
    logger.info('Unauth request Dog from: '+str(
        update.message.chat_id)+' Result: '+str(result))


DEVELOPER_KEY = config['GOOGLE']['DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

prefix = ['ricardo ', 'рикардо ']
postfix = [' milos', ' милос']
postpostfix = [' flex ', ' флекс ']


def youtube_search():
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
    search_response = youtube.search().list(
         q=random.choice(prefix) +
         random.choice(postfix) +
         random.choice(postpostfix),
         part='snippet', maxResults=5).execute()

    videos = []
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append('%s' % (search_result['id']['videoId']))
    return (videos[random.randint(0, 2)])


def flex(bot, update):
    result = False
    if is_trusted(update.message.chat_id):
        bot.send_message(chat_id=update.message.chat_id,
                         text="https://www.youtube.com/watch?v=" +
                         youtube_search())
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Your \
            heterosexuality is not ready for this")
    logger.info('Unauth request Flex from: '+str(
        update.message.chat_id)+' Result: '+str(result))


def add_user(bot, update):
    root_from_set = config['TELEGRAM']['Root_users']
    root_from_set = root_from_set.split(',')
    is_root = False
    for id in root_from_set:
        if str(id) == str(update.message.chat_id):
            is_root = True
    if not is_root:
        return False
    text = update.message.text
    text = text.replace('/addUser ', '')
    text = text.split(' ')
    adding_chat_it = text[0]
    try:
        adding_user_name = text[1]
    except IndexError:
        adding_user_name = ''
    session = Session()
    q = session.query(TrustedChats).filter(
        TrustedChats.chat_id == str(adding_chat_it)
    )
    if q.count():
        bot.send_message(chat_id=update.message.chat_id,
                         text="This user already in base.")
        bot.send_message(chat_id=update.message.chat_id,
                         text="Bitch")
    else:
        myobject = TrustedChats(chat_id=str(adding_chat_it),
                                name=adding_user_name)
        session.add(myobject)
        session.commit()
        bot.send_message(chat_id=update.message.chat_id,
                         text="User was added.")
    session.close()


cat_handler = CommandHandler('cat', cat)
dispatcher.add_handler(cat_handler)

flex_handler = CommandHandler('flex', flex)
dispatcher.add_handler(flex_handler)

dog_handler = CommandHandler('dog', dog)
dispatcher.add_handler(dog_handler)

sme_handler = CommandHandler('getsme', whossme)
dispatcher.add_handler(sme_handler)

tl_handler = CommandHandler('gettl', whostl)
dispatcher.add_handler(tl_handler)

whoshere_handler = CommandHandler('who', whoshere)
dispatcher.add_handler(whoshere_handler)

add_user_handler = CommandHandler('addUser', add_user)
dispatcher.add_handler(add_user_handler)

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_polling()
