class SearchResult:
    """Class that represents a search result.
    
    Attributes
    ----------
    text : str
        The title of the search result
    link : str
        The hyperlink for the webpage this search result links to
    """

    def __init__(self, text, link):
        """
        Parameters
        ----------
        text : str
            The title of the search result
        link : str
            The hyperlink for the webpage this search result links to
        """
        
        self.text = text
        self.link = link
