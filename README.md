# Tweedi.py
#### Takes a given hashtag and outputs a dynamically Created piece of music.

## How to run the script
• Download both "tweedi.py" & "twitter_credentials" scripts.

• Replace Blank credentials in "twitter_credentials" with personal credentials.

• In "Tweedi.py" change line 143 to any hashtag of your choosing.


### Line 143: 
```
 tweets = api.search (q="#NHS"+" -filter:retweets",count=100,lang="en")
```

To save produced MIDI File: un-comment lines 270-272.

### Lines 270-272: 
```
    # binfile = open("FileName.midi", 'wb')
    # MyMIDI.writeFile(binfile)
    # binfile.close()
```
