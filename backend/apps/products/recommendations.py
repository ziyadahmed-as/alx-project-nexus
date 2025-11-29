"""
Product Recommendation Engine
Provides personalized product recommendations based on:
- User browsing history
- Product views
- Category similarity
- Price range similarity
- Vendor products
"""

from django.db.models import Count, Q
from .models import Product, Category
from apps.orders.models import Order, OrderItem


class ProductRecommendations:
    """Generate product recommendations"""
    
    @staticmethod
    def get_similar_products(product, limit=8):
        """Get products similar to the given product"""
        similar_products = Product.objects.filter(
            Q(category=product.category) |  # Same category
            Q(vendor=product.vendor),  # Same vendor
            is_active=True,
            status='published'
        ).exclude(
            id=product.id  # Exclude the current product
        ).order_by('-featured', '-created_at')[:limit]
        
        return similar_products
    
    @staticmethod
    def get_recommendations_by_category(category_id, limit=8):
        """Get popular products from a specific category"""
        return Product.objects.filter(
            category_id=category_id,
            is_active=True,
            status='published'
        ).order_by('-sales_count', '-views', '-created_at')[:limit]
    
    @staticmethod
    def get_trending_products(limit=8):
        """Get trending products based on recent views and sales"""
        return Product.objects.filter(
            is_active=True,
            status='published'
        ).order_by('-views', '-sales_count', '-created_at')[:limit]
    
    @staticmethod
    def get_recommendations_by_price_range(product, limit=8):
        """Get products in similar price range"""
        price = float(product.price)
        min_price = price * 0.7  # 30% lower
        max_price = price * 1.3  # 30% higher
        
        return Product.objects.filter(
            price__gte=min_price,
            price__lte=max_price,
            is_active=True,
            status='published'
        ).exclude(
            id=product.id
        ).order_by('-featured', '-sales_count')[:limit]
    
    @staticmethod
    def get_frequently_bought_together(product, limit=4):
        """Get products frequently bought with this product"""
        # Get orders containing this product
        order_items = OrderItem.objects.filter(product=product)
        order_ids = order_items.values_list('order_id', flat=True)
        
        # Get other products from those orders
        related_products = OrderItem.objects.filter(
            order_id__in=order_ids
        ).exclude(
            product=product
        ).values('product').annotate(
            count=Count('product')
        ).order_by('-count')[:limit]
        
        product_ids = [item['product'] for item in related_products]
        
        return Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            status='published'
        )
    
    @staticmethod
    def get_personalized_recommendations(user, limit=12):
        """Get personalized recommendations based on user history"""
        if not user or not user.is_authenticated:
            # Return trending products for anonymous users
            return ProductRecommendations.get_trending_products(limit)
        
        # Get user's order history
        user_orders = Order.objects.filter(buyer=user)
        ordered_products = OrderItem.objects.filter(
            order__in=user_orders
        ).values_list('product__category', flat=True).distinct()
        
        # Get products from categories user has purchased from
        if ordered_products:
            recommendations = Product.objects.filter(
                category__in=ordered_products,
                is_active=True,
                status='published'
            ).order_by('-featured', '-sales_count', '-created_at')[:limit]
        else:
            # Fallback to trending products
            recommendations = ProductRecommendations.get_trending_products(limit)
        
        return recommendations
    
    @staticmethod
    def get_new_arrivals_in_category(category_id, limit=8):
        """Get newest products in a category"""
        return Product.objects.filter(
            category_id=category_id,
            is_active=True,
            status='published'
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_best_sellers(limit=8):
        """Get best selling products"""
        return Product.objects.filter(
            is_active=True,
            status='published'
        ).order_by('-sales_count', '-views')[:limit]
    
    @staticmethod
    def get_you_may_also_like(product, user=None, limit=8):
        """
        Comprehensive recommendation combining multiple strategies
        """
        recommendations = []
        
        # 1. Similar products (same category/vendor)
        similar = list(ProductRecommendations.get_similar_products(product, limit=4))
        recommendations.extend(similar)
        
        # 2. Products in similar price range
        if len(recommendations) < limit:
            price_similar = list(ProductRecommendations.get_recommendations_by_price_range(
                product, 
                limit=limit - len(recommendations)
            ))
            # Avoid duplicates
            for p in price_similar:
                if p not in recommendations:
                    recommendations.append(p)
        
        # 3. Trending products if still need more
        if len(recommendations) < limit:
            trending = list(ProductRecommendations.get_trending_products(
                limit=limit - len(recommendations)
            ))
            for p in trending:
                if p not in recommendations:
                    recommendations.append(p)
        
        return recommendations[:limit]
