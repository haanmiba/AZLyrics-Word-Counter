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
    """Takes command line arguments and converts them into the configuration for this program.

    Parameters
    ----------
    args : list(str,)
        A list of command line arguments
    
    Returns
    -------
    Configuration
        The configuration settings for this program's execution
    
    Throws
    ------
    InvalidArgumentsError
        If any of the command line arguments are invalid
    """

    # Extract information from the command line arguments
    mode_flag = args[1]
    mode_flag_idx = args.index(mode_flag)
    export = '--export' in args
    export_flag_idx = args.index('--export') if export else None
    print_frequencies = '--print' in args
    print_flag_idx = args.index('--print') if print_frequencies else None

    # Validate the user's command line arguments if they are exporting the data
    if export:

        # If they are exporting and the export flag comes before the mode flag, throw an InvalidArguentsError
        if export_flag_idx < mode_flag_idx:
            raise InvalidArgumentsError('`--export` must come after `{}`'.format(mode_flag))

        # If the export flag comes right after the mode flag, that means there were no search queries, throw an InvalidArgumentsError
        if export_flag_idx == mode_flag_idx+1:
            raise InvalidArgumentsError('`--export` cannot come right after `{}`. Should have search query between.'
                                        .format(mode_flag))

        # If the export flag is at the end of the command line arguments, that means the user did not enter the export path, throw an InvalidArgumentsError
        if export_flag_idx == len(args)-1:
            raise InvalidArgumentsError('`--export` must have the <file_path> listed after it.')

    export_path = args[export_flag_idx+1] if export else None
    # Check if the export file path has an extension
    if export_path:
        check_file_extension_exists(export_path)
    export_extension = export_path.rsplit('.', 1)[-1].lower() if export_path else None

    # Retrieve the search query string
    next_flag_idx = None
    if export_flag_idx and print_frequencies:
        next_flag_idx = min(export_flag_idx, print_flag_idx)
    elif export_flag_idx:
        next_flag_idx = export_flag_idx
    elif print_flag_idx:
        next_flag_idx = print_flag_idx
    search_query_string = ' '.join(args[mode_flag_idx+1:next_flag_idx])

    return Configuration(mode_flag[2:], search_query_string, export, export_path, export_extension, print_frequencies)


def get_url_soup(url, params=None):
    """Makes a GET request to a URL and returns that URL parsed through the BeautifulSoup module.

    Parameters
    ----------
    url : str
        The url to make the request to
    params : dict, optional (default=None)
        A dictionary of parameters to be put into the GET request
    
    Returns
    -------
    BeautifulSoup
        The page's HTML contents parsed through the BeautifulSoup module
    """

    page = requests.get(url, params=params)
    return BeautifulSoup(page.content, 'html.parser')


def no_results(doc):
    """Verifies whether there are any search results on an AZLyrics query.

    Returns
    -------
    bool
        True if there are no results
        False otherwise
    """

    return len(doc.findAll('div', {'class': 'alert'})) != 0


def search(params):
    """Performs a search query on AZLyrics and scrapes the search results.

    Parameters
    ----------
    params : str
        Parameters for the search query
    
    Returns
    -------
    list(SearchResult,)
        A list of search results returned from AZLyrics
    
    Raises
    ------
    NoResultsError
        If there were no search results returned
    """

    # Get the search result's BeautifulSoup and see if it has any search results
    doc = get_url_soup(AZLYRICS_SEARCH_URL, params)
    if no_results(doc):
        raise NoResultsError('No search results were found for the query: `{}`'.format(params['q']))

    # Compile all of the search results into a list of SearchResult instances
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
    """Print out the search results as an ordered list.

    Parameters
    ----------
    search_results : list(SearchResult,)
        A list of SearchResult instances to print out
    """

    print('Search Results:')
    for i in range(1, len(search_results)+1):
        print('{}.\t{}'.format(i, search_results[i-1].text))


def prompt_search_result_selection(search_results):
    """When there are multiple search results to choose from, prompt the user to select from them.

    Parameters
    ----------
    search_results : list(SearchResult,)
        A list of SearchResult instances for the user to choose from
    
    Returns
    -------
    int
        The index of the search result the user has selected
    """

    # Prompt user to keep entering input long as the input is invalid or the user has not submitted anything
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
    """Scrape the song lyrics from a song's page.

    Parameters
    ----------
    song_url : str
        The URL to a song page

    Returns
    -------
    Counter
        A count of the words that occur in the lyrics
    """

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
    """Scrape the lyrics of all songs on an artist's page.

    Parameters
    ----------
    artist_url : str
        The URL to an artist's page
    
    Returns
    -------
    Counter
        A count of the words that occur for all the song lyrics
    """

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
    """Scrape lyrics from an album

    Parameters
    ----------
    album_url : str
        The URL to an album. Note: The album's URL is simply a section within an artist's page
    
    Returns
    -------
    Counter
        A count of all the words that occur for htis album
    """

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
    """Exports the word frequencies to a CSV file.

    Parameters
    ----------
    word_frequencies : Counter
        A Counter instance of all words that occur within lyrics
    export_path : str
        The file path to the CSV file to export the Counter's data to
    """

    if os.path.dirname(export_path):
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
    with open(export_path, 'w', newline="") as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=",", quotechar='"')
        csv_writer.writerow(['Word', 'Frequency'])
        for word, frequency in word_frequencies.most_common():
            csv_writer.writerow([word, frequency])


def print_word_frequencies(word_frequencies):
    """Prints word frequencies from most occuring words to least

    Parameters
    ----------
    word_frequencies : Counter
        The Counter instance keeping track of all of the words that occur and their frequencies
    """
    
    print('----------------')
    print('Word Frequencies')
    print('----------------')
    for word, frequency in word_frequencies.most_common():
        print('{:<{fill}} {}'.format(word + ':', frequency, fill=max(map(len, word_frequencies.keys()))+1))
