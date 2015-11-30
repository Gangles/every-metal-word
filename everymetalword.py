#!/usr/bin/python
# -*- coding: utf-8 -*-

import config
import datetime
import logging
import math
import os
import random
import sys
import time
from PIL import Image, ImageDraw, ImageFont
from twython import Twython

def connectTwitter():
	# connect to twitter API
	return Twython(config.twitter_key, config.twitter_secret,
		config.access_token, config.access_secret)

def getNextWordIndex(twitter):
	# get the word index from the tweet count
	index = 1
	timeline = twitter.get_user_timeline(screen_name = config.bot_name)
	if len(timeline) > 0:
		index += int(timeline[0]['user']['statuses_count'])
	return index

def getNextWord(file_name, index):
	# line count of dictionary.txt, hard coded for performance
	assert index > 0 and index < 109158
	# get the word at the given line number
	with open(file_name) as source_fh:
		for i, word in enumerate(source_fh):
			if i == index:
				break
		return word.strip()

def post_tweet(twitter, to_tweet, image_name):
	# post the string and the image to twitter
	image = open(image_name, 'rb')
	response = twitter.upload_media(media=image)
	twitter.update_status(status=to_tweet, media_ids=[response['media_id']])

def getMetalEmoji(index):
	# add an emoji on every 10th tweet
	if index % 10 != 0: return ""

	emoji = [] # METAL EMOJI
	emoji.append(u" \U00002620") # skull & crossbones
	emoji.append(u" \U00002694") # crossed swords
	emoji.append(u" \U000026A1") # high voltage
	emoji.append(u" \U0001F3B8") # guitar
	emoji.append(u" \U0001F40D") # snake
	emoji.append(u" \U0001F480") # skull
	emoji.append(u" \U0001F577") # spider
	emoji.append(u" \U0001F918") # horns
	emoji.append(u" \U0001F982") # scorpion

	i = index // 10
	seed = i - (i % len(emoji))
	random.Random(seed).shuffle(emoji)
	return emoji[i % len(emoji)]

def getMetalFont(word, index, width=420):
	# pick a random font from the folder
	fonts = []
	for font in os.listdir('fonts'):
		if font.endswith('.ttf'):
			fonts.append(font)

	# prune certain fonts on short words
	if len(word) < 6:
		fonts.remove('Crucifixion.ttf')
		fonts.remove('HighVoltage.ttf')

	# use the same random seed
	seed = index - (index % len(fonts))
	random.Random(seed).shuffle(fonts)

	# choose a font from the random bag
	fontName = fonts[index % len(fonts)]
	fontPath = "fonts/%s" % fontName
	print "Using font: %s" % fontName

	# hack around a buggy font
	if len(word) < 15 and 'HighVoltage' in fontPath:
		width = 400

	# start font at size 30, then find best size
	fontSize = 30
	draw = ImageDraw.Draw(Image.new('RGBA', (width,220)))
	font = ImageFont.truetype(fontPath,fontSize)

	# increment font size quickly until text is too wide
	while draw.textsize(word, font=font)[0] < width:
		fontSize += 30
		font = ImageFont.truetype(fontPath,fontSize)

	# decrement font size slowly until text fits
	while draw.textsize(word, font=font)[0] > width:
		fontSize -= 3
		font = ImageFont.truetype(fontPath,fontSize)
	font = ImageFont.truetype(fontPath,fontSize)
	return font, draw.textsize(word, font=font)

def makeImage(word, index, image_name):
	# these fonts don't handle accents well
	print "Making image for: %s" % word
	word_safe = word.replace('é','e').replace('è','e').upper()
	font, size = getMetalFont(word_safe, index)

	# draw the text as an image, save as a GIF
	img = Image.new('RGBA', (440,size[1]),(255,255,255))
	draw = ImageDraw.Draw(img)
	x_offset = round((440 - size[0]) / 2)
	draw.text((x_offset,0), word_safe, (0,0,0), font=font)
	draw = ImageDraw.Draw(img)
	img.save(image_name, 'GIF', transparency=0)

def timeToWait():
	# tweet every 4 hours
	now = datetime.datetime.now()
	wait = 60 - now.second
	wait += (59 - now.minute) * 60
	wait += (3 - (now.hour % 4)) * 60 * 60;
	# tweet a little early if necessary
	if wait <= 10 * 60: wait = min(wait, 590)
	return wait

if __name__ == "__main__":
	# heroku scheduler runs every 10 minutes
	wait = timeToWait()
	print "Wait " + str(wait) + " seconds for next tweet"
	if wait > 10 * 60: sys.exit(0)

	try:
		# pick the next word in the dictionary
		twitter = connectTwitter()
		index = getNextWordIndex(twitter)
		word = getNextWord('dictionary.txt', index)

		# create a font image for it
		image_name = 'word.gif'
		makeImage(word, index, image_name)
		to_tweet = u"%s%s" % (word, getMetalEmoji(index))
		post_tweet(twitter, to_tweet, image_name)
		sys.exit(0) # success!
	except SystemExit as e:
		# working as intended, exit normally
		sys.exit(e)
	except:
		logging.exception(sys.exc_info()[0])

