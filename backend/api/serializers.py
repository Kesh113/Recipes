import base64
from decimal import Decimal
import pprint

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer, UserSerializer as DjoserUserSerializer
from django.core.validators import MinValueValidator

from .utils import pop_fields
from foodgram.models import Favorite, Ingredient, Recipe, RecipeIngredients, ShoppingCart, Tag, Tokens
from users.models import Subscribe


User = get_user_model()

EXCLUDE_RECIPE_FIELDS = [
    'tags', 'author', 'ingredients',
    'text', 'is_favorited', 'is_in_shopping_cart'
]

SELF_SUBSCRIBE_ERROR = {'subscribe': 'Нельзя подписаться на самого себя.'}

ALREADY_SUBSCRIBED_ERROR = {'subscribe': 'Вы уже подписаны'}


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
            if Subscribe.objects.filter(user=me_user, subscribing=instance).exists():
                data['is_subscribed'] = True
        return data


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class ReadRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        exclude = 'pub_date',

    def to_representation(self, instance):
        recipe_data = super().to_representation(instance)
        recipe_data.pop('favorites_count')
        recipe_data['is_favorited'] = False
        recipe_data['is_in_shopping_cart'] = False
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            me_user = self.context['request'].user
            if Favorite.objects.filter(user=me_user, recipe=instance).exists():
                recipe_data['is_favorited'] = True
            if ShoppingCart.objects.filter(user=me_user, recipe=instance).exists():
                recipe_data['is_in_shopping_cart'] = True
        return recipe_data

    def get_ingredients(self, recipe):
        ingredients = []
        for item in recipe.recipe_ingredients.all():
            ingredient_data = IngredientSerializer(item.ingredient).data
            ingredient_data['amount'] = item.amount
            ingredients.append(ingredient_data)
        return ingredients


class IngredientWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])


class TagWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class WriteRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    image = Base64ImageField(required=True)
    ingredients = serializers.ListField(child=IngredientWriteSerializer(), write_only=True)

    class Meta:
        model = Recipe
        exclude = 'pub_date',

    def to_representation(self, instance):
        recipe_data = super().to_representation(instance)
        recipe_data.pop('favorites_count')
        recipe_data['is_favorited'] = False
        recipe_data['is_in_shopping_cart'] = False
        ingredients = []
        for item in instance.recipe_ingredients.all():
            ingredient_data = IngredientSerializer(item.ingredient).data
            ingredient_data['amount'] = item.amount
            ingredients.append(ingredient_data)
        me_user = self.context['request'].user
        if Favorite.objects.filter(user=me_user, recipe=instance).exists():
            recipe_data['is_favorited'] = True
        if ShoppingCart.objects.filter(user=me_user, recipe=instance).exists():
            recipe_data['is_in_shopping_cart'] = True
        recipe_data['ingredients'] = ingredients
        recipe_data['tags'] = TagSerializer(instance.tags.all(), many=True).data
        return recipe_data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Поле обязательно для заполнения')
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться.')
        for item in value:
            if not Ingredient.objects.filter(id=item['id']).exists():
                raise serializers.ValidationError(f'Ингредиента с id={item["id"]} не существует.')
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Поле tags обязательно.')
        tag_ids = [item for item in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Тэги не должны повторяться.')
        for item in value:
            if not Tag.objects.filter(id=item).exists():
                raise serializers.ValidationError(f'Тэга с id={item} не существует.')
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe(**validated_data)
        try:
            recipe.full_clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        recipe.save()
        for ingredient_data in ingredients:
            ingredient = Ingredient.objects.get(pk=ingredient_data['id'])
            amount = ingredient_data['amount']
            RecipeIngredients.objects.create(recipe=recipe, ingredient=ingredient, amount=amount)
        tags = Tag.objects.filter(pk__in=tags_data)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        try:
            super().update(instance, validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients:
                ingredient = Ingredient.objects.get(pk=ingredient_data['id'])
                amount = ingredient_data['amount']
                RecipeIngredients.objects.create(recipe=instance, ingredient=ingredient, amount=amount)
        if tags_data is not None:
            tags = Tag.objects.filter(pk__in=tags_data)
            instance.tags.set(tags)
        return instance


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ['subscribing',]

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
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if request and recipes_limit:
            subscribing_recipes = subscribing_recipes[:int(recipes_limit)]
        serialized_recipes = ReadRecipeSerializer(
            subscribing_recipes, many=True
        ).data
        pop_fields(serialized_recipes, EXCLUDE_RECIPE_FIELDS)
        return serialized_recipes

    def to_representation(self, subscribing):
        data = UserSerializer(subscribing).data
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


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        fields = 'recipe',

    def to_representation(self, instance):
        pprint.pprint(instance)
        recipe_data = ReadRecipeSerializer(
            instance.recipe, context=self.context
        ).data
        pop_fields([recipe_data], EXCLUDE_RECIPE_FIELDS)
        return recipe_data
