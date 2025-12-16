from django.http import HttpResponse, JsonResponse
from django.conf import settings # Import Django settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sqlalchemy import create_engine, text # Import text for parameterized queries
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TreeData(APIView):
    """
    Retrieves tree sensor data from the PostgreSQL database and returns it as JSON.
    """
    
    # 1. Use environment variables/settings for DB connection (Security Best Practice)
    # The actual DB URL should be configured in settings.py or environment variables.
    DB_URL = settings.DATABASE_URL_READ_ONLY 
    
    # Define a default limit to prevent accidental massive table dumps
    DEFAULT_LIMIT = 500

    def get(self, request):
        if not self.DB_URL:
            logger.error("Database URL is not configured.")
            return Response(
                {"error": "Database service is unavailable"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # 2. Input Sanitation and Query Parameterization
        # Safely get the 'limit' parameter from the request, falling back to DEFAULT_LIMIT
        try:
            limit = int(request.query_params.get('limit', self.DEFAULT_LIMIT))
            if limit < 1 or limit > 10000:  # Enforce reasonable limits
                limit = self.DEFAULT_LIMIT
        except ValueError:
            limit = self.DEFAULT_LIMIT
            
        # 3. Execution and Error Handling
        try:
            engine = create_engine(self.DB_URL)
            
            # Use text() for explicit SQL statement; LIMIT is parameterized safely
            sql_query = text(f"SELECT * FROM tree_data LIMIT :limit")
            
            # Pass parameters separately to the execution method
            df = pd.read_sql_query(sql_query, engine, params={'limit': limit})
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return Response(
                {"error": "Failed to retrieve data from database."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4. Data Transformation (Cleaning unnecessary columns)
        # Ensure 'tree_data' table structure is known, as relying on index (0, 1) is fragile.
        # Assuming the first two columns are unnamed index columns we want to drop.
        if df.shape[1] >= 2:
            df_modified = df.drop(df.columns[[0, 1]], axis=1)
        else:
            df_modified = df
            
        # 5. Response Formatting
        # Use DRF's Response or Django's JsonResponse for proper header handling
        return JsonResponse(
            df_modified.to_dict(orient='records'),
            safe=False,
            status=status.HTTP_200_OK
        )