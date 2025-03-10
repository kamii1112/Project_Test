import json
import os
import uuid
from github import Github
from rest_framework.response import Response
from rest_framework import status, views
from dotenv import load_dotenv

load_dotenv()

class GitHubStorage(views.APIView):

    def post(self, request, *args, **kwargs):
        """Store JSON data in a GitHub repository, allowing multiple objects"""
        file_name = request.data.get("file_name")
        new_data = request.data.get("data")

        if not file_name or not new_data:
            return Response({"error": "File name and data are required"}, status=status.HTTP_400_BAD_REQUEST)

        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")

        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            file_path = f"{file_name}.json"

            try:
                file = repo.get_contents(file_path)
                existing_data = json.loads(file.decoded_content.decode("utf-8"))

                if not isinstance(existing_data, list):
                    existing_data = [existing_data]  # Convert to list if necessary

            except:
                existing_data = []

            # Ensure `new_data` is a list
            if not isinstance(new_data, list):
                new_data = [new_data]

            # Assign unique IDs to each object
            for obj in new_data:
                obj["id"] = str(uuid.uuid4())  # Generate a unique ID

            updated_data = existing_data + new_data
            updated_content = json.dumps(updated_data, indent=4)

            if 'file' in locals():
                repo.update_file(file_path, "Added new data", updated_content, file.sha)
            else:
                repo.create_file(file_path, "Created new file with data", updated_content)

            return Response({"message": "Data stored successfully!"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get(self, request, *args, **kwargs):
        """Retrieve all JSON data or a specific object by ID"""
        file_name = request.query_params.get("file_name")
        obj_id = request.query_params.get("id")  # Get ID if provided

        if not file_name:
            return Response({"error": "File name is required"}, status=status.HTTP_400_BAD_REQUEST)

        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")

        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            file_path = f"{file_name}.json"

            try:
                file = repo.get_contents(file_path)
                existing_data = json.loads(file.decoded_content.decode("utf-8"))

                if obj_id:
                    filtered_data = next((obj for obj in existing_data if obj.get("id") == obj_id), None)
                    if not filtered_data:
                        return Response({"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND)
                    return Response(filtered_data, status=status.HTTP_200_OK)

                return Response(existing_data, status=status.HTTP_200_OK)

            except:
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request, *args, **kwargs):
        """Delete an object from the JSON file by ID"""
        file_name = request.data.get("file_name")
        obj_id = request.data.get("id")

        if not file_name or not obj_id:
            return Response({"error": "File name and object ID are required"}, status=status.HTTP_400_BAD_REQUEST)

        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")

        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            file_path = f"{file_name}.json"

            try:
                file = repo.get_contents(file_path)
                existing_data = json.loads(file.decoded_content.decode("utf-8"))

                if not isinstance(existing_data, list):
                    existing_data = [existing_data]

                updated_data = [obj for obj in existing_data if obj.get("id") != obj_id]

                if len(updated_data) == len(existing_data):
                    return Response({"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND)

                updated_content = json.dumps(updated_data, indent=4)
                repo.update_file(file_path, "Deleted an object from the JSON file", updated_content, file.sha)

                return Response({"message": "Object deleted successfully!"}, status=status.HTTP_200_OK)

            except:
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, *args, **kwargs):
        """Update a specific object by ID in the JSON file"""
        file_name = request.data.get("file_name")
        obj_id = request.data.get("id")
        update_data = request.data.get("data")

        if not file_name or not obj_id or not update_data:
            return Response({"error": "File name, object ID, and update data are required"}, status=status.HTTP_400_BAD_REQUEST)

        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")

        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            file_path = f"{file_name}.json"

            try:
                file = repo.get_contents(file_path)
                existing_data = json.loads(file.decoded_content.decode("utf-8"))

                if not isinstance(existing_data, list):
                    existing_data = [existing_data]

                for obj in existing_data:
                    if obj.get("id") == obj_id:
                        obj.update(update_data)  # Update only the provided fields
                        break
                else:
                    return Response({"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND)

                updated_content = json.dumps(existing_data, indent=4)
                repo.update_file(file_path, "Updated an object in the JSON file", updated_content, file.sha)

                return Response({"message": "Object updated successfully!"}, status=status.HTTP_200_OK)

            except:
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
