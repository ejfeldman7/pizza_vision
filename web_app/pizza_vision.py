# -*- coding: utf-8 -*-
"""pizza_vision.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UEXIk-rxGhtC3Mbx9-y1PzbMiEnBf0PJ
"""

# Commented out IPython magic to ensure Python compatibility.
import streamlit as st
import pandas as pd
import numpy as np
from numpy.linalg import norm
import time
import random
from datetime import datetime
import re
import os
import urllib, io
from io import StringIO 
import string

import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

#nltk.download()
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

from nltk.corpus import stopwords
from nltk.corpus import wordnet
# from nltk import sent_tokenize, word_tokenize
# from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
import string
from nltk.tokenize import word_tokenize
# from nltk.corpus import stopwords, wordnet
import pickle
# from tqdm import tqdm, tqdm_notebook
import sklearn
# from sklearn.manifold import TSNE
# from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances

import PIL
from PIL import Image
from sklearn.neighbors import NearestNeighbors
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image as image_process

import glob
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
# %matplotlib inline

# Set stop words for cleaning input text
stops = stopwords.words("english")
sw = stops + ['pizza','pizzas','\xa0we','come', 'food', 'one', 'give', 'ask', 'back', 'great', 'take', 'wait','bar','pasta','time','place','go','would','say','call','make','minute','like','miss','pita','rib','salad','gyro','tzatziki','wing','burger','chicken','sandwich','dog','steak','hotdog']

# Pizza info
big_pizza_details = pickle.load(open('/app/pizza_vision/web_app/big_pizza_details.pickle', 'rb'))
url_df = pickle.load(open('/app/pizza_vision/web_app/big_pizza_urls.pickle', 'rb'))
chicagoland = pickle.load(open('/app/pizza_vision/web_app/chicagoland.pickle', 'rb'))

# Computer Vision
filenames = pickle.load(open('/app/pizza_vision/web_app/OGfilenames_images.pickle', 'rb'))
feature_list = pickle.load(open('/app/pizza_vision/web_app/OGfeatures-resnet.pickle','rb'))
class_ids = pickle.load(open('/app/pizza_vision/web_app/OGresnet_classids.pickle', 'rb'))
# apart_features = pickle.load(open('/content/drive/My Drive/ds/pizza_images/autoencoder/features-resnet-apart.pickle', 'rb'))

# NLP info
nmf_df = pickle.load(open('/app/pizza_vision/web_app/colab_nmf_df.pickle', 'rb'))
nmf = pickle.load(open('/app/pizza_vision/web_app/colab_nmf.pickle', 'rb'))
doc_topic = pickle.load(open('/app/pizza_vision/web_app/colab_doc_topic.pickle', 'rb'))
topic_word = pickle.load(open('/app/pizza_vision/web_app/colab_topic_word.pickle', 'rb'))
tfidf = pickle.load(open('/app/pizza_vision/web_app/colab_tfidf.pickle', 'rb'))
tfidf__mat = pickle.load(open('/app/pizza_vision/web_app/colab_tfidf_mat.pickle', 'rb'))

@st.cache
def load_resnet():
    return ResNet50(weights='imagenet',include_top=False, input_shape=(224, 224, 3),pooling='max')
    
resnet_model = load_resnet()

# Helper function to get the classname
def classname(str):
    return str.split('/')[-2]


# Helper function to get the classname and filename
def classname_filename(str):
    return str.split('/')[-2] + '/' + str.split('/')[-1]

# Helper functions to plot the nearest images given a query image
def plot_images(filenames, distances):
    
    rec_ids = []
    github_files = []
    input_file = filenames.pop(0)
    for filename in filenames:
        github = '/app/pizza_vision/web_app/yelp_only/' + classname_filename(filename)
        github_files.append(github)
    github_files = [input_file]+github_files
    
    images = []
    for filename in github_files:
        images.append(mpimg.imread(filename))
    
    captions_on_page = ['Your Input Image']
    for indx in range(1,len(github_files)):
      captions_on_page.append(github_files[indx].split('/')[-1].split('.')[0].split('_')[0])
    captions_on_page = captions_on_page[0:4]
    images_on_page = images
    st.image(images_on_page, width=170, caption=captions_on_page)


# Helper function to return restaurant ids for recommendations
def get_image_recs(img_path, num_recs):
  img_features = extract_features(img_path,resnet_model)
  distances, indices = neighbors.kneighbors([img_features])
  # Since this image is from outside our images, first image is ok to take as recommendation
  similar_image_paths = [filenames[indices[0][i]] for i in range(0, num_recs)]
  rec_ids = []
  for filename in similar_image_paths:
    rec_ids.append(filename.split('/')[-1].split('.')[0].split('_')[0])
  # rec_ids = [i for n, i in enumerate(rec_ids) if i not in rec_ids[:n]]
  return rec_ids

# Helper function to return top images
def top_images(img_path, num_recs):
  img_features = extract_features(img_path,resnet_model)
  distances, indices = neighbors.kneighbors([img_features])
  # Since this image is from outside our images, first image is ok to take as recommendation
  similar_image_paths = [filenames[indices[0][i]] for i in range(0, num_recs)]
  github_files = []
  for filename in similar_image_paths:
      github = '/app/pizza_vision/web_app/yelp_only/' + classname_filename(filename)
      github_files.append(github)
  return github_files

# Helper function to extract resnet features from an image
def extract_features(img, model):
    input_shape = (224, 224, 3)
    img_array = image_process.img_to_array(img)
    expanded_img_array = np.expand_dims(img_array, axis=0)
    preprocessed_img = preprocess_input(expanded_img_array)
    features = model.predict(preprocessed_img)
    flattened_features = features.flatten()
    normalized_features = flattened_features / norm(flattened_features)
    return normalized_features

# Helper function to clean user input text before TFIDF
def clean_text(input):
  total_df = pd.DataFrame([input],columns=['pizza_words'])
  total_df['tokenized'] = total_df['pizza_words'].apply(word_tokenize)
  total_df['lower'] = total_df['tokenized'].apply(lambda x: [word.lower() for word in x])
  punc = string.punctuation
  total_df['no_punc'] = total_df['lower'].apply(lambda x: [word for word in x if word not in punc])
  total_df['stopwords_removed'] = total_df['no_punc'].apply(lambda x: [word for word in x if word not in sw])
  total_df['pos_tags'] = total_df['stopwords_removed'].apply(nltk.tag.pos_tag)
  def get_wordnet_pos(tag):
      if tag.startswith('J'):
          return wordnet.ADJ
      elif tag.startswith('V'):
          return wordnet.VERB
      elif tag.startswith('N'):
          return wordnet.NOUN
      elif tag.startswith('R'):
          return wordnet.ADV
      else:
          return wordnet.NOUN
  total_df['wordnet_pos'] = total_df['pos_tags'].apply(lambda x: [(word, get_wordnet_pos(pos_tag)) for (word, pos_tag) in x])
  wnl = WordNetLemmatizer()
  total_df['lemmatized'] = total_df['wordnet_pos'].apply(lambda x: [wnl.lemmatize(word, tag) for word, tag in x])
  total_df['clean_pizza'] = [' '.join(map(str, l)) for l in total_df['lemmatized']]
  total_df['clean_pizza']  = total_df['clean_pizza'] .str.replace(r'\d+','',regex=True) # remove numbers
  clean_string = total_df.iloc[0,0]
  return clean_string

st.sidebar.write(
    '''
    __About__ \n
    This project was built from just under 1000 scraped restaurants in the Chicagoland area. The user reviews were used to create vectors across the pizza spectrum for comparisons between pizzas. 
    \n
    This site was created by Ethan Feldman. You can find him on [GitHub](https://github.com/ejfeldman7), [LinkedIn](https://www.linkedin.com/in/feldmanethan/), [Medium/TDS](https://ethan-feldman.medium.com/) and his [website](https://www.ejfeldman.com/).
    ''')
st.title('Pizza-Vision')
st.write('A few years ago, our favorite pizzeria closed and ever since, my wife and I have not been able to find a new pizza that matched the same inocuous style. In an attempt to find new pizza, I created the recommendation system that filters by similar images and then recommends based on similarity to user reviews.')
st.write('To use this recommender, try adding an image and a description of the pizza you want. Try to think about the style, the crust type, flavors, and more in your description.')
st.write('You must add text and an image to get a recommendation')
user_text = st.text_input("Write a couple sentences (the more the better) to describe your pizza", '')

st.title("Upload + Classification Example")

uploaded_file = st.file_uploader("Choose an image...", type="jpg")

if ((uploaded_file is not None) & (user_text != '')):
    # user_image = Image.open(uploaded_file)
    # image_other = image.load_img(uploaded_file,target_size=(input_shape[0], input_shape[1]))
    image = Image.open(uploaded_file)
    newsize = (224, 224) 
    image = image.resize(newsize) 
    # st.image(image, caption='Uploaded Image.', use_column_width=True)
    st.write("")
    st.write("Working on a recommendation...")

    # Get the 25 closest images to the input using Nearest Neighbors by Euclidean distance
    neighbors = NearestNeighbors(n_neighbors=25, algorithm='brute', metric='euclidean').fit(feature_list)

    # Get 25 recommended images for an image (placeholder file entered for now)
    image_recs = get_image_recs(image,25)
    recommended_image_files = top_images(image,25)

    # Use this to find and show the top images, along with the uploaded image (placeholder files for now)
    # Since this image is from outside our images, first image is ok to take as recommendation
    distances, indices = neighbors.kneighbors([extract_features(image,resnet_model)])
    similar_image_paths = [uploaded_file] + [filenames[indices[0][i]] for i in range(0, 3)]
    # st.write(indices[0][0:3])
    # st.write(recommended_image_files)

    '''__Now I'll take the top 25 closest images and find the three restaurants whose reviews match your text most closely__'''
    # Get dataframe of 25 recommended pizzas from full restaurant list
    image_recs_df = nmf_df[nmf_df['id'].isin(image_recs) & (nmf_df['pizza_words'] != '')].reset_index()

    # Get user text input (placeholder for now) and clean it for topic modeling
    user_text = clean_text(user_text)
    # Vectorize user text, do topic modeling
    vt = tfidf.transform([user_text]).todense() # 
    tt1 = nmf.transform(vt)
    doc_topic = image_recs_df[['Delivery','Italian','Deep Dish','Pizza Puffs','NY/Detroit','Tavern Style','Bar Food']]

    # Find cosine distances between image recommendations and input text
    indices = pairwise_distances(tt1.reshape(1,-1),doc_topic,metric='cosine').argsort()

    # Select the top three closest user reviews with the input text and find those restaurants
    recs = list(indices[0][0:4])
    # Get urls of those recommendations
    url_of_recs = list(image_recs_df.iloc[recs]['index'])
    # Get images of those recommendations
    # unique_recs = 
    indices_for_images = [x for x in range(len(image_recs)) if image_recs[x] in list(image_recs_df.iloc[recs[0:3]]['id'])]
    end_result = [uploaded_file]+[recommended_image_files[i] for i in indices_for_images]

    # Report back the final recommendations
    st.write('Based on your image and text description, the following options are recommended:') #str(item)
    st.write('\n')
    st.write('I recommnend you try [{}]({}), located at {}'.format(image_recs_df.iloc[recs[0]]['name'],url_df.iloc[url_of_recs[0]]['rest_url'],image_recs_df.iloc[recs[0]]['address']))
    st.write('\n')
    st.write('I recommnend you try [{}]({}), located at {}'.format(image_recs_df.iloc[recs[1]]['name'],url_df.iloc[url_of_recs[1]]['rest_url'],image_recs_df.iloc[recs[1]]['address']))
    st.write('\n')
    st.write('I recommnend you try [{}]({}), located at {}'.format(image_recs_df.iloc[recs[2]]['name'],url_df.iloc[url_of_recs[2]]['rest_url'],image_recs_df.iloc[recs[2]]['address']))
   
    # st.write('I recommend you try:',image_recs_df.iloc[recs[0]]['name'],'located at',image_recs_df.iloc[recs[0]]['address'],'.')
    # st.write('\n')
    # st.write('I recommend you try:',image_recs_df.iloc[recs[1]]['name'],'located at',image_recs_df.iloc[recs[1]]['address'],'.')
    # st.write('\n')
    # st.write('I recommend you try:',image_recs_df.iloc[recs[2]]['name'],'located at',image_recs_df.iloc[recs[2]]['address'],'.')
    # plot_images(end_result, distances[0])

    '''
      
      
    __If you would prefer, you may also consider the recommendation based solely on the most similar images. Below, you can find your input image and the three most similar images, without using the reviews in the recommendation.__'''
    plot_images(similar_image_paths, distances[0])

