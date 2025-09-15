# core/views.py
from itertools import count
from django import db
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import AgriculturalDataForm, SignUpForm, LoginForm, ProfileForm
from .models import AgriculturalData
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import os
from django.conf import settings
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count
import json



# Constants for model features
MODEL_FEATURES = [
    'Country', 
    'Crop', 
    'Year', 
    'Area_harvested_ha',
    'Rainfall_mm', 
    'Temperature_C', 
    'Policy_Flag',
    'Transport_Cost_USD', 
    'Demand_Supply_Gap',
    'Rainfall_Temp_interaction',
    'Price_to_Yield_ratio',
    'Production_tonnes',
    'log_Area_harvested_ha',
    'Demand_Supply_balance',
    'log_Transport_Cost_USD',
    'Price_USD_per_tonne',
    'Productivity_index',
    'log_Production_tonnes'
]


# Load the model and preprocessing pipeline
def load_model():
    model_path = os.path.join(settings.BASE_DIR, 'core', 'models', 'agricultural_model.pkl')
    return joblib.load(model_path)

model = load_model()
print(model.feature_names_in_)
@login_required
def dashboard(request):
    # Get user's prediction history
    user_data = AgriculturalData.objects.filter(user=request.user).order_by('-created_at')
    
    # Get summary statistics for the dashboard
    total_predictions = user_data.count()
    recent_predictions = user_data[:5]
    
    # Calculate 30-day statistics
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_data = user_data.filter(created_at__gte=thirty_days_ago)
    
    if recent_data.exists():
        avg_production = recent_data.aggregate(Avg('predicted_production'))['predicted_production__avg']
        avg_yield = recent_data.aggregate(Avg('predicted_yield'))['predicted_yield__avg']
        avg_price = recent_data.aggregate(Avg('predicted_price'))['predicted_price__avg']
    else:
        avg_production = avg_yield = avg_price = 0
    
    context = {
        'user_data': user_data,
        'total_predictions': total_predictions,
        'recent_predictions': recent_predictions,
        'avg_production': avg_production,
        'avg_yield': avg_yield,
        'avg_price': avg_price,
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def predict(request):
    if request.method == 'POST':
        form = AgriculturalDataForm(request.POST)
        if form.is_valid():
            # Save form data to database
            data = form.save(commit=False)
            data.user = request.user
            
            # Prepare input data
            input_data = {
                'Country': data.country,
                'Crop': data.crop,
                'Year': data.year,
                'Area_harvested_ha': data.area_harvested_ha,
                'Rainfall_mm': data.rainfall_mm,
                'Temperature_C': data.temperature_c,
                'Policy_Flag': data.policy_flag,
                'Transport_Cost_USD': data.transport_cost_usd,
                'Demand_Supply_Gap': data.demand_supply_gap,
                'Rainfall_Temp_interaction': data.rainfall_temp_interaction,
                'Price_to_Yield_ratio': data.price_to_yield_ratio,
                'Production_tonnes': data.production_tonnes,
                'log_Area_harvested_ha': data.log_area_harvested_ha,
                'Demand_Supply_balance': data.demand_supply_balance,
                'log_Transport_Cost_USD': data.log_transport_cost_usd,
                'Price_USD_per_tonne': data.price_usd_per_tonne,
                'Productivity_index': data.productivity_index,
                'log_Production_tonnes': data.log_production_tonnes
            }

            # Debug: Print the input data
            print("Input data before prediction:", input_data)
            
            # Convert Policy_Flag to numeric
            policy_flag_numeric = 1 if input_data['Policy_Flag'] == 'Subsidy' else 0
            
            # Direct prediction logic (mock example)
            predicted_production = (
                input_data['Area_harvested_ha'] * 
                (input_data['Rainfall_mm'] / 100) * 
                (input_data['Temperature_C'] / 20) * 
                (1 + policy_flag_numeric)  # Use the numeric value for policy flag
            )
            predicted_yield = predicted_production / input_data['Area_harvested_ha'] if input_data['Area_harvested_ha'] > 0 else 0
            predicted_price = input_data['Price_USD_per_tonne'] * (1 + input_data['Demand_Supply_Gap'] / 100)

            # Save predictions to the data object
            data.predicted_production = predicted_production
            data.predicted_yield = predicted_yield
            data.predicted_price = predicted_price
            
            data.save()
            
            # Prepare data for results page
            prediction_results = {
                'production': data.predicted_production,
                'yield': data.predicted_yield,
                'price': data.predicted_price,
                'input_data': {
                    'country': data.country,
                    'crop': data.crop,
                    'year': data.year,
                    'area': data.area_harvested_ha,
                }
            }
            
            # Store in session for results page
            request.session['prediction_results'] = prediction_results
            
            messages.success(request, 'Prediction successful!')
            return redirect('prediction_results', pk=data.id)
                
        else:
            messages.error(request, 'Form is not valid.')
    else:
        # Initialize form with default values if needed
        initial_data = {}
        if request.GET.get('crop'):
            initial_data['crop'] = request.GET.get('crop')
        form = AgriculturalDataForm(initial=initial_data)
    
    return render(request, 'core/predict.html', {
        'form': form,
        'model_features': MODEL_FEATURES
    })

@login_required
def prediction_results(request, pk):
    # Retrieve the prediction data
    prediction = get_object_or_404(AgriculturalData, pk=pk, user=request.user)
    
    # Get from session if available (for immediate display after prediction)
    results = request.session.get('prediction_results', None)
    
    if not results:
        # If not in session, create from database
        results = {
            'production': prediction.predicted_production,
            'yield': prediction.predicted_yield,
            'price': prediction.predicted_price,
            'input_data': {
                'country': prediction.country,
                'crop': prediction.crop,
                'year': prediction.year,
                'area': prediction.area_harvested_ha,
            }
        }
    
    context = {
        'prediction': prediction,
        'results': results,
    }
    
    # Clear the session data after displaying
    if 'prediction_results' in request.session:
        del request.session['prediction_results']
    
    return render(request, 'core/prediction_results.html', context)

@login_required
def delete_prediction(request, pk):
    prediction = get_object_or_404(AgriculturalData, pk=pk, user=request.user)
    if request.method == 'POST':
        prediction.delete()
        messages.success(request, 'Prediction deleted successfully.')
        return redirect('dashboard')
    return render(request, 'core/confirm_delete.html', {'prediction': prediction})

@login_required
def prediction_detail(request, pk):
    prediction = get_object_or_404(AgriculturalData, pk=pk, user=request.user)
    return render(request, 'core/prediction_detail.html', {'prediction': prediction})

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    # Get user statistics
    user_stats = {
        'total_predictions': AgriculturalData.objects.filter(user=request.user).count(),
        'last_prediction': AgriculturalData.objects.filter(user=request.user)
                            .order_by('-created_at').first(),
        'favorite_crop': AgriculturalData.objects.filter(user=request.user)
                            .values('crop').annotate(count=Count('crop'))
                            .order_by('-count').first(),
    }
    
    return render(request, 'core/profile.html', {
        'form': form,
        'user_stats': user_stats
    })

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            
            # Send welcome email (placeholder - implement email in production)
            # send_welcome_email(user.email)
            
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                
                # Redirect to next page if specified
                next_page = request.GET.get('next', 'dashboard')
                return redirect(next_page)
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def home(request):
    # Show featured crops or statistics for anonymous users
    if not request.user.is_authenticated:
        top_crops = AgriculturalData.objects.values('crop').annotate(
            count=db.models.Count('crop')
        ).order_by('-count')[:5]
        
        recent_predictions_count = AgriculturalData.objects.count()
        
        context = {
            'top_crops': top_crops,
            'recent_predictions_count': recent_predictions_count,
        }
        return render(request, 'core/home.html', context)
    
    # For logged in users, redirect to dashboard
    return redirect('dashboard')

# API Views for AJAX functionality
@login_required
@require_http_methods(["GET"])
def get_prediction_stats(request):
    # Get statistics for the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    user_data = AgriculturalData.objects.filter(
        user=request.user,
        created_at__gte=thirty_days_ago
    )
    
    stats = {
        'count': user_data.count(),
        'avg_production': user_data.aggregate(Avg('predicted_production'))['predicted_production__avg'],
        'avg_yield': user_data.aggregate(Avg('predicted_yield'))['predicted_yield__avg'],
        'avg_price': user_data.aggregate(Avg('predicted_price'))['predicted_price__avg'],
    }
    
    return JsonResponse(stats)

@login_required
def export_predictions(request, format='csv'):
    predictions = AgriculturalData.objects.filter(user=request.user)
    
    if format == 'csv':
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="agricultural_predictions.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Crop', 'Country', 'Year', 'Area Harvested (ha)', 
            'Rainfall (mm)', 'Temperature (C)', 'Policy Flag',
            'Transport Cost (USD)', 'Demand Supply Gap',
            'Predicted Production', 'Predicted Yield', 'Predicted Price',
            'Date Created'
        ])
        
        for pred in predictions:
            writer.writerow([
                pred.crop, pred.country, pred.year, pred.area_harvested_ha,
                pred.rainfall_mm, pred.temperature_c, pred.policy_flag,
                pred.transport_cost_usd, pred.demand_supply_gap,
                pred.predicted_production, pred.predicted_yield, pred.predicted_price,
                pred.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        return response
    
    elif format == 'json':
        data = list(predictions.values(
            'crop', 'country', 'year', 'area_harvested_ha',
            'rainfall_mm', 'temperature_c', 'policy_flag',
            'transport_cost_usd', 'demand_supply_gap',
            'predicted_production', 'predicted_yield', 'predicted_price',
            'created_at'
        ))
        return JsonResponse(data, safe=False)
    
    else:
        messages.error(request, 'Invalid export format requested')
        return redirect('dashboard')

def about(request):
    return render(request, 'core/about.html')

def documentation(request):
    return render(request, 'core/documentation.html')

def handler404(request, exception):
    return render(request, 'core/404.html', status=404)

def handler500(request):
    return render(request, 'core/500.html', status=500)