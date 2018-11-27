import requests
import re
import time
import os
import csv
from bs4 import BeautifulSoup
from collections import Counter
from random import randint, shuffle
from Configuration import Configuration
from SearchResult import SearchResult


AZLYRICS_SEARCH_URL = 'https://search.azlyrics.com/search.php'
AZLYRICS_BASE_URL = 'https://www.azlyrics.com'


class InvalidArgumentsError(Exception):
    """An exception that indicates that the command line arguments for the program's execution are invalid."""
    pass


class NoResultsError(Exception):
    """An exception that indicates that 0 search results were returned."""
    pass


def check_file_extension_exists(file_name):
    """Check to see if the file name has a file extension.

    Parameters
    ----------
    file_name : str
        name of the file to check

    Raises
    ------
    InvalidArgumentsError
        if there is no file extension
    """
    if len(file_name.rsplit('.', 1)) < 2:
        raise InvalidArgumentsError('No file extension listed in export path `{}`'.format(file_name))


def read_args(args):
    mode_flag = args[1]
    mode_flag_idx = args.index(mode_flag)
    export = '--export' in args
    export_flag_idx = args.index('--export') if export else None

    if export:
        if export_flag_idx < mode_flag_idx:
            raise InvalidArgumentsError('`--export` must come after `{}`'.format(mode_flag))

        if export_flag_idx == mode_flag_idx+1:
            raise InvalidArgumentsError('`--export` cannot come right after `{}`. Should have search query between.'
                                        .format(mode_flag))

        if export_flag_idx == len(args)-1:
            raise InvalidArgumentsError('`--export` must have the <file_path> listed after it.')

    search_query_string = ' '.join(args[mode_flag_idx+1:export_flag_idx])
    allow_duplicates = '--duplicates' in args
    export_path = args[export_flag_idx+1] if export else None
    if export_path:
        check_file_extension_exists(export_path)
    export_extension = export_path.rsplit('.', 1)[-1].lower() if export_path else None

    return Configuration(mode_flag[2:], search_query_string, allow_duplicates, export, export_path, export_extension)


def get_url_soup(url, params=None):
    page = requests.get(url, params=params)
    return BeautifulSoup(page.content, 'html.parser')


def no_results(doc):
    return len(doc.xpath("//div[@class='alert']")) != 0


def search(params):
    doc = get_url_soup(AZLYRICS_SEARCH_URL, params)
    if doc.findAll('div', {'class': 'alert'}):
        raise NoResultsError('No search results were found for the query: `{}`'.format(params['q']))

    search_results = []
    result_list = doc.findAll('td', {'class': 'text-left'})
    for result in result_list:
        # Remove digit
        text = re.sub(r'^\d+.\s', '', result.text.strip())
        # Isolate first line
        text = re.sub(r' +', ' ', text).split('\n')[0]
        # Grab first link
        link = result.findAll('a')[0]['href']
        search_results.append(SearchResult(text, link))

    return search_results


def print_search_results(search_results):
    print('Search Results:')
    for i in range(1, len(search_results)+1):
        print('{}.\t{}'.format(i, search_results[i-1].text))


def prompt_search_result_selection(search_results):
    user_input = None
    while not user_input or not str(user_input).isnumeric() or not int(user_input) in range(1, len(search_results)+1):
        print_search_results(search_results)
        if user_input:
            if not str(user_input).isnumeric():
                print('`{}` is not a number. Please enter a number.'.format(user_input))
            elif int(user_input) < 1 or int(user_input) > len(search_results):
                print('`{}` is not between 1 and {}.'.format(user_input, len(search_results)))
        user_input = input('Enter the number of desired search result: ')

    return int(user_input)-1


def scrape_song_lyrics(song_url):
    doc = get_url_soup(song_url)
    div_container = doc.find('div', {'class': 'ringtone'}).findNext('div')
    text = div_container.text
    # Remove all text between brackets
    text = re.sub(r'\[.+\]', '', text)
    # Remove all punctuations
    text = re.sub(r'[^\w\s\d\']', '', text)
    # Remove duplicate adjacent whitespace
    text = re.sub(r'\s+', ' ', text)
    words = [w.lower() if not re.search(r"^I('|$)", w) else w for w in text.split()]
    return Counter(words)


def scrape_artist_lyrics(artist_url):
    doc = get_url_soup(artist_url)
    div_container = doc.find('div', {'id': 'listAlbum'})
    song_elems = div_container.findAll('a', {'target': '_blank'})
    shuffle(song_elems)

    word_frequencies = Counter()
    for song in song_elems:
        time.sleep(randint(3, 25)) # Wait a random amount of seconds
        word_frequencies += scrape_song_lyrics(AZLYRICS_BASE_URL + song['href'][2:])
    
    return word_frequencies


def scrape_album_lyrics(album_url):
    artist_url, album_id = album_url.split('#')
    doc = get_url_soup(artist_url)

    div_container = doc.find('div', {'id': 'listAlbum'})
    div_child_elems = div_container.find_all(recursive=False)

    entered = False
    div_count = 0
    song_elems = []
    for elem in div_child_elems:
        if elem.has_attr('id') and elem['id'] == album_id:
            entered = True
        if entered:
            if elem.name == 'div':
                div_count += 1
            if elem.has_attr('target') and elem['target'] == '_blank':
                song_elems.append(elem)
        if div_count == 2:
            break
    
    shuffle(song_elems)
    word_frequencies = Counter()
    for song in song_elems:
        time.sleep(randint(3, 25)) # Wait a random amount of seconds
        word_frequencies += scrape_song_lyrics(AZLYRICS_BASE_URL + song['href'][2:])
    return word_frequencies


def export_word_frequencies_to_csv(word_frequencies, export_path):
    if os.path.dirname(export_path):
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
    with open(export_path, 'w', newline="") as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=",", quotechar='"')
        csv_writer.writerow(['Word', 'Frequency'])
        for word, frequency in word_frequencies.most_common():
            csv_writer.writerow([word, frequency])