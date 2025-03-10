import os 
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")


class GitHubSerivce:
    @staticmethod
    def get_repo_content():
        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            contents = repo.get_contents("")
            return contents
        except Exception as e:
            raise Exception(f"Error fetching repo contents: {str(e)}")
        
    @staticmethod
    def get_repo_folders():
        """
        This method fetches all the folders of the repository
        """

        try:
            contents = GitHubSerivce.get_repo_content()
            folders = [content.path for content in contents if content.type == "dir"]
            return folders
        except Exception as e:
            raise Exception(f"Error fetching folder contents: {str(e)}")
        
    
