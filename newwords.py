import argparse
import os
import string

import frontmatter
import nltk
import pyatproto
from nltk.stem.wordnet import WordNetLemmatizer

import config

parser = argparse.ArgumentParser()

parser.add_argument("--path", help="path to blog post")
parser.add_argument("--full_path", help="path to all other blog posts")

args = parser.parse_args()

if not args.path or not args.full_path:
    raise ValueError(
        "Please set the path to the blog post and the path to all other blog posts"
    )
FULL_PATH = args.full_path

ENDPOINT = config.ATPROTO_ENDPOINT
USERNAME = config.ATPROTO_USERNAME
PASSWORD = config.ATPROTO_PASSWORD

if not ENDPOINT or not USERNAME or not PASSWORD:
    raise ValueError(
        "Please set the ATPROTO_ENDPOINT, ATPROTO_USERNAME and ATPROTO_PASSWORD environment variables."
    )

lemmatizer = WordNetLemmatizer()


def normalize_word(word) -> str:
    """
    Normalize a word by removing punctuation, lemmatizing, lowercasing, and rejecting short words, proper nouns, and words with numbers.
    """
    # if proper noun, return empty string
    pos = nltk.pos_tag([word])[0][1]

    if pos == "NNP" or pos == "NNPS":
        return ""

    if word.startswith("http"):
        return ""

    # if word contains numbers, skip
    if any(char.isdigit() for char in word):
        return ""

    if "'" in word:
        word = word.split("'")[0]

    word = word.strip(string.punctuation)

    lemma = lemmatizer.lemmatize(word)

    if len(lemma) < 4:
        return ""

    return lemma.lower()


def get_words_from_all_posts() -> tuple:
    documents = {}

    sorted_file_list = os.listdir(FULL_PATH)

    sorted_file_list.sort()

    for filename in sorted_file_list:
        if filename.endswith(".md"):
            with open(os.path.join(FULL_PATH, filename), "r") as f:
                documents[os.path.join(FULL_PATH, filename)] = frontmatter.load(
                    f
                ).content

    words = {}

    for document in documents.values():
        for word in document.split():
            word = normalize_word(word)
            if word in words:
                words[word] += 1
            else:
                words[word] = 1

    return documents, words


def get_unique_words_from_newest_post(documents: dict, words: dict) -> dict:
    newest_post = documents[args.path]

    newest_post_words = {}

    for word in newest_post.split():
        word = normalize_word(word)

        if words[word] > 1:
            continue

        if word in newest_post_words:
            newest_post_words[word] += 1
        else:
            newest_post_words[word] = 1

    return newest_post_words


documents, words = get_words_from_all_posts()
newest_post_words = get_unique_words_from_newest_post(documents, words)

ap = pyatproto.AtProtoConfiguration(ENDPOINT, USERNAME, PASSWORD)

word_list = "\n".join([f"{word}" for word in newest_post_words])

bluesky_post = (
    "In my most recent blog post, I used the following words for the first time:\n\n"
    + word_list
)

post = ap.create_post(bluesky_post)
