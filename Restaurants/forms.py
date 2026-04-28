from django import forms
from .models import TableSize, SeatingType, Restaurant, Table, SpecialDay, Review


# -------------------------------
# TableSize Form
# -------------------------------
class TableSizeForm(forms.ModelForm):
    class Meta:
        model = TableSize
        exclude = ['restaurant']

    def __init__(self, *args, **kwargs):
        self.restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        capacity = cleaned_data.get('capacity')
        size = cleaned_data.get('size')
        if capacity and size and self.restaurant:
            from django.db.models import Q
            if TableSize.objects.filter(capacity=capacity, size=size).filter(Q(restaurant__isnull=True) | Q(restaurant=self.restaurant)).exists():
                raise forms.ValidationError(f"A table size '{size}' with {capacity} seats already exists globally or for this restaurant.")
        return cleaned_data


# -------------------------------
# SeatingType Form
# -------------------------------
class SeatingTypeForm(forms.ModelForm):
    class Meta:
        model = SeatingType
        exclude = ['restaurant']

    def __init__(self, *args, **kwargs):
        self.restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and self.restaurant:
            from django.db.models import Q
            if SeatingType.objects.filter(name__iexact=name).filter(Q(restaurant__isnull=True) | Q(restaurant=self.restaurant)).exists():
                raise forms.ValidationError(f"A seating type named '{name}' already exists globally or for this restaurant.")
        return name


# -------------------------------
# Restaurant Form
# -------------------------------
class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        exclude = [
            'created_at',   # auto
            'is_approved',  # admin-controlled
        ]

        widgets = {
            'about_restaurant': forms.Textarea(attrs={'rows': 3}),
            'seating_types': forms.CheckboxSelectMultiple(),
            'default_opening_hour': forms.TimeInput(attrs={'type': 'time'}),
            'default_closing_hour': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only these two should be optional if they were somehow required
        self.fields['fb_link'].required = False
        self.fields['website_link'].required = False


# -------------------------------
# Table Form
# -------------------------------
class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        exclude = ['restaurant', 'is_available', 'is_combinable']  # restaurant set in logic, others deleted

    def __init__(self, *args, **kwargs):
        self.restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)

        # Limit dropdowns dynamically (important UX improvement)
        if self.restaurant:
            from django.db.models import Q
            self.fields['table_size'].queryset = TableSize.objects.filter(Q(restaurant__isnull=True) | Q(restaurant=self.restaurant))
            self.fields['seating_type'].queryset = SeatingType.objects.filter(Q(restaurant__isnull=True) | Q(restaurant=self.restaurant))

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and self.restaurant:
            if Table.objects.filter(name=name, restaurant=self.restaurant).exists():
                raise forms.ValidationError(f"A table with the name '{name}' already exists.")
        return name


# -------------------------------
# SpecialDay Form
# -------------------------------
class SpecialDayForm(forms.ModelForm):
    class Meta:
        model = SpecialDay
        exclude = ['restaurant']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'adjusted_opening_hour': forms.TimeInput(attrs={'type': 'time'}),
            'adjusted_closing_hour': forms.TimeInput(attrs={'type': 'time'}),
        }


# -------------------------------
# WeeklySchedule Form
# -------------------------------
from .models import WeeklySchedule

class WeeklyScheduleForm(forms.ModelForm):
    class Meta:
        model = WeeklySchedule
        exclude = ['restaurant']

        widgets = {
            'opening_hour': forms.TimeInput(attrs={'type': 'time'}),
            'closing_hour': forms.TimeInput(attrs={'type': 'time'}),
        }


# -------------------------------
# Review Form
# -------------------------------
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        exclude = ['restaurant', 'user', 'created_at']  # set in view

        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': '1',
                'max': '5',
                'class': 'custom-select'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Write your review...'
            }),
        }