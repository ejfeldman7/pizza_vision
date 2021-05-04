# Pizza Vision Project

[The Streamlit app can be found here](https://share.streamlit.io/ejfeldman7/pizza_vision/main/web_app/pizza_vision.py), but for a short demo of the Streamlit app, please scroll to the bottom of this ReadMe.

# Contents

## In the Notebooks folder you will find:  
- Notebooks for scraping data from Yelp: pizza_from_yelp  
- Notebooks for computer vision (Resnet, Autoencoder): resnet_finetuning, resnet_knn_tsne, autoencoder  
- Notebooks for natural language processing: pizza_nmf_location  
- Notebooks for making a recommendation app: combined_pizza_recs, streamlit_pizza_vision  

## Ih the web_app folder you will find:
All pickles of data and models along with a .py file for the Streamlit app to run on

## In the Visuals folder you will find:  

An assortment of visuals used for the presentation

# Summary of Work and Findings  

## Process

I scraped just under 1000 Chicagoland restaurant Yelp pages for both images tagged as pizza and recommended reviews. Images were then manually cleaned to remove items that were clearly not pizza. Reviews were cleaned first to contain only sentences that contain "pizza words" and then concatenated together to form a document for each restaurant. 

While I tried using a pretrained Resnet model, a finetuned Resnet model, and a custom Autoencoder model, I found that the pretrained Resnet model performed the best on identifying similar images. This was a subjective decision made by comparing top recommended pizzas from randomly selected input pizzas and identifying flaws (recommending deep dish when the input was Neopolitan). In this process, I decided the recommendations from the images alone needed additional support, but that they did an excellect job of filtering to a smaller subset from which to recommend.

Using the nearest twenty five neighbors to a given image's Resnet feature weights, I then used a comparison of reviews to finalize the top three recommendations. I implemented topic modeling using Non-negative Matrix Factorization on a TF-IDF embedding of each review to turn each review into a shorter vector. The dimensions of this vector identified each review as falling into categories I identified "Deep Dish" or "Italian Restaurant" by the identifying the most common words and most central restaurants to each group.

The recommendation enginge filters restaurants initially by a nearest neighbors algorithm using Euclidean distance to identify the 25 most similar images. Those images are then used to identify the top potential restaurants, whose review documents are then compared against the user text input. Using cosine similarity, I then output the top three recommended restaurants overall for future pizza exploration.

## Findings

I was surprised at how well using the pretrained Resnet weights worked for comparing pizzas. Going in to the project, I had expected the models that trained on pizzas to output better recommendations. I believe image quality issues from Yelp, in particular focus, lighting, and angle, led to worse results upon training. I think, for the future, finding a source of more, higher quality, consistent images could allow me to return to creating a better model from the images. 

In comparing the recommendations from using only images, only text, or a combination, I do believe that the outputs from the combined version appear most trustworthy. However, to truly identify success in this area, I think I'll need to eat a lot of pizza to confirm. That's a sacrifice I'm willing to make. Early returns on recommendations have been strong and I am committed to seeing this effort through.

## Demo

![Streamlit Demo Gif](https://github.com/ejfeldman7/pizza_vision/blob/main/Visuals/app_demo_2.gif)


