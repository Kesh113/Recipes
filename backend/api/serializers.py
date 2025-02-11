import base64
from decimal import Decimal
import pprint

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer
)
from rest_framework import serializers

from .utils import pop_fields
from foodgram.models import (
    Favorite, Ingredient, Recipe, RecipeIngredients, Tag, Tokens
)
from users.models import Subscribe


User = get_user_model()

REQUIRED_FIELD = 'Обязательное поле.'

IMAGE_REQUIRED_FIELD = {'image': 'Обязательное поле'}

INGREDIENTS_NOT_REPEAT = 'Ингредиенты не должны повторяться.'

NOT_EXIST_INGREDIENT = 'Ингредиента с id={} не существует.'

TAGS_NOT_REPEAT = 'Тэги не должны повторяться.'

EXCLUDE_RECIPE_FIELDS = [
    'tags', 'author', 'ingredients',
    'text', 'is_favorited', 'is_in_shopping_cart'
]

SELF_SUBSCRIBE_ERROR = {'subscribe': 'Нельзя подписаться на самого себя.'}

ALREADY_SUBSCRIBED_ERROR = {'subscribe': 'Вы уже подписаны'}

ALREADY_IN_FAVORITE = {'favorite': 'Рецепт уже добавлен в избранное'}

ALREADY_IN_SHOPPING_CART = {
    'shopping_cart': 'Рецепт уже добавлен в список покупок'
}


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['is_subscribed'] = False
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            me_user = self.context['request'].user
            if Subscribe.objects.filter(
                user=me_user, subscribing=instance
            ).exists():
                data['is_subscribed'] = True
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            data = ContentFile(
                base64.b64decode(imgstr),
                name='image.' + format.split('/')[-1]
            )
        return super().to_internal_value(data)


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = 'name', 'text', 'cooking_time', 'author', 'tags'


class ReadRecipeSerializer(RecipeSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + (
            'id', 'tags', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'image'
        )

    def get_ingredients(self, recipe):
        ingredients = []
        for item in recipe.recipe_ingredients.all():
            ingredient_data = IngredientSerializer(item.ingredient).data
            ingredient_data['amount'] = item.amount
            ingredients.append(ingredient_data)
        return ingredients

    def _get_is_related(self, recipe, related_name):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (getattr(recipe, related_name)
                    .filter(user=request.user)
                    .exists())
        return False

    def get_is_favorited(self, recipe):
        return self._get_is_related(recipe, 'favorites')

    def get_is_in_shopping_cart(self, recipe):
        return self._get_is_related(recipe, 'shopping_carts')


class RecipeIngredientsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )


class WriteRecipeSerializer(RecipeSerializer):
    ingredients = RecipeIngredientsSerializer(many=True, required=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ('ingredients', 'image')

    def validate(self, data):
        if self.instance is None and not data.get('image'):
            raise serializers.ValidationError(IMAGE_REQUIRED_FIELD)
        return data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(REQUIRED_FIELD)
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(INGREDIENTS_NOT_REPEAT)
        for id in ingredient_ids:
            if not Ingredient.objects.filter(id=id).exists():
                raise serializers.ValidationError(
                    NOT_EXIST_INGREDIENT.format(id)
                )
        return value

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(TAGS_NOT_REPEAT)
        return tags

    @transaction.atomic
    def create(self, recipe_data):
        ingredients_data = recipe_data.pop('ingredients')
        tags_data = recipe_data.pop('tags')
        recipe = Recipe.objects.create(**recipe_data)
        RecipeIngredients.objects.bulk_create([
            RecipeIngredients(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients_data])
        recipe.tags.set(tags_data)
        return recipe

    @transaction.atomic
    def update(self, old_recipe, new_recipe_data):
        old_recipe.ingredients.clear()
        RecipeIngredients.objects.bulk_create([
            RecipeIngredients(
                recipe=old_recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            ) for ingredient_data in new_recipe_data.pop('ingredients')])
        old_recipe.tags.set(new_recipe_data.pop('tags'))
        for key, value in new_recipe_data.items():
            setattr(old_recipe, key, value)
        old_recipe.save()
        return old_recipe

    def to_representation(self, recipe):
        return ReadRecipeSerializer(recipe, context=self.context).data


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = 'subscribing',

    def validate(self, data):
        request = self.context.get('request')
        subscribing = data.get('subscribing')
        if request:
            if request.user == subscribing:
                raise serializers.ValidationError(SELF_SUBSCRIBE_ERROR)
            if Subscribe.objects.filter(
                user=request.user, subscribing=subscribing
            ).exists():
                raise serializers.ValidationError(ALREADY_SUBSCRIBED_ERROR)
        return subscribing

    def save(self, user):
        return Subscribe.objects.create(
            user=user, subscribing=self.validated_data
        )

    def _get_serialized_recipes(self, subscribing):
        subscribing_recipes = subscribing.recipes.all()
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        if request and recipes_limit:
            subscribing_recipes = subscribing_recipes[:int(recipes_limit)]
        serialized_recipes = ReadRecipeSerializer(
            subscribing_recipes, many=True
        ).data
        pop_fields(serialized_recipes, EXCLUDE_RECIPE_FIELDS)
        return serialized_recipes

    def to_representation(self, subscribing):
        data = UserSerializer(
            subscribing, context={'request': self.context['request']}
        ).data
        serialized_recipes = self._get_serialized_recipes(subscribing)
        data.update({
            'recipes': serialized_recipes,
            'recipes_count': len(serialized_recipes)
        })
        return data


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tokens
        fields = '__all__'
        extra_kwargs = {'full_url': {'validators': []}}

    def to_representation(self, instance):
        return {'short-link': instance.short_link}

    def create(self, validated_data):
        token, _ = Tokens.objects.get_or_create(
            full_url=validated_data['full_url']
        )
        return token


class UserRecipeListsSerializer(serializers.Serializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    def save(self, user, model):
        favorite_recipe, created = model.objects.get_or_create(
            user=user, recipe=self.validated_data['recipe']
        )
        if not created:
            if model == Favorite:
                raise serializers.ValidationError(
                    ALREADY_IN_FAVORITE,
                )
            raise serializers.ValidationError(
                ALREADY_IN_SHOPPING_CART,
            )
        return favorite_recipe

    def to_representation(self, instance):
        recipe_data = ReadRecipeSerializer(
            instance['recipe'], context=self.context
        ).data
        pop_fields([recipe_data], EXCLUDE_RECIPE_FIELDS)
        return recipe_data
