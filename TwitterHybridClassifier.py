# -*- coding: utf-8 -*-

#########################################################################
############## Semeval - Sentiment Analysis in Twitter  #################
#########################################################################

####
#### Authors: Pedro Paulo Balage Filho e Lucas Avanço
#### Version: 2.0
#### Date: 26/03/14
####

# Python 3 compatibility
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement
from __future__ import unicode_literals

# Import the libraries created for this task
from RulesClassifier import RulesClassifier
from LexiconClassifier import LexiconClassifier
from EmotionClassifier import EmotionClassifier
from MachineLearningClassifier import MachineLearningClassifier
from PreProcess import pre_process

# Import other libraries used
import pickle
import codecs
import os
import sys

#### Provides a hybrid Sentiment Analysis classifier.
#### This classifier was designed for Semeval 2014 Task 9 - Sentiment Analysis in Twitter
#### Information about Semeval format can be found at:
####    http://alt.qcri.org/semeval2014/task9/
####
#### The trainset must be in SemevalTwitter format. See SemevalTwitter.py for information.
class TwitterHybridClassifier(object):

    def __init__(self, tweets=[]):
        # initialize internal variables
        self.rules_classifier = RulesClassifier()
        self.lexicon_classifier = LexiconClassifier()
        self.emotion_classifier = EmotionClassifier()
        self.ml_classifier = None

        # if the ML model has been generated, load the model from model.pkl
        if sys.version_info >= (3,0):
            if os.path.exists('model_python3.pkl'):
                print ('Reading the model from model_python3.pkl')
                self.ml_classifier = pickle.load(open('model_python3.pkl','rb'))
        else:
            if os.path.exists('model_python2.pkl'):
                print ('Reading the model from model_python2.pkl')
                self.ml_classifier = pickle.load(open('model_python2.pkl','rb'))

        if self.ml_classifier == None:
            # Preprocess the data and train a new model
            print ('Preprocessing the training data')
            tweet_messages = [tweet_message for tweet_message,label in tweets]
            tweet_labels = [label for tweet_message,label in tweets]

            # preprocess all the tweet_messages (Tokenization, POS and normalization)
            tweet_tokens = pre_process(tweet_messages)

            # compile a trainset with tweet_tokens and labels (positive,
            # negative or neutral)

            trainset = [(tweet_tokens[i],tweet_labels[i]) for i in range(len(tweets))]

            # initialize the classifier and train it
            classifier = MachineLearningClassifier(trainset)

            # dump the model into de pickle
            python_version = sys.version_info[0]
            model_name = 'model_python' + str(python_version) + '.pkl'
            print ('Saving the trained model at ' + model_name)
            pickle.dump(classifier, open(model_name, 'wb'))
            self.ml_classifier = classifier

    # Apply the classifier over a tweet message in String format
    def classify(self,tweet_text):

        # 0. Pre-process the tweets (tokenization, tagger, normalizations)
        tweet_tokens_list = []

        print ('Preprocessing the string')
        # pre-process the tweets
        tweet_tokens_list = pre_process([tweet_text])

        predictions = []
        rbpreds = []
        lbpreds = []
        mlpreds = []
        total_tweets = len(tweet_tokens_list)

        # iterate over the tweet_tokens
        for index, tweet_tokens in enumerate(tweet_tokens_list):

            # 1. Rule-based classifier. Look for emoticons basically
            positive_score,negative_score = self.rules_classifier.classify(tweet_tokens)

            #1. Apply the rules, If any found, classify the tweet here. If none found, continue for the lexicon classifier.
            if positive_score >= 1 and negative_score == 0:
                sentiment = ('positive','RB')
                predictions.append(sentiment)
                rbpreds.append(sentiment)
                continue
            elif positive_score == 0 and negative_score <= -1:
                sentiment = ('negative','RB')
                predictions.append(sentiment)
                rbpreds.append(sentiment)
                continue

            # 2. Lexicon-based classifier
            positive_score, negative_score = self.lexicon_classifier.classify(tweet_tokens)
            lexicon_score = positive_score + negative_score

            # 2. Apply lexicon classifier,
            # If in the threshold classify the tweet here. If not, continue for the ML classifier
            if positive_score >= 1 and negative_score == 0:
                sentiment = ('positive','LB')
                predictions.append(sentiment)
                lbpreds.append(sentiment)
                continue
            elif negative_score <= -2:
                sentiment = ('negative','LB')
                predictions.append(sentiment)
                lbpreds.append(sentiment)
                continue

            # 3. Machine learning based classifier - used the Train+Dev set sto define the best features to classify new instances
            result = self.ml_classifier.classify(tweet_tokens)
            positive_conf = result['positive']
            negative_conf = result['negative']
            neutral_conf = result['neutral']

            if negative_conf >= -0.4:
                sentiment = ('negative','ML')
            elif positive_conf > neutral_conf:
                sentiment = ('positive','ML')
            else:
                sentiment = ('neutral','ML')

            predictions.append(sentiment)
            mlpreds.append(sentiment)

        return predictions

    # Apply the classifier in batch over a list of tweet messages in String format
    def classify_batch(self,tweet_texts):

        # 0. Pre-process the teets (tokenization, tagger, normalizations)
        tweet_tokens_list = []

        if len(tweet_texts) == 0:
            return tweet_tokens_list

        print ('Preprocessing the test data')
        # pre-process the tweets
        tweet_tokens_list = pre_process(tweet_texts)

        predictions = []
        rbpreds = [] #not needed
        lbpreds = [] #not needed
        mlpreds = [] #not needed
        emopreds = []
        total_tweets = len(tweet_tokens_list)

        # iterate over the tweet_tokens
        for index, tweet_tokens in enumerate(tweet_tokens_list):

            print('Testing for tweet n. {}/{}'.format(index+1,total_tweets))

            # 1. Rule-based classifier. Look for emoticons basically
            positive_score,negative_score = self.rules_classifier.classify(tweet_tokens)

            #1. Apply the rules, If any found, classify the tweet here. If none found, continue for the lexicon classifier.
            if positive_score >= 1 and negative_score == 0:
                sentiment = ('positive','RB')
                predictions.append(sentiment)
                rbpreds.append(sentiment)#not needed
                continue
            elif positive_score == 0 and negative_score <= -1:
                sentiment = ('negative','RB')
                predictions.append(sentiment)
                rbpreds.append(sentiment)#not needed
                continue

            # 2. Lexicon-based classifier w/ emotions
            positive_score, negative_score = self.lexicon_classifier.classify(tweet_tokens)
            lexicon_score = positive_score + negative_score
            #added new emotion scores here
            anger_score, anticipation_score, disgust_score, fear_score, joy_score, sadness_score, surprise_score, trust_score = self.emotion_classifier.classify(tweet_tokens)


            # 2. Apply lexicon classifier,
            # If in the threshold classify the tweet here. If not, continue for the ML classifier
            if positive_score >= 1 and negative_score == 0: # original: >= 1, == 0
                sentiment = ('positive','LB')
                predictions.append(sentiment)
                lbpreds.append(sentiment)#not needed
                continue
            elif negative_score <= -2:
                sentiment = ('negative','LB')
                predictions.append(sentiment)
                lbpreds.append(sentiment)#not needed
                continue

            emotionDict = {'anger': anger_score, 'anticipation': anticipation_score, 'disgust': disgust_score,'fear': fear_score, 'joy': joy_score, 'sadness': sadness_score, 'surprise': surprise_score, 'trust': trust_score}
            emotion = max(emotionDict, key=emotionDict.get)
            emopreds.append(emotion)

            # 3. Machine learning based classifier - used the Train+Dev set sto define the best features to classify new instances
            result = self.ml_classifier.classify(tweet_tokens)
            positive_conf = result['positive']
            negative_conf = result['negative']
            neutral_conf = result['neutral']

            if negative_conf >= -0.4:
                sentiment = ('negative','ML')
            elif positive_conf > neutral_conf:
                sentiment = ('positive','ML')
            else:
                sentiment = ('neutral','ML')

            predictions.append(sentiment)
            mlpreds.append(sentiment)#not needed

        return predictions

    # Output Individual scores for each method
    def output_individual_scores(self,tweets):

        tweet_texts = [tweet_message for tweet_message,label in tweets]
        tweet_labels = [label for tweet_message,label in tweets]

        # write the log
        fp = codecs.open('individual_scores.tab','w',encoding='utf8')
        line = 'pos_score_rule\tneg_score_rule\tpos_score_lex\tneg_score_lex\tpos_conf\tneg_conf\tneutral_conf\tclass\tmessage\n'
        fp.write(line)

        # 0. Pre-process the text (emoticons, misspellings, tagger)
        tweet_tokens_list = None
        tweet_tokens_list = pre_process(tweet_texts)

        predictions = []
        for index,tweet_tokens in enumerate(tweet_tokens_list):
            line = ''

            # 1. Rule-based classifier. Look for emoticons basically
            positive_score,negative_score = self.rules_classifier.classify(tweet_tokens)
            line += str(positive_score) + '\t' + str(negative_score) + '\t'

            # 2. Lexicon-based classifier (using url_score obtained from RulesClassifier)
            positive_score, negative_score = self.lexicon_classifier.classify(tweet_tokens)
            lexicon_score = positive_score + negative_score
            line += str(positive_score) + '\t' + str(negative_score) + '\t'

            # 3. Machine learning based classifier - used the training set to define the best features to classify new instances
            result = self.ml_classifier.decision_function(tweet_tokens)
            line += str(result['positive']) + '\t' + str(result['negative']) + '\t' + str(result['neutral']) + '\t'

            line += tweet_labels[index] + '\t"' + tweet_texts[index].replace('"','') + '"\n'

            fp.write(line)
        print('Individual score saved in the file: individual_scores.tab')
