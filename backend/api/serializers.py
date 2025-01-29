from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer

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


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredients
        fields = 'ingredient', 'amount'


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Recipe
        exclude = 'pub_date',


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorites
        fields = 'recipe',

    def to_representation(self, instance):
        recipe_data = super().to_representation(instance)
        return recipe_data


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = (
#             'id', 'username', 'email', 'first_name', 'last_name', 'avatar'
#         )

#     def to_representation(self, instance):
#         # Получаем стандартное представление
#         representation = super().to_representation(instance)
#         # Если метод запроса не POST, убираем 'avatar'
#         if self.context.get('request') and self.context['request'].method == 'POST':
#             representation.pop('avatar', None)
#         return representation


class UserSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        fields = DjoserUserCreateSerializer.Meta.fields + ('first_name', 'last_name')


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('avatar',)
