import json
import os
from github import Github
from rest_framework.response import Response
from rest_framework import status, views

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")

class TableSchema(views.APIView):
    def post(self, request, *args, **kwargs):
        """Create or update a table schema in GitHub storage"""
        database_name = request.data.get("database_name")
        table_name = request.data.get("table_name")
        new_schema = request.data.get("schema")

        if not database_name or not table_name or not new_schema:
            return Response(
                {"error": "Database name, table name, and schema are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate the schema (Ensure it's a valid dictionary)
        if not isinstance(new_schema, dict):
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
            for field, field_type in new_schema.items():
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
            schema_json = json.dumps(new_schema, indent=4)

            try:
                # Check if the schema file exists
                schema_file = repo.get_contents(schema_path)
                
                # Check if the table has data before allowing schema change
                try:
                    table_file = repo.get_contents(table_path)
                    table_data = json.loads(table_file.decoded_content.decode("utf-8"))

                    # Prevent schema change if table has data
                    if table_data and isinstance(table_data, list) and len(table_data) > 0:
                        return Response(
                            {"error": "Table has data, schema cannot be changed."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except:
                    # Table does not exist or is empty, allow schema change
                    pass
                
                # Delete old schema before creating the new one
                repo.delete_file(
                    schema_path,
                    f"Removed old schema for table {table_name}",
                    schema_file.sha
                )

                # Create the new schema
                repo.create_file(
                    schema_path,
                    f"Created new schema for table {table_name}",
                    schema_json
                )
                
                return Response(
                    {"message": "Table schema updated successfully"},
                    status=status.HTTP_200_OK
                )
            except:
                
                return Response(
                    {"error": "Table schema doesnot exist"},
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        database_name = request.data.get("database_name")  # Use query params for GET requests
        table_name = request.data.get("table_name")  # Use query params for GET requests

        if not database_name or not table_name:
            return Response(
                {"error": "Database name and table name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)

            contents = repo.get_contents("")  # Get contents at the root level
            folders = [content.path for content in contents if content.type == "dir"]
            
            # Check if the database folder exists
            if database_name not in folders:
                return Response({"error": "Database does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            # Define the path for the schema file
            schema_path = f"{database_name}/Schema/{table_name}.json"
            
            try:
                # Attempt to get the schema file
                schema_file = repo.get_contents(schema_path)
                schema = json.loads(schema_file.decoded_content.decode("utf-8"))

                # Return the schema
                return Response({"schema": schema}, status=status.HTTP_200_OK)

            except:
                # If the schema file does not exist, return an error
                return Response(
                    {"error": "Table schema does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

