from flask import Flask
import os

from controllers.routes import configure_routes

app = Flask(__name__, static_folder='.', static_url_path='')

configure_routes(app)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

    # import nltk
    # nltk.download('brown')
    # import csv
    # from nltk.corpus import brown

    # # Get all words tagged as nouns, adjectives, or verbs
    # tagged_words = brown.tagged_words()
    # adjectives = [(word, 'adj') for word, pos in tagged_words if pos.startswith('JJ')]
    # nouns = [(word, 'noun') for word, pos in tagged_words if pos.startswith('NN')]
    # verbs = [(word, 'verb') for word, pos in tagged_words if pos.startswith('VB')]

    # # Combine the lists into one
    # all_words = adjectives + nouns + verbs

    # # Write to CSV, with each word and its type (adj, noun, verb) in separate columns
    # with open('word_lists.csv', 'w', newline='', encoding='utf-8') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(['Word', 'Type'])  # Header row
    #     writer.writerows(all_words)

    # print("CSV file 'word_lists.csv' created successfully.")

