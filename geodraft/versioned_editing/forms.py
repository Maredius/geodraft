"""
Django forms for versioned editing.
"""
from django import forms
from django.contrib.auth import get_user_model
from geonode.groups.models import GroupProfile
from .models import EditBranch, MergeRequest, UserRole

User = get_user_model()


class CreateBranchForm(forms.ModelForm):
    """Form for creating a new editing branch"""
    
    class Meta:
        model = EditBranch
        fields = ['name', 'description', 'parent_branch', 'group']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Branch name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description'
            }),
            'parent_branch': forms.Select(attrs={
                'class': 'form-control'
            }),
            'group': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class CreateMergeRequestForm(forms.ModelForm):
    """Form for creating a merge request"""
    
    class Meta:
        model = MergeRequest
        fields = ['source_branch', 'target_branch', 'title', 'description']
        widgets = {
            'source_branch': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_branch': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Merge request title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your changes'
            }),
        }


class AssignRoleForm(forms.Form):
    """Form for assigning roles to users in groups"""
    
    group = forms.ModelChoiceField(
        queryset=GroupProfile.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Group"
    )
    
    role = forms.ChoiceField(
        choices=UserRole.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Role"
    )
    
    can_approve_merges = forms.BooleanField(
        required=False,
        initial=False,
        label="Can approve merge requests",
        help_text="Automatically enabled for validators and admins"
    )
    
    can_manage_branches = forms.BooleanField(
        required=False,
        initial=True,
        label="Can manage branches",
        help_text="Can create and delete branches"
    )


class CreateGroupForm(forms.ModelForm):
    """Form for creating a new group"""
    
    class Meta:
        model = GroupProfile
        fields = ['title', 'description', 'access']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Group name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Group description'
            }),
            'access': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
