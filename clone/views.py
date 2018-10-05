from django.shortcuts import render,redirect
from django.http import HttpResponse,Http404
from .models import Image,Profile,Comments
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from .forms import ImageForm,EditProfileForm,RegistrationForm,CommentsForm
from django.contrib.sites.shortcuts import get_current_site
from .emails import activation_email
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .tokens import activation_token

import datetime as dt


@login_required(login_url='/login')
def instagram(request):
    images = Image.objects.all()
    return render(request,'instagram.html',{"images":images})




def profile(request):
    profile = User.objects.get(username=request.user)
    try:
        profile_details = Profile.get_by_id(profile.id)
    except:
        profile_details = Profile.filter_by_id(profile.id)
    images = Image.get_profile_images(profile.id)
    title = f'@{profile.username} Instagram photos and videos'

    return render(request, 'profile/profile.html', {'title':title, 'profile':profile, 'profile_details':profile_details, 'images':images})

@login_required(login_url='/login')
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES)
        if form.is_valid():
            edit = form.save(commit=False)
            edit.user = request.user
            edit.save()
            return redirect('edit_profile')
    else:
        form = EditProfileForm()

    return render(request, 'profile/edit_profile.html', {'form':form})

@login_required(login_url='/login')
def upload_image(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.profile = request.user
            upload.save()
            return redirect('profile')
    else:
        form = ImageForm()

    return render(request, 'profile/upload_image.html', {'form': form})



def register(request):
    if request.user.is_authenticated():
        return redirect('instagram')
    else:
        if request.method == 'POST':
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                current_site = get_current_site(request)
                to_email = form.cleaned_data.get('email')
                activation_email(user, current_site, to_email)
                return HttpResponse('Confirm your email address to complete registration')
        else:
            form = RegistrationForm()
            return render(request, 'registration/signup.html',{'form':form})

def search_profile(request):
    if 'search' in request.GET and request.GET['search']:
        search_term = request.GET.get('search')
        profiles = Profile.search_profile(search_term)
        message = f'{search_term}'

        return render(request, 'search.html',{'message':message, 'profiles':profiles})
    else:
        message = 'Enter term to search'
        return render(request, 'search.html', {'message':message})


@login_required(login_url='/login')
def single_image(request, image_id):
    images = Image.get_image_id(image_id)
    comments = Comments.get_comments_by_images(image_id)

    if request.method == 'POST':
        form = CommentsForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.image = images
            comment.user = request.user
            comment.save()
            return redirect('single_image', image_id=image_id)
    else:
        form = CommentsForm()

    return render(request, 'single_image.html', {'images': images, 'form': form, 'comments': comments})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        return HttpResponse('Thank you for confirming email. Now login to your account')
    else:
        return HttpResponse('Activation link is invalid')