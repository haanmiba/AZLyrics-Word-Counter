import sys
from requests.exceptions import ConnectionError
from Utility import read_args, search, prompt_search_result_selection, scrape_artist_lyrics, scrape_song_lyrics, scrape_album_lyrics


USAGE_STR = 'usage: python Driver.py [--artist | --song | --album] <search_query> (--export <file_path>) (--duplicates)'
ALLOWED_FLAGS = {'--artists', '--songs', '--albums', '--export', '--duplicates'}
ALLOWED_MODE_FLAGS = {'--artists', '--songs', '--albums'}


def main():
    # Check if the user input less than 3 command line arguments. If so, terminate the program with exit code 1.
    if len(sys.argv) < 3:
        print('This program requires at least 3 command line arguments.')
        print(USAGE_STR)
        sys.exit(1)
    
    # If the user did not enter a valid flag, terminate the program with exit code 1.
    if sys.argv[1] not in ALLOWED_MODE_FLAGS:
        print('`{}` is not a valid flag.'.format(sys.argv[1]))
        print(USAGE_STR)
        sys.exit(1)

    # Check if the user used an invalid flag. If so, terminate the program with exit code 1.
    invalid_flags = set(filter(lambda x: x.startswith('--'), sys.argv)) - ALLOWED_FLAGS
    if invalid_flags:
        print('`{}` is not a valid flag.'.format(next(iter(invalid_flags))))
        print(USAGE_STR)
        sys.exit(1)
    
    try:
        config = read_args(sys.argv)
        params = dict(q=config.query, w=config.search_by, p=1)
        search_results = search(params)
        result_index = prompt_search_result_selection(search_results) if len(search_results) > 1 else 0
        selected_result = search_results[result_index]

        if config.search_by == 'artists':
            word_frequencies = scrape_artist_lyrics(selected_result.link)
        elif config.search_by == 'songs':
            word_frequencies = scrape_song_lyrics(selected_result.link)
        elif config.search_by == 'albums':
            word_frequencies = scrape_album_lyrics(selected_result.link)

        print(word_frequencies.most_common())
        sys.exit(0)
    except ConnectionError as e:
        print('{}: Connection aborted.'.format(e.__class__.__name__))
        sys.exit(1)


if __name__ == '__main__':
    main()
