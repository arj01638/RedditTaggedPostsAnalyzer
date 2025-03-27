class InsufficientData(Exception):
    def __init__(self, message="The data frame does not have enough data for analysis."):
        super().__init__(message)
