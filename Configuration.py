class Configuration:
    """A class that represents the configuration for this program.

    Attributes
    ----------
    search_by : str
        The type of query to search on AZLyrics (artists, songs, album)
    query : str
        The actual search query
    export : bool
        Whether or not the program will export the data to an external file
    export_path : str
        The path to the file where the program will export the data
    export_extension : str
        The file extension of the output file
    print_frequencies : bool
        Whether or not the program will print the frequencies to the command line
    """

    def __init__(self, search_by, query, export, export_path, export_extension, print_frequencies):
        """
        Parameters
        ----------
        search_by : str
            The type of query to search on AZLyrics (artists, songs, album)
        query : str
            The actual search query
        export : bool
            Whether or not the program will export the data to an external file
        export_path : str
            The path to the file where the program will export the data
        export_extension : str
            The file extension of the output file
        print_frequencies : bool
            Whether or not the program will print the frequencies to the command line
        """
        
        self.search_by = search_by
        self.query = query
        self.export = export
        self.export_path = export_path
        self.export_extension = export_extension
        self.print_frequencies = print_frequencies
