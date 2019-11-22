# utility functions


def get_major_version(version: str) -> str:
    """
    Given a StarChat version as a string returns major version
    :param version: string containing StarChat version
    :return: major version as a string
    """
    return version.split('.')[0]
