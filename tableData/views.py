import json
import os
import uuid
from github import Github
from rest_framework.response import Response
from rest_framework import status, views

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")

class TableData(views.APIView):

    def post(self, request, *args, **kwargs):
            """Create a new table schema in GitHub storage"""
            database_name = request.data.get("database_name")
            table_name = request.data.get("table_name")
            new_data = request.data.get("data")

            if not database_name or not table_name or not new_data:
                return Response(
                    {"error": "Database name, table name, and data are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                g = Github(GITHUB_TOKEN)
                repo = g.get_repo(REPO_NAME)

                table_path = f"{database_name}/Tables/{table_name}.json"
                try:
                    table_file = repo.get_contents(table_path)
                    existing_data = json.loads(table_file.decoded_content.decode("utf-8"))
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]


                except:
                    existing_data = []

                # Assign unique ID to each entry if not present
                if isinstance(new_data, list):
                    for entry in new_data:
                        if "id" not in entry:
                            entry["id"] = str(uuid.uuid4())
                    existing_data.extend(new_data)
                else:
                    if "id" not in new_data:
                        new_data["id"] = str(uuid.uuid4())
                    existing_data.append(new_data)

                # Update GitHub with new table data
                updated_content = json.dumps(existing_data, indent=4)
                if 'table_file' in locals():
                    repo.update_file(table_path, "Updated table with new data", updated_content, table_file.sha)
                else:
                    repo.create_file(table_path, "Created new table", updated_content)

                return Response({"message": "Data added successfully!"}, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        """Retrieve all JSON data or a specific object by ID"""
        database_name = request.data.get("database_name")  # Use query params for GET requests
        table_name = request.data.get("table_name")  # Use query params for GET requests
        object_id = request.data.get("id")  # The ID of the object to retrieve, if provided

        if not database_name or not table_name:
            return Response(
                {"error": "Database name and table name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            table_path = f"{database_name}/Tables/{table_name}.json"

            try:
                # Try to retrieve the file from GitHub
                file = repo.get_contents(table_path)
                existing_data = json.loads(file.decoded_content.decode("utf-8"))

                # If an ID is provided, filter the data to return the specific object
                if object_id:
                    # Find the object with the matching ID
                    filtered_data = next((item for item in existing_data if item.get("id") == object_id), None)
                    if filtered_data is not None:
                        return Response(filtered_data, status=status.HTTP_200_OK)
                    else:
                        return Response({"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND)
                
                # If no ID is provided, return all data
                return Response(existing_data, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": "Table not found or invalid data format", "details": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        """Delete objects from the JSON file by ID or delete all content if no IDs are provided."""
        database_name = request.data.get("database_name")
        table_name = request.data.get("table_name")
        obj_ids = request.data.get("ids")  # Array of IDs (can be empty or provided)

        if not database_name or not table_name:
            return Response({"error": "Database name and table name are required"}, status=status.HTTP_400_BAD_REQUEST)

        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")

        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            file_path = f"{database_name}/Tables/{table_name}.json"

            try:
                # Retrieve the file contents from the GitHub repository
                file = repo.get_contents(file_path)

                # Load existing data from the JSON file
                existing_data = json.loads(file.decoded_content.decode("utf-8"))

                # Ensure the existing data is a list
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]

                if obj_ids:
                    # If IDs are provided, try to delete those objects
                    updated_data = [obj for obj in existing_data if obj.get("id") not in obj_ids]

                    if len(updated_data) == len(existing_data):
                        # If no objects were deleted, return an error message
                        return Response({"error": "Objects not found"}, status=status.HTTP_404_NOT_FOUND)
                    else:
                        # If some objects were deleted, update the file
                        updated_content = json.dumps(updated_data, indent=4)
                        repo.update_file(file_path, "Deleted objects from the JSON file", updated_content, file.sha)
                        return Response({"message": "Objects deleted successfully!"}, status=status.HTTP_200_OK)

                else:
                    # If no IDs are provided, delete all content
                    updated_data = []
                    updated_content = json.dumps(updated_data, indent=4)
                    repo.update_file(file_path, "Deleted all content from the JSON file", updated_content, file.sha)
                    return Response({"message": "No IDs provided. All content deleted."}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": "File not found or error with file operations."}, status=status.HTTP_404_NOT_FOUND)

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
