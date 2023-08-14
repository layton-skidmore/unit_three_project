from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django import forms
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Review, Album
from decouple import config
import boto3
import os
from botocore.exceptions import NoCredentialsError


# Create your views here.
def home(request):
  return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')

def profile_index(request):
    albums = Album.objects.all()
    return render(request, 'profile/index.html', {'albums' : albums })

class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['name', 'artist_name', 'album_cover']


class NewAlbumView(CreateView):
    form_class = AlbumForm
    template_name = 'main_app/new_album.html'
    success_url = '/index/'

    def form_valid(self, form):
        form.instance.user = self.request.user

        album = form.save(commit=False)

        if 'album_cover' in self.request.FILES:
            album_cover = self.request.FILES['album_cover']
            aws_access_key_id = config('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY')
            s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
            try:
                s3.upload_fileobj(album_cover, config('S3_BUCKET'), album_cover.name)
                album.album_cover = f"{config('S3_BASE_URL')}{config('S3_BUCKET')}/{album_cover.name}"
            except NoCredentialsError:
                print("Credentials not available")

        album.save()
        return super().form_valid(form)

     
def signup(request):
  error_message = ''
  if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
    form = UserCreationForm(request.POST)
    if form.is_valid():
      # This will add the user to the database
      user = form.save()
      # This is how we log a user in via code
      login(request, user)
      return redirect('index')
    else:
      error_message = 'Invalid sign up - try again'
  # A bad POST or a GET request, so render signup.html with an empty form
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)