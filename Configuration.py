class Configuration:
    def __init__(self, search_by, query, allow_duplicates, export, export_path, export_extension):
        self.search_by = search_by
        self.query = query
        self.allow_duplicates = allow_duplicates
        self.export = export
        self.export_path = export_path
        self.export_extension = export_extension
