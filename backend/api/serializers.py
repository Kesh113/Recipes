from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    MIN_VALUE_AMOUNT, Ingredient, Recipe, RecipeIngredients, Tag, Subscribe
)


User = get_user_model()

REQUIRED_FIELD = 'Обязательное поле.'

NOT_EMPTY_FIELD = 'Поле не должно быть пустым'

ITEMS_NOT_REPEAT = 'Объекты не должны повторяться: {}'


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


class ReadRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ReadRecipeIngredientSerializer(
        many=True, read_only=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'name', 'text', 'cooking_time', 'author',
            'tags', 'image', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = fields

    def _get_is_related(self, recipe, related_name):
        request = self.context.get('request')
        return request and request.user.is_authenticated and (
            getattr(recipe, related_name)
            .filter(user=request.user)
            .exists()
        )

    def get_is_favorited(self, recipe):
        return self._get_is_related(recipe, 'favorites')

    def get_is_in_shopping_cart(self, recipe):
        return self._get_is_related(recipe, 'shoppingcarts')


class WriteRecipeIngredientSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    amount = serializers.IntegerField(min_value=MIN_VALUE_AMOUNT)


class WriteRecipeSerializer(serializers.ModelSerializer):
    ingredients = WriteRecipeIngredientSerializer(many=True, required=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = 'name', 'text', 'cooking_time', 'tags', 'ingredients', 'image'

    def validate(self, data):
        for field in ['image', 'ingredients', 'tags']:
            if not data.get(field):
                if field == 'image' and self.instance:
                    continue
                raise serializers.ValidationError({field: REQUIRED_FIELD})
        if not data.get('image', True):
            raise serializers.ValidationError({'image': NOT_EMPTY_FIELD})
        return data

    def _validate_unique(self, items):
        duplicates = [item for item in items if items.count(item) > 1]
        if duplicates:
            raise serializers.ValidationError(
                ITEMS_NOT_REPEAT.format(duplicates)
            )

    def validate_ingredients(self, recipe_ingredient_data):
        self._validate_unique([
            ingredient_data['ingredient'] for ingredient_data
            in recipe_ingredient_data
        ])
        return recipe_ingredient_data

    def validate_tags(self, tags):
        self._validate_unique(tags)
        return tags

    @transaction.atomic
    def _get_new_recipe(
        self, recipe, recipe_ingredient_data, tag_data
    ):
        recipe.tags.set(tag_data)
        RecipeIngredients.objects.bulk_create(
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ) for ingredient_data in recipe_ingredient_data)
        return recipe

    def create(self, recipe_data):
        recipe_ingredient_data = recipe_data.pop('ingredients')
        tag_data = recipe_data.pop('tags')
        return self._get_new_recipe(
            recipe=super().create(recipe_data),
            recipe_ingredient_data=recipe_ingredient_data,
            tag_data=tag_data
        )

    def update(self, old_recipe, new_recipe_data):
        recipe_ingredient_data = new_recipe_data.pop('ingredients')
        tag_data = new_recipe_data.pop('tags')
        old_recipe.ingredients.clear()
        self._get_new_recipe(
            recipe=old_recipe,
            recipe_ingredient_data=recipe_ingredient_data,
            tag_data=tag_data,
        )
        return super().update(old_recipe, new_recipe_data)

    def to_representation(self, recipe):
        return ReadRecipeSerializer(recipe, context=self.context).data


class RecipeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'
        read_only_fields = fields


class SubscribedUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')
        read_only_fields = fields

    def _get_recipes_limit(self):
        return 

    def get_recipes(self, author):
        return RecipeListSerializer(author.recipes.all()[
            :int(self.context.get('request').GET.get('recipes_limit', 10**10))
        ], many=True, read_only=True).data

    def get_recipes_count(self, author):
        return author.recipes.count()
