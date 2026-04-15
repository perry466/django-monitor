from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"注册成功！欢迎 {user.username}")
            return redirect('/')                    # 注册成功直接进入首页
        else:
            # 注册失败时，给出更清晰的提示
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}：{error}")

    # 渲染模板时传递表单（这样可以保留用户输入）
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"欢迎回来，{user.username}！")
            return redirect('/')
        else:
            messages.error(request, "用户名或密码错误，请重试")

    return render(request, 'accounts/login.html')


@login_required(login_url='/login/')
def logout_view(request):
    logout(request)
    messages.info(request, "您已成功登出")
    return redirect('/login/')