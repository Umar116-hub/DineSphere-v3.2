from django import forms
from .models import TableSize, SeatingType, Restaurant, Table, SpecialDay, Review


# -------------------------------
# TableSize Form
# -------------------------------
class TableSizeForm(forms.ModelForm):
    class Meta:
        model = TableSize
        # Exclude advanced pricing fields from normal UI
        fields = '__all__'


# -------------------------------
# SeatingType Form
# -------------------------------
class SeatingTypeForm(forms.ModelForm):
    class Meta:
        model = SeatingType
        fields = ['name']


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
            'seating_types': forms.CheckboxSelectMultiple(),  # better UI
        }


# -------------------------------
# Table Form
# -------------------------------
class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        exclude = ['restaurant', 'is_available', 'is_combinable']  # restaurant set in logic, others deleted

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)

        # Limit dropdowns dynamically (important UX improvement)
        if restaurant:
            self.fields['table_size'].queryset = TableSize.objects.all()
            self.fields['seating_type'].queryset = SeatingType.objects.all()


# -------------------------------
# SpecialDay Form
# -------------------------------
class SpecialDayForm(forms.ModelForm):
    class Meta:
        model = SpecialDay
        exclude = ['restaurant']  # usually set from context

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
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