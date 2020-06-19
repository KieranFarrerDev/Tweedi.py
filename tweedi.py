from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from midiutil.MidiFile import MIDIFile
import numpy as np
import random
import pygame
import pygame.mixer
from time import sleep
from StringIO import StringIO
from textblob import TextBlob
import pandas as pd
import re

import twitter_credentials

tweetValues = {
  "content":'',
  "length":'',
  "retweets":'',
  "likes":'',
  "sentiment":''
}


# # # # TWITTER CLIENT # # # #
class TwitterClient():
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client


# # # # TWITTER AUTHENTICATER # # # #
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth

# # # # TWITTER STREAMER # # # #
class TwitterStreamer():
    """
    Class for streaming and processing live tweets.
    """
    def __init__(self):
        self.twitter_autenticator = TwitterAuthenticator()

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        # This handles Twitter authetification and the connection to Twitter Streaming API
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_autenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)

        # This line filter Twitter Streams to capture data by the keywords:
        stream.filter(track=hash_tag_list)


# # # # TWITTER STREAM LISTENER # # # #
class TwitterListener(StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """
    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True

    def on_error(self, status):
        if status == 420:
            # Returning False on_data method in case rate limit occurs.
            return False
        print(status)


class TweetAnalyzer():
    """
    Functionality for analyzing and categorizing content from tweets.
    """

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        # analysis is performed on cleaned tweet - via clean_tweet function
        analysis = TextBlob(self.clean_tweet(tweet))

        # if score is above 0 return 1 i.e good sentiment
        # if score is 0 return 0 i.e indifferent sentiment
        # if score is less than 0 return -1 i.e bad sentiment
        if analysis.sentiment.polarity > 0:
            return 1
        elif analysis.sentiment.polarity == 0:
            return 0
        else:
            return -1

    def tweets_to_data_frame(self, tweets):

        #collects the text content of each indivdual tweet
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])

        #assigns each value into respective dictionary directory
        tweetValues["content"] = [tweet.text for tweet in tweets]
        tweetValues["length"] = [len(tweet.text) for tweet in tweets]
        tweetValues["retweets"] = [tweet.favorite_count for tweet in tweets]
        tweetValues["likes"] = [tweet.retweet_count for tweet in tweets]


        #returns values to DataFrame
        return df


if __name__ == '__main__':

    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()
    api = twitter_client.get_twitter_client_api()


# # # # Hashtag Filtering  # # # #
"""
Scrapes data for a specified Hashtag
"""


    # query(q="") to specify the hashtag search. -filter:retweets removes retweets from results
    tweets = api.search (q="#NHS"+" -filter:retweets",count=100,lang="en")

    df = tweet_analyzer.tweets_to_data_frame(tweets)
    tweetValues["sentiment"] = [tweet_analyzer.analyze_sentiment(tweet) for tweet in df['tweets']]

    tweetValues['likes'] = [ int(x) for x in tweetValues['likes'] ]

    print("sum length of all tweets: ",sum(tweetValues['length']))
    print("sum total of likes from 100 tweets: ",sum(tweetValues['likes']))
    print("sum total of all retweets from 100 tweets: ",sum(tweetValues['retweets']))
    print("sentiment value of 100 tweets overall: ",sum(tweetValues['sentiment']))


# # # # MIDI creation  # # # #
"""
Manipulates the Gathered Data into MIDI Notes
"""

    # overall sentiment average dictates the starting tempo, the more positive the 100 tweets are percived the faster the tempo
    if sum(tweetValues['sentiment']) > 20:
        defaultTempo = 75
    elif sum(tweetValues['sentiment']) > 10:
        defaultTempo = 65
    else:
        defaultTempo = 55

    # Amount of overall characters used in the 100 tweets analysed dictates the duration of the notes, the lower value the lower the note duration
    # !midiUtil requires note length to be the same, so cannot make dynamic array with different duration values for each note as planned.
    if sum(tweetValues['length']) >= 12000:
        duration = 10
    elif sum(tweetValues['length']) >= 11000:
        duration = 6
    else:
        duration = 4


    # Create the MIDIFile Object
    memFile = StringIO()
    MyMIDI = MIDIFile(1)

    track = 0

    # time needs to go up in increments of 1 for each piece of data passed in
    time = 0
    print("Tempo: ",defaultTempo)

    MyMIDI.addTrackName(track,time,"TweediPy Track")
    MyMIDI.addTempo(track,time, defaultTempo)


    # takes value in each array and assigns the passed in value to the closest octave
    # in the specified key
    def closest(lst, K):

         lst = np.asarray(lst)
         idx = (np.abs(lst - K)).argmin()
         return lst[idx]

    adjustedVolume = []

    adjustedLikes = []
    adjustedLength = []
    adjustedRetweets = []
    finalValLength = []

    finalValRetweets = []
    finalValLikes = []
    timeArray = []


    # so each value in data arrays can be re-adjusted to closest 'C' or 'G' octave value
    # midi values from - http://faydoc.tripod.com/formats/mid.htm#midi_event_commands
    cAndGmajorValues = [48, 60, 72, 84, 96, 108, 120, 55, 67, 79, 91, 103, 115, 127]

    gMajorValues = [55, 67, 79, 91, 103]

    eMajorValues = [52,64,76,88]

    i = 0

    while i < len(tweetValues['length']):
        # -40 applied to a notes length to give more variety when findind closest note value in array
        adjustedLength.append(tweetValues['length'][i] - 40)

        adjustedRetweets.append ((tweetValues['retweets'][i] + 1) * 50)
        adjustedLikes.append ((tweetValues['likes'][i] + 1) * 50)

        finalValLength.append(closest(cAndGmajorValues, adjustedLength[i]))
        finalValRetweets.append(closest(eMajorValues, adjustedRetweets[i]))
        finalValLikes.append(closest(gMajorValues, adjustedLikes[i]))

        # if statement converts sentiment score i.e. -1,0,1 into use-able midi values
        if tweetValues['sentiment'][i] == 1:
            adjustedVolume.append (100)
        elif tweetValues['sentiment'][i] == 0:
            adjustedVolume.append (55)
        else:
            adjustedVolume.append (35)

        i+=1

    j = 0
    while j < len(adjustedVolume):

        MyMIDI.addNote(track,0,finalValLength[j],time,duration,adjustedVolume[j])
        MyMIDI.addNote(track,1,finalValRetweets[j],time,duration,(adjustedVolume[j]/2))
        MyMIDI.addNote(track,2,finalValLikes[j],time,duration,(adjustedVolume[j]/2))

        # if tweet is percived as 'positve' time between next note is less
        if tweetValues['sentiment'][j] == 1:
                time -= 1
                timeArray.append(time)
        # if tweet is percived as 'neutral' no change
        elif tweetValues['sentiment'][j] == 0:
                time += 0
                timeArray.append(time)
        # if tweet is percived as 'negative' make time between next is longer
        else:
                time += 2
                timeArray.append(time)
        time += 1
        j += 1

# # # # MIDIFile Saving To Local  # # # #
"""
Saving Output to MIDIFile
"""
    # binfile = open("FileName.midi", 'wb')
    # MyMIDI.writeFile(binfile)
    # binfile.close()


# # # # MIDIFile Playing in terminal  # # # #
"""
PLaying generated MIDI
"""
    MyMIDI.writeFile(memFile)
    pygame.init()
    pygame.mixer.init()
    memFile.seek(0)
    pygame.mixer.music.load(memFile)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        sleep(1)

    print "Done!"
