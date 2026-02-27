from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm


class UserProfileView(DetailView):
    model = CustomUser
    template_name = 'users/user_profile.html' # Путь к шаблону
    context_object_name = 'user_profile' # Имя переменной в шаблоне

    def get_object(self, queryset=None):
        # Получаем пользователя по первичному ключу из URL
        return get_object_or_404(CustomUser, pk=self.kwargs['pk'])

class UserProfileEditView(LoginRequiredMixin, UpdateView): # Требует авторизации
    model = CustomUser
    form_class = CustomUserChangeForm # Используем кастомную форму для изменения
    template_name = 'users/user_profile_edit.html'
    success_url = reverse_lazy('users:user_profile_edit') # Возвращаемся на страницу редактирования, если нет pk

    def get_object(self, queryset=None):
        # Позволяем редактировать только свой профиль
        return self.request.user

    def get_success_url(self):
        # Перенаправляем на профиль отредактированного пользователя
        return reverse_lazy('users:user_profile', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
        # Добавляем сообщение об успехе
        messages.success(self.request, 'Ваш профиль успешно обновлен!')
        return super().form_valid(form)