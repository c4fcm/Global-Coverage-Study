import sys, time, logging, ConfigParser, json, string, math, operator, os
from nltk.tokenize import word_tokenize, sent_tokenize
import nltk
import mediacloud.api
from mediameter.db import GeoStoryDatabase
from iso3166 import countries
from mediameter import stopwords    # Ali's combo module
import pandas as pd

'''
TODO: We could speed this up by pulling a random sample of stories, instead of doing them all
'''

DO_IF_IDF = True
DO_PEOPLE = True

start_time = time.time()

english_stop_words = stopwords.getStopWords()

# load shared config file
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config = ConfigParser.ConfigParser()
config.read(parent_dir+'/mc-client.config')

# connect to database
db = GeoStoryDatabase(config.get('db','name'),
    config.get('db','host'))

# load estimate data, change index to country alpha3
estimate_file = os.path.join(parent_dir, 'analysis/output/estimate.csv')
estimate_df = pd.DataFrame.from_csv(estimate_file)
estimate_df.set_index("X")

output = [] # the thing to jsonify at the end

def count_incidence(lookup, term):
    if term in lookup:
        lookup[term] += 1
    else:
        lookup[term] = 1

def add_idf(idf, term, count):
    idf[term] = count

# get list of all media sources
print "Starting to generate json"
media_counts = db.mediaTypeStoryCounts()
for media_type, media_story_count in media_counts.iteritems():
    print "  Working on "+media_type+" type ("+str(media_story_count)+" articles)"
    info = {
        'mediaType': media_type,
        'totalArticleCount': media_story_count,
    }
    # setup tfidf computation
    doc_by_country = {}         # maps alpha2 to document (country nltk.Text)
    term_doc_incidence = {}     # maps term to number of documents (country nltk.Text) it appears in
    idf = {}                    # maps term to inverse document frequency
    all_countries = db.allAboutCountries(media_type)
    if DO_IF_IDF:
        print "    Computing TF and IDF"
        total_countries = len(all_countries)
        for country in all_countries:
            country_code = country
            count = db.storiesOfType(media_type,country_code).count()
            country_stopwords = []
            try:
                country_iso3166 = countries.get(country_code)
                country_stopwords.append( country_iso3166.name.lower() )
            except KeyError:
                country_stopwords = []  
            # fetch and put back together the stories
            print "      fetch "+country_code
            print "        ("+str(db.storiesOfType(media_type, country_code).count())+" stories) "
            print "        create text"
            country_stories_text = ' '.join( [story['story_text'] for story in db.storiesOfType(media_type, country_code)] )
            # nltk-ize it
            print "        nltk "
            doc = nltk.Text([ \
                word.encode('utf-8') \
                    for sent in sent_tokenize(country_stories_text.lower()) for word in word_tokenize(sent) \
                    if word not in english_stop_words and word not in string.punctuation and word not in country_stopwords])
            # compute the document tf 
            print "        doc tf "
            doc_term_count = len(doc.vocab().keys())
            print "        ("+str(doc_term_count)+" terms)"
            doc_by_country[country_code] = doc
        print "      computing df"
        [count_incidence(term_doc_incidence,term) \
            for country_doc in doc_by_country.values() \
            for term in country_doc.vocab().keys() ]
        print "       done "
        print "       computing idf"
        idf = { term: math.log(float(total_countries)/float(incidence)) for term, incidence in term_doc_incidence.iteritems() }
        print "       done "
        print "    done setting up text collection for media "+media_type

    # now create results we care about
    print "    Computing info for each country"
    count_by_country = []
    parsed_article_count = 0
    total_stories = db.allStories().count()
    for country in all_countries:
<<<<<<< Updated upstream
        country_code = country
        country_story_count = db.storiesOfType(media_type,country_code).count()
        print "    "+country_code+": "+str(country_story_count)+" stories"

=======
>>>>>>> Stashed changes
        # setup country-specific info
        country_code = country['countryCode']
        country_alpha3 = None
        try:
            country_iso3166 = countries.get(country_code)
            country_alpha3 = country_iso3166.alpha3
        except KeyError:
            # not sure how to handle things that aren't fully approved, like XK for Kosovo :-(
            print '      Unknown country code '+country_code
            country_alpha3 = None           

        country_story_count = db.storiesOfType(media_type,country_code).count()
        try:
            country_estimate = estimate_df[country_alpha3,"estimate"]
        except KeyError:
            pass
        print "    "+country_code+": "+str(country_story_count)+" stories"
        
        tfidf_results = []
        if DO_IF_IDF:
            # compute document term frequency for stories about this country from this media source
            print "      Calculating tfidf for country "+country_code
            doc_tf = doc_by_country[country_code].vocab()
            tfidf = { term: frequency * idf[term] for term, frequency in doc_tf.iteritems() }
            print "       done"
            tfidf_results = [ {'term': term, 'count':freq} \
                for term, freq in sorted(tfidf.iteritems(), key=operator.itemgetter(1), reverse=True)]\
                [:30]

        # put country-specific info together
        if country_alpha3 is not None:
            people_counts = []
            if DO_PEOPLE:
                all_people_counts = db.peopleMentioned(media_type, country_code)
                people_counts = [ { 'name': name, 'count':freq } \
                    for name, freq in sorted(all_people_counts.iteritems(), key=operator.itemgetter(1), reverse=True)]\
                    [:30]
            result
            country_result = {
                'alpha3': country_alpha3
                , 'count': country_story_count
                , 'people': people_counts
                , 'tfidf': tfidf_results
            }
            if country_estimate is not None:
                country_result['estimate'] = total_stories * country_estimate
            count_by_country.append(country_result)
            parsed_article_count += country_story_count

    info['countries'] = count_by_country
    info['articleCount'] = parsed_article_count
    output.append(info)

print "Writing output"
with open("output/data.json", "w") as text_file:
    text_file.write(json.dumps(output))

print "  done (in "+str(time.time() - start_time)+" seconds)"
