import json
import os
import uuid
from github import Github
from rest_framework.response import Response
from rest_framework import status, views

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")


class CreateTable(views.APIView):
    def post(self, request, *args, **kwargs):
        """Create a new table schema in GitHub storage"""
        database_name = request.data.get("database_name")
        table_name = request.data.get("table_name")
        schema = request.data.get("schema")

        if not database_name or not table_name or not schema:
            return Response(
                {"error": "Database name, table name, and schema are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate the schema
        if not isinstance(schema, dict):
            return Response(
                {"error": "Schema should be a valid dictionary"},
                status=status.HTTP_400_BAD_REQUEST
            )

        def validate_schema_field(field, field_type):
            """Recursively validate schema fields to support nested objects and arrays"""
            if isinstance(field_type, dict):
                # If the field is a nested object, recursively validate its fields
                for subfield, subfield_type in field_type.items():
                    validate_schema_field(subfield, subfield_type)
            elif isinstance(field_type, list):
                # If the field is an array, check the type of items inside the array
                if len(field_type) == 1 and isinstance(field_type[0], dict):
                    # Array of objects (nested)
                    for index, item in enumerate(field_type):
                        # Validate the object inside the array
                        for subfield, subfield_type in item.items():
                            validate_schema_field(subfield, subfield_type)
                else:
                    # If it's an array of simple types, validate each item
                    for item in field_type:
                        if item not in ["string", "integer", "boolean"]:
                            raise ValueError(f"Invalid array type '{item}' in field '{field}'")
            elif field_type not in ["string", "integer", "boolean", "array", "object"]:
                raise ValueError(f"Invalid type '{field_type}' for field '{field}'")

        # Validate the schema fields
        try:
            for field, field_type in schema.items():
                validate_schema_field(field, field_type)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)

            contents = repo.get_contents("")
            folders = [content.path for content in contents if content.type == "dir"]
            
            # Check if the database folder exists
            if database_name not in folders:
                return Response({"error": "Database does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            # Define paths for schema and table
            schema_path = f"{database_name}/Schema/{table_name}.json"
            table_path = f"{database_name}/Tables/{table_name}.json"

            # Convert schema to JSON format
            schema_json = json.dumps(schema, indent=4)

            # Check if the schema file already exists
            try:
                repo.get_contents(schema_path)  # This will raise an exception if file does not exist
                return Response(
                    {"error": "Table schema already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except:
                # File does not exist, create schema and table files
                repo.create_file(
                    schema_path,
                    f"Created schema for table {table_name}",
                    schema_json
                )
                repo.create_file(
                    table_path,
                    f"Created table {table_name}",
                    "[]"  # Initialize table as an empty list
                )
                return Response(
                    {"message": "Table schema created successfully"},
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        """Rename a table schema and data in the repository"""
        database_name = request.data.get("database_name")
        old_table_name = request.data.get("old_table_name")
        new_table_name = request.data.get("new_table_name")

        if not database_name or not old_table_name or not new_table_name:
            return Response(
                {"error": "Database name, old table name, and new table name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)

            # Define the paths for the old and new table files
            old_schema_path = f"{database_name}/Schema/{old_table_name}.json"
            old_table_path = f"{database_name}/Tables/{old_table_name}.json"

            new_schema_path = f"{database_name}/Schema/{new_table_name}.json"
            new_table_path = f"{database_name}/Tables/{new_table_name}.json"

            # Check if the old table and schema exist
            try:
                old_schema_file = repo.get_contents(old_schema_path)
                old_table_file = repo.get_contents(old_table_path)
            except:
                return Response(
                    {"error": f"Table or schema '{old_table_name}' does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Read the content of the old files
            schema_content = old_schema_file.decoded_content.decode("utf-8")
            table_content = old_table_file.decoded_content.decode("utf-8")

            # Create the new schema and table files with the new name
            repo.create_file(new_schema_path, f"Renamed schema for table {old_table_name} to {new_table_name}", schema_content)
            repo.create_file(new_table_path, f"Renamed table {old_table_name} to {new_table_name}", table_content)

            # Delete the old schema and table files
            repo.delete_file(old_schema_file.path, f"Deleted old schema: {old_table_name}", old_schema_file.sha)
            repo.delete_file(old_table_file.path, f"Deleted old table: {old_table_name}", old_table_file.sha)

            return Response(
                {"message": f"Table renamed from '{old_table_name}' to '{new_table_name}' successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
