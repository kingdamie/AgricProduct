# agriproduct/urls.py
from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('documentation/', views.documentation, name='documentation'),
    
    # Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # User profile
    path('profile/', views.profile, name='profile'),
    
    # Prediction functionality
    path('dashboard/', views.dashboard, name='dashboard'),
    path('predict/', views.predict, name='predict'),
    path('predict/results/<int:pk>/', views.prediction_results, name='prediction_results'),
    path('predict/<int:pk>/', views.prediction_detail, name='prediction_detail'),
    path('predict/<int:pk>/delete/', views.delete_prediction, name='delete_prediction'),
    
    # Data export
    path('export/<int:pk>/<str:format>/', views.export_predictions, name='export_prediction'),
    path('export/all/<str:format>/', views.export_predictions, name='export_predictions'),
    
    # API endpoints
    path('api/stats/', views.get_prediction_stats, name='prediction_stats'),
]

# Error handlers
handler404 = views.handler404
handler500 = views.handler500