import sys
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .query_solver import QuerySolver
from .db_manager import DBManager


class QuerySolverView(APIView):
    def __init__(self):
        super().__init__()
        self.query_solver = QuerySolver()

    def post(self, request):
        try:
            prompt = request.data.get('prompt')
            file_paths = request.data.get('file_paths', [])
            
            if not prompt:
                return Response(
                    {"error": "Prompt is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = QuerySolver().solve_query(prompt, file_paths=file_paths)
            # result is a json object
            
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
