import os 
from github import Github, GithubException
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .methods import GitHubSerivce

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")

class DatabaseManager(APIView):

    def post(self, request):
        database_name = request.data.get("database_name")

        if not database_name:
            return Response({"error": "Database name is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:

            repo = Github(GITHUB_TOKEN).get_repo(REPO_NAME)
            
            folders = GitHubSerivce.get_repo_folders()
            if folders.__contains__(database_name):
                return Response({"error" : f"Database '{database_name}' is already Present!"})

            subFolders = ['Tables', 'Schema']

            for subfolder in subFolders:
                table_path = f"{database_name}/{subfolder}/.gitkeep"

                try:
                    # Check if the file already exists
                    repo.get_contents(table_path)
                except GithubException:
                    # Create an empty .gitkeep file in each subfolder
                    repo.create_file(table_path, f"Created {database_name}/{subfolder}", "", branch="main")

            return Response({"message": f"Database '{database_name}' created successfully!"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request):
        """Retrieve all folders in the repository"""
        try:

            databases = GitHubSerivce.get_repo_folders()
            return Response({"databases": databases}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
     
    def delete(self, request):
        """Delete a folder and its contents (including subfolders) from the repository"""
        database_name = request.data.get("database_name")

        if not database_name:
            return Response({"error": "Database name is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)

            contents = repo.get_contents("")
            folders = [content.path for content in contents if content.type == "dir"]
            if not folders.__contains__(database_name):
                            return Response({"error": "Database is not present"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            table_path = f"{database_name}/"

            # Recursive function to delete all files in a folder (and its subfolders)
            def delete_contents(path):
                # Get all the contents in the folder (or subfolder)
                contents = repo.get_contents(path)

                for content in contents:
                    if content.type == "dir":
                        # Recursively delete contents of subfolders
                        delete_contents(content.path)
                    else:
                        # Delete files
                        repo.delete_file(content.path, f"Deleted file: {content.path}", content.sha)

            # Start the deletion from the root folder
            delete_contents(table_path)

            # After deleting all files and subfolders, the parent folder is automatically removed if empty
            return Response({"message": f"Database '{database_name}' and its contents deleted successfully!"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

  # def put(self, request):
    #     """Rename a folder in the repository"""
    #     old_database_name = request.data.get("old_database_name")
    #     new_database_name = request.data.get("new_database_name")

    #     if not old_database_name or not new_database_name:
    #         return Response({"error": "Both old and new database names are required"}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         g = Github(GITHUB_TOKEN)
    #         repo = g.get_repo(REPO_NAME)

    #         old_table_path = f"{old_database_name}/"
    #         new_table_path = f"{new_database_name}/"

    #         # Get all contents in the old folder
    #         contents = repo.get_contents(old_table_path)

    #         if not contents:
    #             return Response({"error": f"Folder '{old_database_name}' not found"}, status=status.HTTP_404_NOT_FOUND)

    #         # Iterate through the contents of the old folder and move files to the new folder
    #         for file in contents:
    #             old_file_path = file.path
    #             new_file_path = old_file_path.replace(old_table_path, new_table_path)

    #             # Check if the file is a text file or binary
    #             if file.encoding == "base64":  # binary file
    #                 file_content = file.content  # Base64 encoded content
    #             else:  # text file
    #                 file_content = file.decoded_content.decode("utf-8")  # Decode content to string

    #             # Create the file in the new folder
    #             repo.create_file(new_file_path, f"Moved file from {old_database_name} to {new_database_name}", file_content)

    #             # Delete the old file after moving
    #             repo.delete_file(old_file_path, f"Deleted old file: {old_database_name}", file.sha)

    #         # Now, check if the old folder is empty and delete it if necessary
    #         return Response({"message": f"Folder renamed from '{old_database_name}' to '{new_database_name}'"}, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

