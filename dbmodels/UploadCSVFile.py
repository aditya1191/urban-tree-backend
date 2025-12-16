from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
import pandas as pd
from sqlalchemy import create_engine
from django.contrib.auth import authenticate
import os

# Import for basic input cleaning


class UploadCSVFile(APIView):
    parser_classes = [FileUploadParser]

    def post(self, request):
        # 1. AUTHENTICATION & INPUT SANITATION FOR CREDENTIALS
        username_raw = request.POST.get("name")
        password_raw = request.POST.get("password")

        # Simple sanitization on username to remove leading/trailing whitespace and limit chars
        username = username_raw.strip() if username_raw else None
        password = password_raw.strip() if password_raw else None

        # Basic check to ensure required fields were sent
        if not username or not password:
            return Response(
                {"error": "Missing username or password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # User is authenticated, proceed with file processing
        csv_file = request.FILES.get("file")

        if not csv_file:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file type
        if not csv_file.name.endswith(".csv"):
            return Response(
                {"error": "File is not CSV type"}, status=status.HTTP_400_BAD_REQUEST
            )

        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://urbantree:urbantree@localhost:5432/urbantree",
        )

        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

        # 2. DATA FRAME READING, CLEANING, AND SANITATION

        # Use a context manager to ensure the file handle is closed
        try:
            # Read CSV with specified parameters
            df = pd.read_csv(
                csv_file,
                delimiter=",",
                skiprows=29,
                header=0,
                dtype=str,
                # Add encoding handling for robustness
                encoding="utf-8",
            )
        except Exception as e:
            # Catch errors during file reading (e.g., malformed CSV)
            return Response(
                {"error": f"Error reading CSV file: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Data Cleaning and Missing Value Handling
        df.dropna(axis=1, how="all", inplace=True)
        # Using a specific non-null sentinel value for missing data
        df.fillna("NULL_MISSING", inplace=True)

        # 3. COLUMN RENAMING AND VALIDATION (CRITICAL FOR DB WRITE)

        # Ensure the DataFrame has enough columns for the intended rename
        if len(df.columns) < 11:
            return Response(
                {
                    "error": f"CSV has fewer than 11 columns after skipping rows (found {len(df.columns)})"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        df_str = df.astype(str)
        df_str = df_str.drop(df.columns[[0]], axis=1)  # Drop the first column

        # Define expected clean column names for the database
        new_columns = [
            "Timestamp_Raw",
            "Timestamp",
            "Temperature",
            "Pressure",
            "Humidity",
            "Dendro",
            "Sapflow",
            "SF_maxD",
            "SF_Signal",
            "SF_Noise",
            "Dendro_Dup",
        ]

        # Assign clean column names
        df_str.columns = new_columns
        df_str = df_str.drop(
            df_str.index[0]
        )  # Drop the original header row/first data row

        # 4. DATABASE WRITE
        db_url = "postgresql+psycopg2://urbantree:urbantree@127.0.0.1:5432/urbantree"
        engine = create_engine(db_url)

        try:
            # Use 'if_exists' to control behavior (append or replace)
            # Use 'index=False' to prevent writing the Pandas index as a column
            df_str.to_sql("tree_data", con=engine, if_exists="append", index=False)
            return Response(
                {"message": "CSV uploaded successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            # Catch database write errors
            return Response(
                {"error": f"Database write failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
