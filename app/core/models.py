from django.db import models
from django.contrib.auth.models import User
import numpy as np
from django.db.models import F, ExpressionWrapper, FloatField

class AgriculturalData(models.Model):
    # Basic Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    crop = models.CharField(max_length=100)
    year = models.IntegerField()
    area_harvested_ha = models.FloatField()
    production_tonnes = models.FloatField()  # Added missing field
    rainfall_mm = models.FloatField()
    temperature_c = models.FloatField()
    price_usd_per_tonne = models.FloatField()  # Added missing field
    policy_flag = models.CharField(max_length=50)
    transport_cost_usd = models.FloatField()
    demand_supply_gap = models.FloatField()
    productivity_index = models.FloatField(default=0)  # Added missing field
    
    # Predicted Values
    predicted_production = models.FloatField(null=True, blank=True)
    predicted_yield = models.FloatField(null=True, blank=True)
    predicted_price = models.FloatField(null=True, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Derived Fields as Properties
    @property
    def rainfall_temp_interaction(self):
        return self.rainfall_mm * self.temperature_c
    
    @property
    def price_to_yield_ratio(self):
        if self.area_harvested_ha > 0:
            return self.price_usd_per_tonne / (self.production_tonnes / self.area_harvested_ha)
        return 0
    
    @property
    def demand_supply_balance(self):
        if self.production_tonnes > 0:
            return self.demand_supply_gap / self.production_tonnes
        return 0
    
    @property
    def log_production_tonnes(self):
        return np.log(self.production_tonnes) if self.production_tonnes > 0 else 0
    
    @property
    def log_area_harvested_ha(self):
        return np.log(self.area_harvested_ha) if self.area_harvested_ha > 0 else 0
    
    @property
    def log_transport_cost_usd(self):
        return np.log(self.transport_cost_usd) if self.transport_cost_usd > 0 else 0
    
    def __str__(self):
        return f"{self.crop} in {self.country} ({self.year})"

    class Meta:
        verbose_name_plural = "Agricultural Data"
        ordering = ['-year', 'country']