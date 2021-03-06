""" Forms for swiftbrowser.browser """
# -*- coding: utf-8 -*-
from django import forms


class CreateContainerForm(forms.Form):
    """ Simple form for container creation """
    containername = forms.CharField(max_length=100)


class AddACLForm(forms.Form):
    """ Form for ACLs """
    username = forms.CharField(max_length=100)
    right = forms.ChoiceField(choices=((0,'read'),(1,'write')), widget=forms.RadioSelect())

class PseudoFolderForm(forms.Form):
    """ Upload form """
    foldername = forms.CharField(max_length=100)


class LoginForm(forms.Form):
    """ Login form """
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
