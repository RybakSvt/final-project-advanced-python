from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _



class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        _("username"),
        max_length=50,
        unique=True,
        error_messages={
            "unique": _("A user with that username already exists."),
        }
    )

    first_name = models.CharField(
        _("first name"),
        max_length=40,
        validators=[MinLengthValidator(2)],
    )
    last_name = models.CharField(
        _("last name"),
        max_length=40,
        validators=[MinLengthValidator(2)],
    )

    email = models.EmailField(
        _("email address"),
        max_length=150,
        unique=True
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(
        db_column="registered", auto_now_add=True
    )
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted = models.BooleanField(default=False)



    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
        "first_name",
        "last_name",
    ]

    objects = UserManager()

    def __str__(self):
        return self.username

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"


class Role(models.Model):
    name = models.CharField(
        _("Name"),
        max_length=50,
        unique=True,
        help_text=_("Unique role identifier (e.g., 'host', 'guest', 'moderator')")
    )

    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("What this role allows users to do")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ['name']



class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("User")
    )

    phone = models.CharField(
        _("Phone number"),
        max_length=20,
        blank=True
    )

    avatar = models.ImageField(
        _("Avatar"),
        upload_to='avatars/',
        null=True,
        blank=True
    )

    bio = models.TextField(
        _("About me"),
        blank=True
    )

    roles = models.ManyToManyField(
        'Role',
        blank=True,
        related_name='profiles',
        verbose_name=_("Roles")
    )

    # Рейтинги пользователя по трём категориям (TOP/OK/POOR)
    satisfaction_total_score = models.FloatField(
        _("Satisfaction total score"),
        default=0.0,
        help_text=_("Sum of points for satisfaction (TOP=100, OK=50, POOR=0)")
    )
    satisfaction_votes_count = models.IntegerField(
        _("Satisfaction votes count"),
        default=0,
        help_text=_("Total number of satisfaction ratings received")
    )
    satisfaction_top_count = models.IntegerField(
        _("Satisfaction TOP count"),
        default=0,
        help_text=_("Number of TOP ratings for satisfaction")
    )
    satisfaction_ok_count = models.IntegerField(
        _("Satisfaction OK count"),
        default=0,
        help_text=_("Number of OK ratings for satisfaction")
    )
    satisfaction_poor_count = models.IntegerField(
        _("Satisfaction POOR count"),
        default=0,
        help_text=_("Number of POOR ratings for satisfaction")
    )

    friendliness_total_score = models.FloatField(
        _("Friendliness total score"),
        default=0.0,
        help_text=_("Sum of points for friendliness (TOP=100, OK=50, POOR=0)")
    )
    friendliness_votes_count = models.IntegerField(
        _("Friendliness votes count"),
        default=0,
        help_text=_("Total number of friendliness ratings received")
    )
    friendliness_top_count = models.IntegerField(
        _("Friendliness TOP count"),
        default=0,
        help_text=_("Number of TOP ratings for friendliness")
    )
    friendliness_ok_count = models.IntegerField(
        _("Friendliness OK count"),
        default=0,
        help_text=_("Number of OK ratings for friendliness")
    )
    friendliness_poor_count = models.IntegerField(
        _("Friendliness POOR count"),
        default=0,
        help_text=_("Number of POOR ratings for friendliness")
    )

    reliability_total_score = models.FloatField(
        _("Reliability total score"),
        default=0.0,
        help_text=_("Sum of points for reliability (TOP=100, OK=50, POOR=0)")
    )
    reliability_votes_count = models.IntegerField(
        _("Reliability votes count"),
        default=0,
        help_text=_("Total number of reliability ratings received")
    )
    reliability_top_count = models.IntegerField(
        _("Reliability TOP count"),
        default=0,
        help_text=_("Number of TOP ratings for reliability")
    )
    reliability_ok_count = models.IntegerField(
        _("Reliability OK count"),
        default=0,
        help_text=_("Number of OK ratings for reliability")
    )
    reliability_poor_count = models.IntegerField(
        _("Reliability POOR count"),
        default=0,
        help_text=_("Number of POOR ratings for reliability")
    )


    created_at = models.DateTimeField(
        _("Created at"),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Updated at"),
        auto_now=True
    )


    def __str__(self):
        return f"Profile of {self.user.username}"

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
        ordering = ['-created_at']