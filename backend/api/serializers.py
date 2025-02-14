from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    MIN_VALUE, Ingredient, Recipe, RecipeIngredients, Tag, Subscribe
)


User = get_user_model()

REQUIRED_FIELD = 'Обязательное поле.'

IMAGE_REQUIRED_FIELD = {'image': 'Обязательное поле'}

INGREDIENTS_NOT_REPEAT = 'Ингредиенты не должны повторяться.'

NOT_EXIST_INGREDIENT = 'Ингредиента с id={} не существует.'

TAGS_NOT_REPEAT = 'Тэги не должны повторяться.'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = (*DjoserUserSerializer.Meta.fields, 'avatar', 'is_subscribed')

    def get_is_subscribed(self, subscribing):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and Subscribe.objects.filter(
                user=request.user, subscribing=subscribing
            ).exists()
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeBaseSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'cooking_time', 'author', 'tags',
            'image', 'is_favorited', 'is_in_shopping_cart'
        )


class ReadRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('amount',)


class ReadRecipeSerializer(RecipeBaseSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ReadRecipeIngredientSerializer(
        many=True, read_only=True, source='recipe_ingredients'
    )

    class Meta(RecipeBaseSerializer.Meta):
        fields = (
            *RecipeBaseSerializer.Meta.fields,
            'id', 'tags', 'ingredients'
        )
        read_only_fields = 'name', 'text', 'cooking_time', 'image', 'id'

    def _get_is_related(self, recipe, related_name):
        request = self.context.get('request')
        return request and request.user.is_authenticated and (
            getattr(recipe, related_name)
            .filter(user=request.user)
            .exists()
        )

    def get_is_favorited(self, recipe):
        return self._get_is_related(recipe, 'favorite_recipe')

    def get_is_in_shopping_cart(self, recipe):
        return self._get_is_related(recipe, 'shoppingcart_recipe')


class WriteRecipeIngredientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=[MinValueValidator(MIN_VALUE)]
    )

    def validate_id(self, id):
        if not Ingredient.objects.filter(id=id).exists():
            raise serializers.ValidationError(NOT_EXIST_INGREDIENT.format(id))
        return id


class WriteRecipeSerializer(RecipeBaseSerializer):
    ingredients = WriteRecipeIngredientSerializer(many=True, required=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta(RecipeBaseSerializer.Meta):
        fields = (*RecipeBaseSerializer.Meta.fields, 'ingredients', 'image')

    def validate(self, data):
        if self.instance is None and not data.get('image'):
            raise serializers.ValidationError(IMAGE_REQUIRED_FIELD)
        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(REQUIRED_FIELD)
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(INGREDIENTS_NOT_REPEAT)
        return ingredients

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(TAGS_NOT_REPEAT)
        return tags

    @transaction.atomic
    def _get_new_recipe(
        self, recipe, ingredients_data, tags_data, new_recipe_data=None
    ):
        if new_recipe_data:
            recipe.ingredients.clear()
            super().update(recipe, new_recipe_data)
        else:
            recipe = super().create(recipe)
        recipe.tags.set(tags_data)
        RecipeIngredients.objects.bulk_create(
            RecipeIngredients(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients_data)
        return recipe

    def create(self, recipe_data):
        return self._get_new_recipe(
            recipe=recipe_data,
            ingredients_data=recipe_data.pop('ingredients'),
            tags_data=recipe_data.pop('tags')
        )

    def update(self, old_recipe, new_recipe_data):
        return self._get_new_recipe(
            recipe=old_recipe,
            ingredients_data=new_recipe_data.pop('ingredients'),
            tags_data=new_recipe_data.pop('tags'),
            new_recipe_data=new_recipe_data
        )

    def to_representation(self, recipe):
        return ReadRecipeSerializer(recipe, context=self.context).data
