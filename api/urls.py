from django.urls import path
from .views import QuerySolverView

urlpatterns = [
    path('query_solving/', QuerySolverView.as_view(), name='query_solving'),
] 
