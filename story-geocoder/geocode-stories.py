import logging, os, json, ConfigParser, sys
from operator import itemgetter
import requests
from mediameter.db import GeoStoryDatabase

logging.basicConfig(filename='geocoder.log',level=logging.DEBUG)
log = logging.getLogger('geocoder')
log.info("---------------------------------------------------------------------------")

# load shared config file
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config = ConfigParser.ConfigParser()
config.read(parent_dir+'/mc-client.config')

# connect to everything
db = GeoStoryDatabase(config.get('db','name'))

cliff_url = config.get('cliff','url')

# Query CLIFF to pull out entities from one story
def fetchEntitiesFromCliff(text):
	try:
		params = {'q':text}
		r = requests.get(cliff_url, params=params)
		entities = r.json()
		return entities
	except requests.exceptions.RequestException as e:
		print "ERROR RequestException " + str(e)

# Find records that don't have geodata and geocode them
for story in db.storiesWithoutCliffInfo():
	sorted_sentences = [s['sentence'] for s in sorted(story['story_sentences'], key=itemgetter('sentence_number'))]
	story_text = ' '.join(sorted_sentences)
	story['entities'] = fetchEntitiesFromCliff(story_text)
	db.updateStory(story)
	print "Saved " + str(story['_id']) + " - " + story['title'] + "..."
