import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer, UserSerializer as DjoserUserSerializer

from foodgram.models import Ingredient, Recipe, RecipeIngredients, Tag, Favorites


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='image.' + ext)

        return super().to_internal_value(data)


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredients
        fields = 'ingredient', 'amount'


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientSerializer(read_only=True, many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        exclude = 'pub_date',

    def to_representation(self, instance):
        recipe_data = super().to_representation(instance)
        recipe_data.pop('favorites_count')
        return recipe_data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorites
        fields = 'recipe',

    def to_representation(self, instance):
        recipe_data = super().to_representation(instance)
        return recipe_data


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        fields = DjoserUserCreateSerializer.Meta.fields + (
            'username', 'first_name', 'last_name'
        )


class UserSerializer(DjoserUserSerializer):
    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'username', 'first_name', 'last_name', 'avatar'
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)
