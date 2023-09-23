from django.shortcuts import render, redirect
from .forms import CustomUserSignupForm
from django.contrib.auth import logout

def signup(request):
    if request.method == 'POST':
        form = CustomUserSignupForm(request.POST)
        if form.is_valid():
            form.save()
            # Here you can also log the user in or send a confirmation email if needed
            return redirect('/')  # Redirect to a success page or login page
    else:
        form = CustomUserSignupForm()
    return render(request, 'signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/')