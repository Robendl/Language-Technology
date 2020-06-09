#!/usr/bin/env python3
# Made by Roben de Lange (s3799174), Julian Zwijghuizen (s3799492), Thomas Veldboer (s3686450), Thomas Tan (s3235289)

import requests
import sys
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
        return 0
    else:
        return json['search']


# returns the type of part of the sentence that is required
def get_blank(token, type):
    part = []
    comp = True
    for d in token.subtree:
        # Nummod zodat hij Apollo 11 bijvoorbeeld goed scant. Amod is zodat hij wel bijvoeglijke naamwoorden meenement zoals atomic number.
        if d.dep_ == type or (d.dep_ == "compound" and comp) or (
                d.dep_ == "nummod" and d.head.lemma_ == token.lemma_) or (
                d.dep_ == "amod" and d.head.lemma_ == token.lemma_ and d.text != "many"):
            if d.dep_ == type:
                comp = False
                part.append(d.lemma_)
            # gedaan zodat hij bijvoorbeeld highest point niet high point van maakt maar gewoon highest point.
            else:
                part.append(d.text)
    return " ".join(part)


# Checks if we can find keywords using regex for certain specific sentences.
def check_regex_sentences(line):
    property = ""
    entity = ""
    type = ""
    # What does DNA stand for? / What does REM sleep stand for? These questions need to be fully written out.
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


def get_keywords_at_what(parse):
    entity = ""
    property = ""
    found_entity = False

    for token in parse:
        if (token.dep_ == "dobj" or token.pos_ == "VERB") and found_entity:
            property = token.lemma_

        if (token.dep_ == "nsubj" or token.dep_ == "compound" or token.pos_ == "VERB") and found_entity == False:
            entity = get_blank(token, token.dep_)
            found_entity = True

    return property, entity, "At what"


def get_keywords_in_what(parse):
    entity = ""
    property = ""
    found_place = False

    for token in parse:
        if token.text == "city" or token.text == "country" or token.text == "place":
            property = token.text
            found_place = True

        if token.dep_ == "nsubj" or token.dep_ == "compound":
            entity = get_blank(token, token.dep_)

        if token.pos_ == "VERB" or (token.pos_ == "NOUN" and token.dep_ == "ROOT"):
            if token.lemma_ != "hold":
                property = token.lemma_
            if token.text == "born":
                property = "date of birth"
            if token.text == "die":
                property = "date of death"
            if token.text == "born" and found_place:
                property = "place of birth"
            if token.text == "die" and found_place:
                property = "place of death"

    return property, entity, "In what"


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
        if property == "" or property == "study":
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


def get_keywords_name(parse):
    entity = ""
    property = ""
    for token in parse:
        # Als de zin begint met Name
        if token.dep_ == "pobj":
            entity = get_blank(token, "pobj")
        if token.dep_ == "dobj":
            property = get_blank(token, "dobj")

    return property, entity, "Name"


def get_keywords_is(parse):
    type = "Is"
    entity = ""
    property = ""

    for token in parse:
        if token.dep_ == "nsubj":
            entity = get_blank(token, "nsubj")
        if token.dep_ == "attr":
            property = get_blank(token, "attr")

    if entity == "" or property == "":
        for token in parse:
            if token.dep_ == "compound":
                entity = token.lemma_
            if token.dep_ == "attr":
                property = token.lemma_

    return property, entity, type


# Calls functions that are made for sentences that start with certain words.
def get_keywords(line):
    nlp = spacy.load('en_core_web_sm')
    parse = nlp(line.strip())
    type = parse[0].text

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
    if type == "Is" or type == "Are" or type == "Were" or type == "Was":
        return get_keywords_is(parse)
    if type == "Did" or type == "Have":
        return 0, 0, "yes"
    if type == "At":
        return get_keywords_at_what(parse)
    if type == "In":
        return get_keywords_in_what(parse)
    if type == "Name":
        return get_keywords_name(parse)

    return get_keywords_what(parse)


# Generates queries for certain types
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
                wd:''' + entity + ''' skos:altLabel ?Alt .
                }
            }'''
    elif type == "Is":
        query = '''SELECT ?answerLabel WHERE {
            wd:''' + entity + ' ?answer wd:' + prop + '''.
            SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
            }'''
    else:
        query = '''SELECT ?answerLabel WHERE {
            wd:''' + entity + ' wdt:' + prop + ''' ?answer.  
            SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }'''

    return query


# generates a query and executes it, returns 0 if it didn't find an answer.
def execute_query(prop, entity, type):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    }
    url = 'https://query.wikidata.org/sparql'
    query = generate_query(prop, entity, type)
    data = requests.get(url, headers=headers, params={'query': query, 'format': 'json'}).json()

    if not data['results']['bindings']:
        return 0

    file = open("answers.txt", "a", encoding="utf-8")

    for item in data['results']['bindings']:
        for var in item:
            value = item[var]['value']

            file.write("    " + value)
    file.close()
    return 1


# Returns False if there is no answer, True if there is.
def execute_yes_no_query(prop, entity):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    }
    url = 'https://query.wikidata.org/sparql'
    query = generate_query(prop, entity, "Is")
    data = requests.get(url, headers=headers, params={'query': query, 'format': 'json'}).json()

    if not data['results']['bindings']:
        return False
    return True


# Writes 'yes' if an answer is found, 'no' if not.
def yes_no_query_handler(prop, entity):
    propIDs = 0
    entityIDs = 0
    if prop != "":
        propIDs = get_id(prop, False)
    if entity != "":
        entityIDs = get_id(entity, False)

    answer = False
    file = open("answers.txt", "a", encoding="utf-8")

    if propIDs != 0 and entityIDs != 0:
        for entityID in entityIDs:
            for propID in propIDs:
                answer = execute_yes_no_query(propID['id'], entityID['id'], )
                if answer:
                    file.write("    yes")
                    file.close()
                    return
    file.write("    no")
    file.close()


# Counts number of answers, if the count is 1 it checks if the value is a number, if it is it returns the number.
# Otherwise it returns the count.
def execute_how_many_query(prop, entity, type):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    }
    url = 'https://query.wikidata.org/sparql'
    query = generate_query(prop, entity, type)
    data = requests.get(url, headers=headers, params={'query': query, 'format': 'json'}).json()

    if not data['results']['bindings']:
        return "0"

    answers = []
    for item in data['results']['bindings']:
        for var in item:
            answers.append(item[var]['value'])

    if len(answers) == 1:
        answer = answers[0]
        if answer.isnumeric():
            return answer
        return "1"

    return str(len(answers))


# Creates queries and handles answer for 'how many' questions, keeps going until it finds an answer that's not 0 or
# when there is nothing left to try.
def how_many_query_handler(prop, entity):
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
                answer = execute_how_many_query(propID['id'], entityID['id'], "rest")
                if answer != "0":
                    break
            if answer != "0":
                break
    else:
        answer = "0"

    file = open("answers.txt", "a", encoding="utf-8")
    file.write("    " + answer)
    file.close()


# If nothing works and we don't have an answer we try every combination of tokens with certain pos_ values.
def try_everything(line):
    nlp = spacy.load('en_core_web_sm')
    parse = nlp(line.strip())

    for token1 in parse:
        for token2 in parse:
            if ((token1.pos_ == "ADJ" or token1.pos_ == "NOUN" or token1.pos_ == "PROPN" or token1.pos_ == "VERB") and
                    (token2.pos_ == "ADJ" or token2.pos_ == "NOUN" or token2.pos_ == "PROPN" or token2.pos_ == "VERB")
                    and token1 != token2):
                propIDs = get_id(get_blank(token1, token1.dep_), True)
                entityIDs = get_id(get_blank(token2, token2.dep_), False)
                if propIDs != 0 and entityIDs != 0:
                    for entityID in entityIDs:
                        for propID in propIDs:
                            answer = execute_query(propID['id'], entityID['id'], "What")
                            if answer == 1:
                                return


# Gets keywords from the line and tries to every combination of IDs. There are some exceptions
def line_handler(line):
    prop, entity, type = get_keywords(line)

    if type == "yes":   # just writes 'yes' for some yes/no questions
        file = open("answers.txt", "a", encoding="utf-8")
        file.write("    yes")
        file.close()
        return

    if type == "Is":    # yes/no with is need different query handlers
        yes_no_query_handler(prop, entity)
        return

    if type == "How many":  # How many questions need different query handlers
        how_many_query_handler(prop, entity)
        return

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
        if entity != "":
            propIDs = get_id(entity, True)
        if prop != "":
            entityIDs = get_id(prop, False)
        if propIDs != 0 and entityIDs != 0:
            for entityID in entityIDs:
                for propID in propIDs:
                    answer = execute_query(propID['id'], entityID['id'], type)
                    if answer >= 1:
                        return

    if answer == 0:
        prop, entity, type = check_regex_sentences(line)
        if prop != "":
            propIDs = get_id(prop, True)
        if entity != "":
            entityIDs = get_id(entity, False)

        if propIDs != 0 and entityIDs != 0:
            for entityID in entityIDs:
                answer += execute_query(None, entityID['id'], type)
                if answer >= 1:
                    return

    try_everything(line)


def main():
    for line in sys.stdin:
        if line != "\n":
            number = line.split()[0]
            new_line = re.sub(r'\d+ +', '', line)
            file = open("answers.txt", "a", encoding="utf-8")
            file.write(number)
            file.close()
            line_handler(new_line)
            file = open("answers.txt", "a", encoding="utf-8")
            file.write("\n")
            file.close()


if __name__ == "__main__":
    main()
