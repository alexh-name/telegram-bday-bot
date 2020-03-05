#!/usr/bin/env python
# -*- coding: utf-8 -*-

botToken = 'XXX'
monPicRelPath = './mons/'

import random, os, logging
from PIL import Image, ImageOps
from pathlib import Path
from telegram.ext import Updater

home = str(Path.home())
os.chdir(home)

updater = Updater(token=botToken, use_context=True)

dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

###

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

from telegram.ext import CommandHandler
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
from telegram.ext import MessageHandler, Filters

###

def bday(update, context):
    name = context.args[0]
    pre = '🎈🎉🎊 Happy Birthday '
    sub = '! Have a wonderful day! 🎊🎉🎈'
    q = '\nWould you like to get a birthday picture? Then reply to one of my messages with \'bdaypic pls\' 😊'
    context.bot.send_message(chat_id=update.effective_chat.id, text= pre + name + sub + q)

bday_handler = CommandHandler('bday', bday)
dispatcher.add_handler(bday_handler)

###

def genPic(pic, position):
    # pic is the profile pic
    monPic = Image.open(monPicRelPath + random.choice(os.listdir(monPicRelPath)))
    # for left position we need to mirror the monPic
    if position == 'left':
        monPic = ImageOps.mirror(monPic)

    # scale
    if monPic.height > monPic.width:
        factor = pic.height / monPic.height
    else:
        factor = pic.width / monPic.width
    if monPic.width < pic.width or monPic.height < pic.height:
        monPic = monPic.resize((int(monPic.width * factor * 0.5), int(monPic.height * factor * 0.5)))
    else:
        monPic = monPic.resize((int(monPic.width / factor), int(monPic.height / factor)))

    monPic = monPic.convert("RGBA")

    # now paste monPic on pic in corner corresponding to "position" and add 2% margin
    margin = 0.02
    vertOffset = pic.height - monPic.height - int(pic.height * margin)
    if position == 'left':
        horOffset = int(pic.width * margin)
    else:
        horOffset = pic.width - monPic.width - int(pic.width * margin)

    # also use monPic as mask, as it's not a rectangle
    pic.paste(monPic, (horOffset, vertOffset), monPic)

    return pic

def bdayPic(update, context):
    # get user info
    user = update.message.from_user
    # use @username if avaiable
    if user['username']:
        name = '@' + user['username']
    # if not, first and last name
    else:
        if user['first_name']:
            name = user['first_name']
        if user['last_name']:
            if name:
                name = name + ' ' + user['last_name']
            else:
                name = user['last_name']
    id = user['id']
    pre = '🥳 Here you go '
    sub = ' 🥳'
    # get the profile pic, but only the current one
    photo = context.bot.get_user_profile_photos(user_id=id, limit=1)
    # "photo" is a telegram PhotoSize object with a photos attribute
    # the attribute is a list of a list. only the current photo concerns us
    # so we choose the first (and only) list item
    # this will have a list of items with different resolutions.
    # we want the highest res, so last item of the list
    # that item has then a dict including file_id etc.
    photoFile = photo.photos[0][-1].get_file()
    # prepare a path for download
    photoDir = '/tmp/bdaybot/' + str(update.effective_chat.id) + '/'
    Path(photoDir).mkdir(parents=True, exist_ok=True)
    # download
    photoPath = photoFile.download(custom_path=photoDir + str(id))

    context.bot.send_message(chat_id=update.effective_chat.id, text=pre + name + sub)

    # back is the profile pic
    back = Image.open(photoPath)
    # use are genPic routine to add a mon left and right
    back = genPic(back, 'left')
    back = genPic(back, 'right')
    # add file extension for PIL to know which format to use
    photoPathNew = photoPath + '.png'
    back.save(photoPathNew)
    # send pic
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(photoPathNew, 'rb'))
    # remove pic
    os.remove(photoPath)
    os.remove(photoPathNew)


bdayPic_handler = MessageHandler(Filters.reply & Filters.text & Filters.regex('^bday[pP]ic (pls|please)(\!)*'), bdayPic)
#bdayPic_handler = MessageHandler(Filters.reply & Filters.text & Filters.regex('^[yY][eE][sS](\!)*'), bdayPic)
#bdayPic_handler = CommandHandler('bdayPic', bdayPic)
dispatcher.add_handler(bdayPic_handler)

###

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)


updater.start_polling()

updater.idle()

