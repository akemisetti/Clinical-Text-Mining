__author__ = 'Jason'
import csv,sys,re,json,yaml
from stanfordcorenlp import StanfordCoreNLP

################
# Obtain synonym from wordnet. docs: http://www.nltk.org/howto/wordnet.html
from nltk.corpus import wordnet as wn
S = wn.synset
L = wn.lemma


print(sys.argv)
if len(sys.argv) < 5:
    print("Usage: [input_file.csv] [output_file] [wordset_file] [stanfordNlp3.7_path]")
    exit(1)
input_file = sys.argv[1]
output_file = sys.argv[2]
wordset_file = sys.argv[3]
stanfordNlpPath = sys.argv[4]
nlp = StanfordCoreNLP(stanfordNlpPath)

def lemma(text):
    global nlp
    props={'annotators': 'lemma','pipelineLanguage':'en','outputFormat':'json'}
    r_dict = nlp.annotate(text, properties=props)
    r_dict = yaml.safe_load(r_dict)
    lemma = []
    for s in r_dict['sentences']:
        for token in s['tokens']:
            lemma.append(token['lemma'])
    return lemma

def get_synonyms(term,pos='asn'):
    synonym = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        #print(ss.name(), ss.lemma_names())
        #synonym.add(ss.name().lower())
        for lemma in ss.lemma_names():
            synonym.add(lemma.lower())
    # for s in synonym:
    #     print(s)
    return synonym
def get_antonyms(term,pos='asn'):
    retSet = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        for lemma in ss.lemmas():
            for anto in lemma.antonyms():
                retSet.add(anto.name().lower())
    return retSet
def get_hyperyms(term,pos='asn'):
    retSet = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        for hyper in ss.hypernyms() + ss.instance_hypernyms():
            for lemma in hyper.lemma_names():
                retSet.add(lemma.lower())
    return retSet
def get_hyponyms(term,pos='asn'):
    retSet = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        for rel in ss.hyponyms() + ss.instance_hyponyms():
            for lemma in rel.lemma_names():
                retSet.add(lemma.lower())
    return retSet
def get_holonyms(term,pos='asn'):
    retSet = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        for rel in ss.part_holonyms() + ss.member_holonyms() + ss.substance_holonyms():
            for lemma in rel.lemma_names():
                retSet.add(lemma.lower())
    return retSet
def get_meronyms(term,pos='asn'):
    retSet = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        for rel in ss.part_meronyms() + ss.member_meronyms() + ss.substance_meronyms():
            for lemma in rel.lemma_names():
                retSet.add(lemma.lower())
    return retSet
def get_siblings(term,pos='asn'):
    retSet = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        for hyper in ss.hypernyms():
            for hypo in hyper.hyponyms():
                for lemma in hypo.lemma_names():
                    retSet.add(lemma.lower())
    return retSet
def get_derivationally_related_forms(term,pos='asn'):
    retSet = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        for lemma in ss.lemmas():
            for rel in lemma.derivationally_related_forms():
                retSet.add(rel.name().lower())
    return retSet
def get_pertainyms(term,pos='asn'):
    retSet = set()
    for ss in wn.synsets(term.strip(),pos=pos):
        for lemma in ss.lemmas():
            for rel in lemma.pertainyms():
                retSet.add(rel.name().lower())
    return retSet

# all the words involved
word_set = set()

## matches:
# 1. (.*) all string within parenthesis; "\N" is the null value for mysql. # FIXME test only by now
rSpecial4name = re.compile(r"\s\(.*\)")
rSpecial4umls = re.compile(r"\(.*\)|[^a-zA-Z0-9-_ ]|- |- |\b-\b")
with open(input_file, 'rb') as csvfile:
    with open(output_file, 'w+') as of:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        writer = csv.writer(of,delimiter='\t',quotechar='"',lineterminator="\n")
        writer.writerow(['word','word_norm','umls_syn','wn_syn','wn_ant','wn_hyper','wn_hypo','wn_holo','wn_mero','wn_sibling','derivation','pertain'])
        for row in reader:
            if len(row) < 1: continue
            word = row[0]
            print("\n### word: %s" % word)
            word_norm = rSpecial4name.sub('',word).strip().replace(' ','_')
            isValidTerm = False  # whether this is term is found in wordnet or umls
            # word_set.add(word_norm)
            cui = '' if len(row) < 2 else  row[1].strip()
            if len(cui) > 0: isValidTerm = True
            synUmls = [] if len(row) < 3 else  row[2].split(r'|')
            synUmlsSet = set()
            for s in synUmls:
                s2 = '_'.join(lemma(rSpecial4umls.sub('',s.replace(r'\N','')).lower().strip())) # \N is null in mysql
                if len(s2) == 0: continue
                synUmlsSet.add(s2)
            print synUmlsSet
            synWnSet = get_synonyms(word_norm)
            word_set |= synWnSet
            if len(synWnSet) > 0: isValidTerm = True
            print(synWnSet)
            antonyms = get_antonyms(word_norm)
            word_set |= antonyms
            print antonyms
            hypernym = get_hyperyms(word_norm)
            word_set |= hypernym
            print(hypernym)
            hyponym = get_hyponyms(word_norm)
            word_set |=hyponym
            print(hyponym)
            holonym = get_holonyms(word_norm)
            word_set |= holonym
            print(holonym)
            meronym = get_meronyms(word_norm)
            word_set |= meronym
            print(meronym)
            siblings = get_siblings(word_norm)
            word_set |= siblings
            print(siblings)
            derivation = get_derivationally_related_forms(word_norm)
            word_set |= derivation
            print(derivation)
            pertain = get_pertainyms(word_norm)
            word_set |= pertain
            print(pertain)
            if isValidTerm:  word_set.add(word_norm)

            sep = ','
            writer.writerow([word,word_norm,sep.join(synUmlsSet),sep.join(synWnSet),sep.join(antonyms),sep.join(hypernym),\
                             sep.join(hyponym),sep.join(holonym),sep.join(meronym),sep.join(siblings),sep.join(derivation),sep.join(pertain)])

        with open(wordset_file, 'w+') as wf:
            for w in word_set:
                wf.write("%s\n" % w)



