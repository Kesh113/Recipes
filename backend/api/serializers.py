import base64
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer, UserSerializer as DjoserUserSerializer
from django.core.validators import MinValueValidator

from foodgram.models import Ingredient, Recipe, RecipeIngredients, Tag, Favorites, Tokens
from users.models import Follow


User = get_user_model()


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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['is_subscribed'] = False
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            me_user = self.context['request'].user
            if Follow.objects.filter(user=me_user, following=instance).exists():
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
        ingredients = []
        for item in instance.recipe_ingredients.all():
            ingredient_data = IngredientSerializer(item.ingredient).data
            ingredient_data['amount'] = item.amount
            ingredients.append(ingredient_data)
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


class SubscribeSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def _get_serialized_recipes(self, user):
        recipes = user.recipes.all()
        request = self.context.get('request')
        if request and request.query_params.get('recipes_limit'):
            recipes = recipes[:int(request.query_params.get('recipes_limit'))]
        serialized_recipes = RecipeSerializer(recipes, many=True).data
        [recipe.pop(field) for recipe in serialized_recipes for field in ['tags', 'author', 'ingredients', 'text']]
        return serialized_recipes

    def to_representation(self, instance):
        data = UserSerializer(instance).data
        serialized_recipes = self._get_serialized_recipes(instance)
        data.update({'recipes': serialized_recipes, 'recipes_count': len(serialized_recipes)})
        return data


class CreateSubscribeSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate(self, data):
        request = self.context.get('request')
        following_id = data.get('id')
        if request:
            if request.user.id == following_id:
                raise serializers.ValidationError({'subscribe': 'Нельзя подписаться на самого себя.'})
            if Follow.objects.filter(user=request.user, following__id=following_id).exists():
                raise serializers.ValidationError({'subscribe': 'Вы уже подписаны'})
        return data

    def save(self):
        following_id = self.validated_data.get('id')
        following = get_object_or_404(User, id=following_id)
        Follow.objects.create(user=self.context['request'].user, following=following)
        return following

    def _get_serialized_recipes(self, user):
        recipes = user.recipes.all()
        request = self.context.get('request')
        if request and request.query_params.get('recipes_limit'):
            recipes = recipes[:int(request.query_params.get('recipes_limit'))]
        serialized_recipes = RecipeSerializer(recipes, many=True, context=self.context).data
        [recipe.pop(field)for recipe in serialized_recipes for field in ['tags', 'author', 'ingredients', 'text']]
        return serialized_recipes

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = User.objects.get(id=data['id'])
        data.update(UserSerializer(user).data)
        serialized_recipes = self._get_serialized_recipes(user)
        data.update({'recipes': serialized_recipes, 'recipes_count': len(serialized_recipes)})
        return data


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tokens
        fields = '__all__'
        extra_kwargs = {'full_url': {'validators': []}}

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return {'short-link': representation['short_link']}

    def create(self, validated_data):
        full_url = validated_data['full_url']
        token, _ = Tokens.objects.get_or_create(full_url=full_url)
        return token
