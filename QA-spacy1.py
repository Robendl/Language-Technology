#!/usr/bin/env python3

import requests
import fileinput
import spacy


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
        return json['search']


# returns the type of part of the sentence that is required
def get_blank(subtree, type):
    part = []
    comp = True
    for d in subtree:
        if d.dep_ == type or (d.dep_ == "compound" and comp):
            if d.dep_ == type:
                comp = False
            part.append(d.lemma_)
    return " ".join(part)

# finds the keywords for 3 different kinds of sentences
def get_keywords(line):
    nlp = spacy.load('en_core_web_sm')
    first_word = True
    parse = nlp(line.strip())
    nsubj = ""
    pobj = ""
    dobj = ""
    root = ""
    for token in parse:
        if(first_word):
            type = token
        if token.dep_ == "nsubj":
            nsubj = get_blank(token.subtree, "nsubj")
        if token.dep_ == "pobj":
            pobj = get_blank(token.subtree, "pobj")
        if token.dep_ == "dobj":
            dobj = get_blank(token.subtree, "dobj")
        if token.dep_ == "ROOT":
            root = token.lemma_
        first_word = False

    if dobj:
        pobj = dobj
    if parse[0].dep_ == "attr":
        return nsubj, pobj, type

    if parse[0].dep_ == "nsubj":
        return root, pobj, type

    if parse[0].dep_ == "advmod":
        return root, nsubj, type

    return nsubj, pobj, type

def generate_query(prop, entity, type):
    #If first_word is of type "who".
    if(type.text == "Who"):
        query = '''SELECT ?answerLabel WHERE {
            wd:''' + entity + ' wdt:' + prop + ''' ?answer.  
            ?answer wdt:P31 wd:Q5.
            SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }'''
    #Hier moeten de andere queries komen.    
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
    propIDs = get_id(prop, True)
    entityIDs = get_id(entity, False)
    if propIDs == 0 or entityIDs == 0:
        return

    answer = 0
    for entityID in entityIDs:
        for propID in propIDs:
            answer += execute_query(propID['id'], entityID['id'], type)

    if answer == 0:
        print("No answer could be found")


def main():
    questions = my_questions()
    for line in questions:
        print(line)

    for line in fileinput.input():
        line_handler(line)


if __name__ == "__main__":
    main()
