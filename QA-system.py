#!/usr/bin/env python3

import requests
import fileinput
import spacy
import re


# returns a list with all IDs that matched with the keyword
def get_id(word, prop):
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    if prop:
        params['type'] = 'property'
    params['search'] = word.rstrip()
    json = requests.get(url, params).json()
    if not json['search']:
        print("Couldn't find any URI for: \'" + word + "\'")
        return 0
    else:
        #for result in json['search']:
        #    print("{}\t{}".format(result['id'],result['label']))
        #    if 'description' in result.keys():
        #        print(result['description'])
        return json['search']


# returns the type of part of the sentence that is required
def get_blank(token, type):
    part = []
    comp = True
    for d in token.subtree:
        #Nummod zodat hij Apollo 11 bijvoorbeeld goed scant. Amod is zodat hij wel bijvoeglijke naamwoorden meenement zoals atomic number.
        if d.dep_ == type or (d.dep_ == "compound" and comp) or (d.dep_ == "nummod" and d.head.lemma_ == token.lemma_) or (d.dep_ == "amod" and d.head.lemma_ == token.lemma_ and d.text != "many"):
            if d.dep_ == type:
                comp = False
                part.append(d.lemma_)
            #gedaan zodat hij bijvoorbeeld highest point niet high point van maakt maar gewoon highest point.
            else:
                part.append(d.text)
    return " ".join(part)


# returns the type of part of the sentence that is required
def check_regex_sentences(line):
    property = ""
    entity = ""
    type = ""
    #What does DNA stand for? / What does REM sleep stand for? These questions need to be fully written out.
    if re.search('What does (a |the ){0,1}(.*?) stand for', line):
        m = re.search('What does (a |the ){0,1}(.*?) stand for', line)
        entity = m.group(2)
        property = ""
        type = "regex2"
        return property, entity, type
    elif re.search('(.*?) (.*?) (a |the ){0,1}(.*?)($|\?| \?)', line):
        # Read the sentence with use of regex
        m = re.search('(.*?) (.*?) (a |the ){0,1}(.*?)($|\?| \?)', line)
        # filter the property and the entity
        entity = m.group(4)
        property = ""
        type = "regex1"
        return property, entity, type
    return property, entity, type


def get_keywords_when(parse):
    entity = ""
    property = ""
    for token in parse:
        # Als de zin begint met When
        if token.dep_ == "pobj":
            entity = get_blank(token, "pobj")
        if token.dep_ == "nsubj":
            entity = get_blank(token, "nsubj")
        if token.dep_ == "nsubjpass":
            entity = get_blank(token, "nsubjpass")
        if token.dep_ == "attr":
            property = get_blank(token, "attr")
        if token.dep_ == "dobj":
            entity = get_blank(token, "dobj")
        if token.pos_ == "VERB":
            if token.text.endswith('ed'):
                property = token.lemma_
            else:
                property = token.text

    return property, entity, "When"


def get_keywords_who(parse):
    entity = ""
    property = ""
    for token in parse:
        # Als de zin begint met Who
        if token.dep_ == "pobj":
            entity = get_blank(token, "pobj")
        if token.dep_ == "poss":
            entity = get_blank(token, "poss")
        if token.dep_ == "attr":
            property = get_blank(token, "attr")
        if token.dep_ == "dobj":
            entity = get_blank(token, "dobj")
        if token.pos_ == "VERB":
            property = token.lemma_

    return property, entity, "Who"

def get_keywords_which(parse):
    entity = ""
    property = ""
    found_entity = False
    found_property = False
    for token in parse:
        # Als de zin begint met When
        if token.dep_ == "pobj":
            entity = get_blank(token, "pobj")
        if token.dep_ == "nsubj":
            property = get_blank(token, "nsubj")
        if token.dep_ == "nsubjpass":
            property = get_blank(token, "nsubjpass")
        if token.dep_ == "dobj":
            entity = get_blank(token, "dobj")
        if token.dep_ == "attr":
            entity = get_blank(token, "attr")
        if property == "":
	        if token.dep_ == "VERB":
	            property = token.lemma_
        if entity == "":
	        entity = get_blank(token, "nsubj")
	        entity = get_blank(token, "nsubjpass")

    print("prop={} ent={}".format(property, entity))
    return property, entity, "Which"

def get_keywords_what(parse):
    entity = ""
    property = ""
    for token in parse:
        # Als de zin begint met What
        if token.dep_ == "pobj":
            entity = get_blank(token, "pobj")
        if token.dep_ == "nsubj":
            property = get_blank(token, "nsubj")

    return property, entity, "What"


#For example What does DNA consist of?/ What does the Dijkstra algorithm solve?
def get_keywords_what_does(parse):
    entity = ""
    property = ""
    for token in parse:
        if token.dep_ == "nsubj":
            entity = get_blank(token, "nsubj")
        if token.dep_ == "ROOT":
            property = token.text
        if token.dep_ == "nmod":
            entity = get_blank(token, "nmod")
    return property, entity, "What_does"


def get_keywords_where(parse):
    entity = ""
    property = ""
    for token in parse:
        # Als de zin begint met where
        if token.dep_ == "pobj":
            entity = get_blank(token, "pobj")
        if token.dep_ == "nsubj":
            entity = get_blank(token, "nsubj")
        if token.dep_ == "attr":
            entity = get_blank(token, "attr")
        if token.pos_ == "VERB":
            if token.text == "die":
                property = "place of death"
            if token.text == "born":
                property = "place of birth"
            else:
                if token.text.endswith('ed'):
                    property = token.lemma_
                else:
                    property = token.text
                if property == "locate":
                    property = "location"
        if property == "":
            property = "educated at"

    return property, entity, "Where"


def get_keywords_how(parse):
    type = "How"
    entity = ""
    property = ""
    if (parse[1].dep_ == "advmod" or parse[1].dep_ == "acomp") and parse[1].text != "many":
        if parse[1].text == "big" or parse[1].text == "wide" or parse[1].text == "large":
            property = "diameter"
        elif parse[1].text == "heavy":
            property = "mass"
        elif parse[1].text == "hot" or parse[1].text == "warm" or parse[1].text == "cold":
            property = "temperature"
        elif parse[1].text == "old" or parse[1].text == "young":
            property = "inception"
        elif parse[1].text == "far" or parse[1].text == "close":
            property = "distance"
        elif parse[1].text == "dense":
            property = "density"
        elif parse[1].text == "fast" or parse[1].text == "slow":
            property = "speed"
        elif parse[1].text == "tall":
            property = "tall"

        for token in parse:
            if token.dep_ == "nsubj" and token.lemma_ != "-PRON-":
                entity = get_blank(token, "nsubj")

    if parse[1].text == "many":
        type = "How many"

        for token in parse:
            if token.dep_ == "pobj" and token.lemma_ != "-PRON-":
                if property == "":
                    property = get_blank(token, "pobj")
                else:
                    entity = get_blank(token, "pobj")
            if token.dep_ == "dobj" and token.lemma_ != "-PRON-":
                if property == "":
                    property = get_blank(token, "dobj")
                else:
                    entity = get_blank(token, "dpobj")
            if token.dep_ == "nsubj" and token.lemma_ != "-PRON-":
                if property == "":
                    property = get_blank(token, "nsubj")
                else:
                    entity = get_blank(token, "nsubj")

    if parse[1].text == "much":
        for token in parse:
            if token.dep_ == "pobj" and token.lemma_ != "-PRON-" and token.lemma_ != "much":
                if entity == "":
                    entity = get_blank(token, "pobj")
                else:
                    property = get_blank(token, "pobj")
            if token.dep_ == "dobj" and token.lemma_ != "-PRON-" and token.lemma_ != "much":
                if entity == "":
                    entity = get_blank(token, "dobj")
                else:
                    property = get_blank(token, "dpobj")
            if token.dep_ == "nsubj" and token.lemma_ != "-PRON-" and token.lemma_ != "much":
                if entity == "":
                    entity = get_blank(token, "nsubj")
                else:
                    property = get_blank(token, "nsubj")
            if token.dep_ == "ROOT" and token.lemma_ != "-PRON-" and token.lemma_ != "much":
                property = token.lemma_
        if property == "weigh":
            property = "mass"

    if entity == "" or property == "":
        for token in parse:
            if token.dep_ == "pobj" and token.lemma_ != "-PRON-" and token.lemma_ != "much":
                if property == "":
                    property = get_blank(token, "pobj")
                else:
                    entity = get_blank(token, "pobj")
            if token.dep_ == "dobj" and token.lemma_ != "-PRON-" and token.lemma_ != "much":
                if property == "":
                    property = get_blank(token, "dobj")
                else:
                    entity = get_blank(token, "dpobj")
            if token.dep_ == "nsubj" and token.lemma_ != "-PRON-" and token.lemma_ != "much":
                if property == "":
                    property = get_blank(token, "nsubj")
                else:
                    entity = get_blank(token, "nsubj")
            if token.dep_ == "ROOT" and token.lemma_ != "-PRON-" and token.lemma_ != "much":
                entity = token.lemma_

    if property == "people":
        property = "attendance"

    return property, entity, type


# finds the keywords for 3 different kinds of sentences
def get_keywords(line):
    nlp = spacy.load('en_core_web_sm')
    parse = nlp(line.strip())
    type = parse[0].text

    for token in parse:
         print("\t".join((token.text, token.lemma_, token.pos_, token.dep_, token.head.lemma_)))

    if type == "Who":
        return get_keywords_who(parse)
    if type == "How":
        return get_keywords_how(parse)
    if type == "What":
        if parse[1].text == "does":
            return get_keywords_what_does(parse)
        return get_keywords_what(parse)
    if type == "Where":
        return get_keywords_where(parse)
    if type == "When":
        return get_keywords_when(parse)
    if type == "Which":
        return get_keywords_which(parse)
    return get_keywords_what(parse)


def generate_query(prop, entity, type):
    # If first_word is of type "who".
    if (type == "Who"):
        query = '''SELECT ?answerLabel WHERE {
            wd:''' + entity + ' wdt:' + prop + ''' ?answer.  
            ?answer wdt:P31 wd:Q5.
            SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }'''
    # If type is regex1 (Who/What (is/was/were) (Albert Einstein/The Beatles)?)
    elif type == "How many":
        query = '''SELECT (COUNT(?co) as ?answer) WHERE {
        wd:''' + entity + ' wdt:' + prop + ''' ?co .
        SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .
        }}'''
    # If type is regex1 (Who/What (is/was/were) (Albert Einstein/The Beatles)?)
    elif type == "regex1":
        query = '''SELECT ?itemLabel WHERE {
            wd:''' + entity + ''' schema:description ?itemLabel.
            FILTER(LANG(?itemLabel) = "en")
            }'''
    elif type == "regex2":
        query = '''SELECT ?Alt WHERE {
            SERVICE wikibase:label {
                bd:serviceParam wikibase:language "en" .
                wd:'''+entity+''' skos:altLabel ?Alt .
                }
            }'''
    else:
        query = '''SELECT ?answerLabel WHERE {
            wd:''' + entity + ' wdt:' + prop + ''' ?answer.  
            SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }'''

    return query


# generates a query and executes it, returns false if it didn't print an answer and true if it did.
def execute_query(prop, entity, type):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    }
    url = 'https://query.wikidata.org/sparql'
    query = generate_query(prop, entity, type)
    data = requests.get(url, headers=headers, params={'query': query, 'format': 'json'}).json()

    if not data['results']['bindings']:
        return 0
    print(query)
    for item in data['results']['bindings']:
        for var in item:
            print(item[var]['value'])
    return 1


# functions that returns 10 questions I know my program can answer
def my_questions():
    return ("What are symptoms of COVID-19?",
            "What was the disability of Stephen Hawking?",
            "What was the goal of the Apollo space program?",
            "What is the birth date of John Lennon?",
            "Who influenced Nicolas Tesla",
            "Who designed Fortran?",
            "Who discovered penicillin?",
            "Who invented the microscope?",
            "Who invented the stethoscope?",
            "When was pluto discovered?",
            "When was gold discovered?",
            "When was the chip invented?")


# This function gets an array of possible IDs and tries to get answers with them.
# It will keep trying new IDs until it gets an answer or until there are no more possible IDs.
def line_handler(line):
    prop, entity, type = get_keywords(line)
    print(prop, entity, type)

    propIDs = 0
    entityIDs = 0
    if prop != "":
        propIDs = get_id(prop, True)
    if entity != "":
        entityIDs = get_id(entity, False)

    answer = 0
    if propIDs != 0 and entityIDs != 0:
        for entityID in entityIDs:
            for propID in propIDs:
                answer = execute_query(propID['id'], entityID['id'], type)
                if type == "How many" and answer == 0:
                    answer = execute_query(propID['id'], entityID['id'], "How many1")
                if answer == 1:
                    return
    if answer == 0:
        #bij sommige vragen moesten de woorden die als entity werden aangeschreven, property's worden en ook andersom. Om een goed antwoord te krijgen
        if prop != "":
            propIDs = get_id(entity, True)
        if entity != "":
            entityIDs = get_id(prop, False)
        if propIDs != 0 and entityIDs != 0:
            for entityID in entityIDs:
                for propID in propIDs:
                    answer = execute_query(propID['id'], entityID['id'], type)
                    if answer == 1:
                        return

    if answer == 0:
        prop, entity, type = check_regex_sentences(line)
        if prop != "":
            propIDs = get_id(prop, True)
        if entity != "":
            entityIDs = get_id(entity, False)
        if propIDs == 0 or entityIDs == 0:
            return

        for entityID in entityIDs:
            answer += execute_query(None, entityID['id'], type)
            if answer >= 1:
                return

    if answer == 0:
        print("No answer could be found")


def main():
    #questions = my_questions()
    #for line in questions:
    #    print(line)

    #for line in fileinput.input():
    #    if line == "stop\n":
    #        break
    #    line_handler(line)

    with open("all_questions.txt") as fl:
        file_contents = [x.rstrip() for x in fl]

    for line in file_contents:
        print(line)
        line_handler(line)
        print()


if __name__ == "__main__":
    main()
