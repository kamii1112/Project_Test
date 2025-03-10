import json
import os
import uuid
from github import Github
from rest_framework.response import Response
from rest_framework import status, views

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")

class Table(views.APIView):

    def get(self, request, *args, **kwargs):
        """Retrieve all tables of a specific database."""
        database_name = request.data.get("database_name")

        if not database_name:
            return Response(
                {"error": "Database name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)

            # List contents of the repository to check if the database folder exists
            contents = repo.get_contents("")
            folders = [content.path for content in contents if content.type == "dir"]

            # Check if the database folder exists
            if database_name not in folders:
                return Response({"error": "Database does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            # Define path to the database folder
            database_path = f"{database_name}/Tables"
            tables = []

            # List contents of the database folder to get all table files
            try:
                table_files = repo.get_contents(database_path)
                for table in table_files:
                    # Only add files that are tables (ignoring subfolders)
                    if table.type == "file" and table.name != ".gitkeep":
                        tables.append(table.name.split('.')[0])

                if not tables:
                    return Response({"tables": tables}, status=status.HTTP_200_OK)

                return Response({"tables": tables}, status=status.HTTP_200_OK)

            except:
                return Response({"error": "Database folder does not contain any tables"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        """Delete the table schema and data from the GitHub repository"""
        database_name = request.data.get("database_name")
        table_name = request.data.get("table_name")

        if not database_name or not table_name:
            return Response(
                {"error": "Database name and table name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Initialize GitHub API client
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)

            # Define paths for schema and table files
            schema_path = f"{database_name}/Schema/{table_name}.json"
            table_path = f"{database_name}/Tables/{table_name}.json"

            # Check if the schema file exists and delete it
            try:
                schema_file = repo.get_contents(schema_path)
                repo.delete_file(schema_path, f"Deleted schema for table {table_name}", schema_file.sha)
            except:
                return Response({"error": f"Schema file for table {table_name} not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check if the table file exists and delete it
            try:
                table_file = repo.get_contents(table_path)
                repo.delete_file(table_path, f"Deleted table data for {table_name}", table_file.sha)
            except:
                return Response({"error": f"Table file for {table_name} not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": f"Table {table_name} and its schema deleted successfully!"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)