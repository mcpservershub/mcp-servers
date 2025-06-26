import docker
import docker.errors
from typing import Optional

from docker import DockerClient
from llm_sandbox.const import SupportedLanguage


def image_exists(client: DockerClient, image: str) -> bool:
    """
    Check if a Docker image exists
    :param client: Docker client
    :param image: Docker image
    :return: True if the image exists, False otherwise
    """
    try:
        client.images.get(image)
        return True
    except docker.errors.ImageNotFound:
        return False
    except Exception as e:
        raise e


def get_libraries_installation_command(lang: str, library: str) -> Optional[str]:
    """
    Get the command to install libraries for the given language
    :param lang: Programming language
    :param library: List of libraries
    :return: Installation command
    """
    if lang == SupportedLanguage.PYTHON:
        return f"pip install {library}"
    elif lang == SupportedLanguage.JAVA:
        return f"mvn install:install-file -Dfile={library}"
    elif lang == SupportedLanguage.JAVASCRIPT:
        return f"yarn add {library}"
    elif lang == SupportedLanguage.CPP:
        return f"apt-get install {library}"
    elif lang == SupportedLanguage.GO:
        return f"go get -u {library}"
    elif lang == SupportedLanguage.RUBY:
        return f"gem install {library}"
    elif lang == SupportedLanguage.CSHARP:
        return f"dotnet add package {library}"
    else:
        raise ValueError(f"Language {lang} is not supported")


def get_code_file_extension(lang: str) -> str:
    """
    Get the file extension for the given language
    :param lang: Programming language
    :return: File extension
    """
    if lang == SupportedLanguage.PYTHON:
        return "py"
    elif lang == SupportedLanguage.JAVA:
        return "java"
    elif lang == SupportedLanguage.JAVASCRIPT:
        return "js"
    elif lang == SupportedLanguage.CPP:
        return "cpp"
    elif lang == SupportedLanguage.GO:
        return "go"
    elif lang == SupportedLanguage.RUBY:
        return "rb"
    elif lang == SupportedLanguage.CSHARP:
        return "cs"
    else:
        raise ValueError(f"Language {lang} is not supported")


def get_code_execution_command(lang: str, code_file: str) -> list:
    """
    Return the execution command for the given language and code file.
    
    For C#, the code_file parameter is expected to be a path to a project directory 
    containing a valid .NET project (with a .csproj file).
    
    :param lang: Language of the code
    :param code_file: Path to the code file or, for C#, a project directory
    :return: List of execution commands
    """
    if lang == SupportedLanguage.PYTHON:
        return [f"python {code_file}"]
    elif lang == SupportedLanguage.JAVA:
        return [f"java {code_file}"]
    elif lang == SupportedLanguage.JAVASCRIPT:
        return [f"node {code_file}"]
    elif lang == SupportedLanguage.CPP:
        return [f"g++ -o a.out {code_file}", "./a.out"]
    elif lang == SupportedLanguage.GO:
        return [f"go run {code_file}"]
    elif lang == SupportedLanguage.RUBY:
        return [f"ruby {code_file}"]
    elif lang == SupportedLanguage.CSHARP:
        # For C#, code_file should be a directory containing a valid .NET project.
        return [f"dotnet run --project {code_file}"]
    else:
        raise ValueError(f"Language {lang} is not supported")
