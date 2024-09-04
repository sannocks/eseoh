from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileUpdateForm

@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile_update')  # Redirect back to profile page after successful save
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'users/profile_update.html', {'form': form})


@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')