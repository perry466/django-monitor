from django.db import models
from django.contrib.auth.models import User

# 可选：扩展用户资料（目前不需要也可跳过）
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_regular_user = models.BooleanField(default=True)  # 标记普通用户

    def __str__(self):
        return self.user.username